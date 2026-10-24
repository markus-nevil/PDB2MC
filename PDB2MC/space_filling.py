"""
Space Filling mode: a smooth molecular surface around the protein / nucleic acid, coloured by the nearest
atom (or by chain), with the backbone and sidechains as a darker skeleton inside and HETATMs as spheres.

Every part is computed on one grid in the model's block coordinates, so the surface, skeleton and
HETATMs always line up. (The previous version computed the surface in its own array and moved it back
by matching centroids, which left the parts misaligned.) Only the outer layer of the surface is placed:
blocks enclosed on all six sides can never be seen, and cavities inside the protein are filled.
"""
import math

import numpy as np
import pandas as pd
from scipy import ndimage
from scipy.spatial import cKDTree

from PDB2MC import pdb_manipulation as pdbm
from PDB2MC.build import EMPTY_BLOCKS, ModelBuilder, backbone_lines, bond_lines, sidechain_blocks

# Surface shape, in Angstrom (multiplied by the protein scale): an isolated atom becomes a ball of
# SURFACE_RADIUS; SURFACE_SMOOTHING blends neighbouring atoms into one smooth surface
SURFACE_RADIUS = 1.6
SURFACE_SMOOTHING = 0.8
# Share of surface blocks kept for "mesh-style" models
MESH_KEEP = 0.10
MESH_SEED = 0


def surface_shell(points, scale, return_solid=False):
    """
    Outer layer of a smooth surface around integer `points` ((n, 3) array), as an (m, 3) int array.

    The points are blurred with a Gaussian into a density; voxels above the density an isolated point
    has at SURFACE_RADIUS are inside. Enclosed cavities are filled and only voxels with an empty face
    neighbour are returned.
    """
    radius = SURFACE_RADIUS * scale
    sigma = max(SURFACE_SMOOTHING * scale, 0.5)
    pad = int(math.ceil(radius + 3 * sigma)) + 1
    origin = points.min(axis=0) - pad
    shape = points.max(axis=0) - origin + pad + 1
    grid = np.zeros(shape, dtype=np.float32)
    np.add.at(grid, tuple((points - origin).T), 1.0)
    density = ndimage.gaussian_filter(grid, sigma=sigma, mode='constant')
    threshold = math.exp(-radius ** 2 / (2 * sigma ** 2)) / (2 * math.pi * sigma ** 2) ** 1.5
    solid = ndimage.binary_fill_holes(density >= threshold)
    shell = solid & ~ndimage.binary_erosion(solid)
    coords = np.argwhere(shell) + origin
    if return_solid:
        return coords, (solid, origin)
    return coords


def colour_by_nearest(coords, atoms, labels):
    """Label of the nearest atom for every coordinate."""
    _, nearest = cKDTree(atoms[['X', 'Y', 'Z']].to_numpy(dtype=float)).query(coords)
    return np.asarray(labels, dtype=object)[nearest]


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
    builder.report(5)

    parts = []
    if not polymer.empty:
        coords = surface_shell(polymer[['X', 'Y', 'Z']].to_numpy(dtype=int), scale)
        if by_chain:
            labels = polymer['chain'].map(lambda c: str(builder.numbers.get(c, 1)))
        else:
            labels = pdbm.element_atom_names(polymer)['atom']
        surface = pd.DataFrame(coords, columns=['X', 'Y', 'Z'])
        surface['atom'] = colour_by_nearest(coords, polymer, labels)
        if config.get('mesh'):
            surface = mesh_sample(surface)
        parts.append((surface, "surface", polymer))
        builder.report(50)

        # Inner skeleton in the darker chain colours ('3b')
        branch_config = {**config, "by_chain": True}
        skeleton = pd.concat([backbone_lines(polymer, True, builder.numbers),
                              sidechain_blocks(polymer, branch_config, builder.numbers)], ignore_index=True)
        if not skeleton.empty:
            skeleton['atom'] = skeleton['atom'].astype(str) + 'b'
            parts.append((skeleton, "branch", polymer))
    builder.report(65)

    if config["show_hetatm"] and not het.empty:
        radius = max(round(scale - 1), 0)
        spheres = pdbm.add_sphere_coordinates(pdbm.rasterized_sphere(radius), pdbm.sphere_center(radius),
                                              pdbm.element_atom_names(het.reset_index(drop=True)),
                                              mesh=config.get('mesh', False))
        parts.append((spheres, "hetatm", het))
        bonds = bond_lines(df, builder.structure.bonds, het['atom_num'])
        if not bonds.empty:
            bonds['block'] = 'gray_concrete'
            parts.append((bonds, "hetatm_bonds", df))
    builder.report(75)

    # The surface reaches below the lowest atom; lift every part by the same amount so the model
    # starts at the placement height and the parts stay aligned
    lowest = min((blocks['Y'].min() for blocks, _, _ in parts if not blocks.empty), default=0)
    for blocks, suffix, atoms in parts:
        builder.write(blocks.assign(Y=blocks['Y'] - lowest), suffix, atoms=atoms.assign(Y=atoms['Y'] - lowest))
    builder.report(100)


def run_mode(config_data, pdb_name, structure, mc_dir, progress=None):
    build(ModelBuilder(config_data, structure, mc_dir, name=pdb_name, progress=progress))
