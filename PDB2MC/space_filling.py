"""
Space Filling mode: the solvent accessible surface (SAS) of the protein / nucleic acid, coloured by atom
element (or by chain), with the backbone and sidechains as a darker skeleton inside and HETATMs as spheres.

The SAS is the surface traced by the centre of a probe ball (a water molecule, radius SASA_radius) rolled
over the atoms. It is found with the Shrake-Rupley algorithm: test points are spread over a sphere of
radius (van der Waals radius + SASA_radius) around every atom, and a point is on the surface when it is
not inside any other atom's sphere: a probe centred there touches its atom without overlapping any other.
The accessible points are placed as blocks; surfaces of cavities closed off inside the molecule are left
out, since they can never be seen.

Every part uses the model's own block coordinates, so the surface, skeleton and HETATMs line up.
"""
import math

import numpy as np
import pandas as pd
from scipy import ndimage
from scipy.spatial import cKDTree

from PDB2MC import pdb_manipulation as pdbm
from PDB2MC.build import RESIDUE_COLUMN, ModelBuilder, backbone_lines, bond_lines, sidechain_blocks

# Radius of the probe ball rolled over the atoms, in Angstrom (1.4 = a water molecule)
SASA_radius = 1.4
# Van der Waals radii in Angstrom (Bondi 1964; metals from Alvarez 2013)
VDW_RADII = {'H': 1.20, 'C': 1.70, 'N': 1.55, 'O': 1.52, 'S': 1.80, 'P': 1.80, 'SE': 1.90, 'F': 1.47,
             'CL': 1.75, 'BR': 1.85, 'I': 1.98, 'MG': 1.73, 'NA': 2.27, 'K': 2.75, 'CA': 2.31,
             'FE': 2.04, 'ZN': 2.01, 'CU': 1.96, 'MN': 2.05}
DEFAULT_VDW_RADIUS = 1.80
# Shrake-Rupley test points per square block of sphere surface; enough that the placed blocks
# have no holes
POINT_DENSITY = 4.0
MIN_POINTS = 60
# Test points handled at once (memory: ~50 bytes each); progress is reported after each batch
CHUNK_POINTS = 250_000
MIN_BATCHES = 25
# Share of surface blocks kept for "mesh-style" models
MESH_KEEP = 0.10
MESH_SEED = 0
# Share of the build's progress for each step; finding the surface takes far longer than anything else
WORK = {"surface": 91, "skeleton": 1, "hetatm": 1, "write": 7}

_FACES = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]


def vdw_radii(elements):
    return np.array([VDW_RADII.get(str(e).strip().upper(), DEFAULT_VDW_RADIUS) for e in elements])


def sphere_points(n):
    """n roughly evenly spaced unit vectors (golden spiral)."""
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    theta = math.pi * (1 + 5 ** 0.5) * i
    return np.column_stack([np.cos(theta) * np.sin(phi), np.sin(theta) * np.sin(phi), np.cos(phi)])


def accessible_points(centres, radii, progress=None):
    """
    Shrake-Rupley: test points on a sphere of radius radii[i] around each centre, kept when they are
    not inside any other sphere. Returns (points (m, 3), index of the sphere each point is on).
    progress, if given, gets the fraction done (0-1).
    """
    centres = np.asarray(centres, dtype=float)
    radii = np.asarray(radii, dtype=float)
    if not len(centres):
        return np.zeros((0, 3)), np.zeros(0, dtype=int)
    counts = np.maximum(MIN_POINTS, np.ceil(4 * math.pi * radii ** 2 * POINT_DENSITY)).astype(int)
    # Atoms share a few radii (one per element), so the "inside another sphere" test is one fixed-radius
    # neighbour count per radius. A point lies on its own sphere; the small margin keeps that sphere
    # from counting, and a point exactly on another sphere's edge counts as accessible.
    # The most common radius (carbon) first: it covers most points, so later queries have fewer to test
    values, sizes = np.unique(radii, return_counts=True)
    trees = [(r, cKDTree(centres[radii == r])) for r in values[np.argsort(-sizes)]]
    points, owners = [], []
    batches = min(len(centres), max(MIN_BATCHES, int(counts.sum() // CHUNK_POINTS)))
    chunks = np.array_split(np.arange(len(centres)), batches)
    for number, chunk in enumerate(chunks, start=1):
        test, owner = [], []
        for n in np.unique(counts[chunk]):
            atoms = chunk[counts[chunk] == n]
            test.append((centres[atoms, None, :] + radii[atoms, None, None] * sphere_points(n)).reshape(-1, 3))
            owner.append(np.repeat(atoms, n))
        test, owner = np.concatenate(test), np.concatenate(owner)
        covered = np.zeros(len(test), dtype=bool)
        for r, tree in trees:
            open_points = ~covered
            distance, _ = tree.query(test[open_points], k=1, distance_upper_bound=r * (1 - 1e-9) - 1e-9, workers=-1)
            covered[open_points] = np.isfinite(distance)
        points.append(test[~covered])
        owners.append(owner[~covered])
        if progress is not None:
            progress(number / len(chunks))
    return np.concatenate(points), np.concatenate(owners)


def outer_voxels(coords):
    """The voxels of `coords` that touch the space outside the molecule (drops closed-off cavities)."""
    origin = coords.min(axis=0) - 1
    shape = coords.max(axis=0) - origin + 2
    filled = np.zeros(shape, dtype=bool)
    filled[tuple((coords - origin).T)] = True
    empty_parts, _ = ndimage.label(~filled)
    outside = empty_parts == empty_parts[0, 0, 0]
    padded = np.pad(outside, 1)
    local = coords - origin + 1
    touches = np.zeros(len(coords), dtype=bool)
    for dx, dy, dz in _FACES:
        touches |= padded[local[:, 0] + dx, local[:, 1] + dy, local[:, 2] + dz]
    return touches


def sas_surface(atoms, scale, probe_radius=SASA_radius, progress=None):
    """
    Solvent accessible surface blocks of `atoms` (with unrounded Xf/Yf/Zf block coordinates and
    'element'), for a probe ball of probe_radius Angstrom. Returns (coords (m, 3) int, index into atoms
    of the atom each block belongs to). progress, if given, gets the fraction done (0-1).
    """
    report = progress or (lambda fraction: None)
    centres = atoms[['Xf', 'Yf', 'Zf']].to_numpy(dtype=float)
    radii = (vdw_radii(atoms['element']) + probe_radius) * scale
    points, owners = accessible_points(centres, radii, progress=lambda fraction: report(0.92 * fraction))
    if not len(points):
        return np.zeros((0, 3), dtype=int), np.zeros(0, dtype=int)
    voxels = np.rint(points).astype(int)
    # One number per voxel, in x, y, z order: the same result as np.unique(axis=0), several times faster
    low = voxels.min(axis=0)
    span = voxels.max(axis=0) - low + 1
    keys = ((voxels[:, 0] - low[0]) * span[1] + voxels[:, 1] - low[1]) * span[2] + voxels[:, 2] - low[2]
    _, first = np.unique(keys, return_index=True)
    coords = voxels[first]
    owners = owners[first]
    report(0.95)
    keep = outer_voxels(coords)
    return coords[keep], owners[keep]


def mesh_sample(blocks):
    """Keep MESH_KEEP of the blocks, the same ones every time."""
    if blocks.empty:
        return blocks
    keep = np.random.default_rng(MESH_SEED).random(len(blocks)) < MESH_KEEP
    return blocks[keep]


def build(builder):
    """Write <name>_surface, _branch (inner skeleton), _hetatm and _hetatm_bonds."""
    config = builder.config
    scale = config['scale']
    df = builder.df
    hidden = builder.mods.hidden
    if hidden:
        # Hidden residues are left out before the surface is made, so it closes around the rest
        keys = df['chain'].astype(str) + ":" + df['resid'].astype(int).astype(str)
        df = df[~keys.isin(hidden)]
    polymer = df[df['polymer']]
    het = df[(df['row'] == 'HETATM') & ~df['polymer']]
    by_chain = config["by_chain"]
    builder.plan(WORK)

    parts = []
    within = builder.step("surface", "Finding the surface of the molecule...", writes=False)
    if not polymer.empty:
        polymer = polymer.reset_index(drop=True)
        coords, owner = sas_surface(polymer, scale, config.get('sasa_radius', SASA_radius), progress=within)
        if by_chain:
            labels = polymer['chain'].map(lambda c: str(builder.numbers.get(c, 1))).to_numpy(dtype=object)
        else:
            labels = pdbm.element_atom_names(polymer)['atom'].to_numpy(dtype=object)
        residues = (polymer['chain'].astype(str) + ":" + polymer['resid'].astype(int).astype(str)).to_numpy()
        surface = pd.DataFrame(coords, columns=['X', 'Y', 'Z'])
        surface['atom'] = labels[owner]
        surface[RESIDUE_COLUMN] = residues[owner]
        if config.get('mesh'):
            surface = mesh_sample(surface)
        parts.append((surface, "surface", polymer))

        # Inner skeleton in the darker chain colours ('3b')
        builder.step("skeleton", "Drawing the inner skeleton...", writes=False)
        branch_config = {**config, "by_chain": True}
        skeleton = pd.concat([backbone_lines(polymer, True, builder.numbers),
                              sidechain_blocks(polymer, branch_config, builder.numbers)], ignore_index=True)
        if not skeleton.empty:
            skeleton['atom'] = skeleton['atom'].astype(str) + 'b'
            parts.append((skeleton, "branch", polymer))

    if config["show_hetatm"] and not het.empty:
        builder.step("hetatm", "Placing the other molecules...", writes=False)
        radius = max(round(scale - 1), 0)
        spheres = pdbm.add_sphere_coordinates(pdbm.rasterized_sphere(radius), pdbm.sphere_center(radius),
                                              pdbm.element_atom_names(het.reset_index(drop=True)),
                                              mesh=config.get('mesh', False))
        parts.append((spheres, "hetatm", het))
        bonds = bond_lines(df, builder.structure.bonds, het['atom_num'])
        if not bonds.empty:
            bonds['block'] = 'gray_concrete'
            parts.append((bonds, "hetatm_bonds", df))

    # The surface reaches below the lowest atom; lift every part by the same amount so the model
    # starts at the placement height and the parts stay aligned
    lowest = min((blocks['Y'].min() for blocks, _, _ in parts if not blocks.empty), default=0)
    builder.step("write", writes=False)
    builder.plan({suffix: len(blocks) for blocks, suffix, _ in parts})
    for blocks, suffix, atoms in parts:
        builder.step(suffix, "Writing the model...", compute=0.05)
        builder.write(blocks.assign(Y=blocks['Y'] - lowest), suffix, atoms=atoms.assign(Y=atoms['Y'] - lowest))
    builder.report(100)


def run_mode(config_data, pdb_name, structure, mc_dir, progress=None):
    build(ModelBuilder(config_data, structure, mc_dir, name=pdb_name, progress=progress))
