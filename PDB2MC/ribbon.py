"""Ribbon mode: smoothed backbone with flat helix/sheet ribbons (or helix rods), nucleic acid ladders."""
import math

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from scipy.spatial import cKDTree
from types import SimpleNamespace

from PDB2MC import pdb_manipulation as pdbm, secondary_structure
from PDB2MC.build import ModelBuilder, hetatm_blocks, part_work

AMINO_ACIDS = ["ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE", "LEU", "LYS", "MET",
               "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL", "MSE"]
NUCLEOTIDES = ["A", "C", "G", "U", "DA", "DC", "DG", "DT", "DI"]
RIBOSE_ATOMS = ["C1'", "C2'", "C3'", "C4'", "O4'"]
BASE_ATOMS = ["N1", "C2", "N3", "C4", "C5", "C6", "N7", "C8", "N9"]
RIBBON_BACKBONE_ATOMS = ['C', 'N', 'CA', "C4'", "C3'"]
SMOOTHNESS = 5000
# Relative time per atom of a chain, for the progress bar: DNA and RNA ladders are far slower than ribbons
PROTEIN_WORK = 1
NUCLEIC_WORK = 7
# Relative time per expected block of other molecules
HETATM_WORK = 0.02


# --- protein cartoon ---
# How thick the flat helix and strand ribbons are, in angstrom: multiplied by the protein scale, and never less
# than one block. Suggested values:
#   0.25  thinnest: one block thick up to protein scale 4
#   0.33  thin (default): one block up to scale 3, two from scale 4.5
#   0.5   medium: one block up to scale 2, then about scale / 2
#   0.8   chunky: about one block per scale step above 1
ribbon_thickness = 0.25
# Other sizes, also in angstrom so they grow with the protein scale
HELIX_HALF_WIDTH = 1.0         # narrower than strands, so a helix shows as a spiral rather than a tube
STRAND_HALF_WIDTH = 1.4
ARROW_HALF_WIDTH = 2.2         # the widest part of a β-strand's arrow head
TUBE_RADIUS = 0.35             # loops
# "Alpha helices as rods": a straight rod from each helix's first alpha carbon to its last, this wide
ROD_DIAMETER = 2.0
ROD_SHELL = 1.3                # blocks: wide rods are hollow, with walls this thick
# Consecutive alpha carbons further apart than this (angstrom) are not joined: a gap in the chain
CA_GAP = 4.3
# Samples along the curve and across the ribbon are at most this many blocks apart, so the blocks join up
SAMPLE_STEP = 0.35


def _residue_frames(chain_df):
    """
    Per residue of a protein chain, in order: alpha carbon positions, C=O directions and secondary structure, from
    the unrounded coordinates (Xf, Yf, Zf).
    """
    xyz = ['Xf', 'Yf', 'Zf'] if 'Xf' in chain_df.columns else ['X', 'Y', 'Z']
    atoms = chain_df[chain_df['atom'].isin(['CA', 'C', 'O'])]
    wide = atoms.drop_duplicates(['resid', 'atom']).pivot_table(index='resid', columns='atom', values=xyz,
                                                                  aggfunc='first', sort=False)
    order = chain_df.drop_duplicates('resid')['resid']
    order = [resid for resid in order if resid in wide.index and not pd.isna(wide.loc[resid, (xyz[0], 'CA')])]
    wide = wide.loc[order]
    ca = np.stack([wide[(axis, 'CA')].to_numpy(dtype=float) for axis in xyz], axis=1)
    if {'C', 'O'} <= set(wide.columns.get_level_values(1)):
        carbonyl = np.stack([wide[(axis, 'O')].to_numpy(dtype=float) - wide[(axis, 'C')].to_numpy(dtype=float)
                             for axis in xyz], axis=1)
    else:
        carbonyl = np.full_like(ca, np.nan)
    kinds = chain_df.drop_duplicates('resid').set_index('resid')['structure'].reindex(order).fillna('None')
    return ca, carbonyl, kinds.to_numpy(dtype=object), np.asarray(order)


def _segments(ca, scale):
    """Index ranges of stretches of chain without a gap."""
    if len(ca) < 2:
        return [(0, len(ca))] if len(ca) else []
    breaks = np.nonzero(np.linalg.norm(np.diff(ca, axis=0), axis=1) > CA_GAP * scale)[0] + 1
    edges = [0, *breaks.tolist(), len(ca)]
    return [(a, b) for a, b in zip(edges[:-1], edges[1:]) if b > a]


def _curve(points, samples_per_residue):
    """A smooth curve through every point (one per residue), sampled evenly: (positions, residue parameter u)."""
    count = len(points)
    u = np.linspace(0, count - 1, max(2, (count - 1) * samples_per_residue + 1))
    if count == 1:
        return np.repeat(points, len(u), axis=0), u
    if count == 2:
        return points[0] + (points[1] - points[0]) * u[:, None], u
    spline = CubicSpline(np.arange(count), points, axis=0, bc_type='natural')
    return spline(u), u


def _side_vectors(carbonyl, tangents_at_residues):
    """
    The direction across the ribbon at each residue: its C=O, at right angles to the chain, flipped where needed so
    it never turns by more than 90 degrees from one residue to the next (in β-strands neighbouring C=O point
    opposite ways, which would twist the ribbon).
    """
    sides = np.array(carbonyl, dtype=float)
    for i in range(len(sides)):
        if not np.all(np.isfinite(sides[i])) or np.linalg.norm(sides[i]) < 1e-6:
            sides[i] = sides[i - 1] if i else np.cross(tangents_at_residues[i], [0.0, 1.0, 0.0])
    sides -= (sides * tangents_at_residues).sum(axis=1)[:, None] * tangents_at_residues
    sides /= np.maximum(np.linalg.norm(sides, axis=1), 1e-9)[:, None]
    for i in range(1, len(sides)):
        if np.dot(sides[i], sides[i - 1]) < 0:
            sides[i] = -sides[i]
    return sides


def _unit(vectors):
    return vectors / np.maximum(np.linalg.norm(vectors, axis=1), 1e-9)[:, None]


def _stamp(centres, radius):
    """Every block within `radius` of the centres (a round tube along a curve)."""
    offsets = np.argwhere(pdbm.rasterized_sphere(max(radius, 0.5)) > 0) - np.array(pdbm.sphere_center(max(radius, 0.5)))
    cells = np.unique(np.rint(centres).astype(int), axis=0)
    return (cells[:, None, :] + offsets[None, :, :]).reshape(-1, 3)


def _ribbon_profile(kinds, u, scale):
    """Half-width of the flat ribbon at each sample (0 where the chain is a loop), with β-strand arrow heads."""
    half = np.zeros(len(u))
    residue = np.clip(np.rint(u).astype(int), 0, len(kinds) - 1)
    half[kinds[residue] == 'helix'] = HELIX_HALF_WIDTH * scale
    half[kinds[residue] == 'sheet'] = STRAND_HALF_WIDTH * scale
    # Arrow head over the last residue of each strand: widest where it starts, a point at the strand's end
    count = len(kinds)
    for end in range(count):
        if kinds[end] == 'sheet' and (end + 1 == count or kinds[end + 1] != 'sheet'):
            start = end - 1 if end > 0 and kinds[end - 1] == 'sheet' else end - 0.5
            head = (u >= start) & (u <= end + 0.5)
            fraction = (u[head] - start) / max(end + 0.5 - start, 1e-9)
            half[head] = ARROW_HALF_WIDTH * scale * (1 - fraction)
    return half


def protein_cartoon(chain_df, scale, bar_helix=False, progress=None):
    """
    (ribbon blocks, loop blocks) for one protein chain, as integer (n, 3) arrays: flat ribbons for helices and
    β-strands (helices as rods with bar_helix) with arrow heads on the strands, and round tubes for the loops.
    progress, if given, gets the fraction done (0-1).
    """
    report = progress or (lambda fraction: None)
    ca, carbonyl, kinds, _ = _residue_frames(chain_df)
    ribbon, loops = [], []
    samples = max(2, int(math.ceil(CA_GAP * scale / SAMPLE_STEP)))
    segments = _segments(ca, scale)
    total = max(sum(end - start for start, end in segments), 1)
    done = 0
    for start, end in segments:
        # Each stretch of chain is a share of the work, in proportion to its residues
        share = (end - start) / total
        points, sides_in, part_kinds = ca[start:end], carbonyl[start:end], kinds[start:end]
        curve, u = _curve(points, samples)
        if len(points) >= 2:
            tangents = _unit(np.gradient(curve, axis=0))
            at_residues = tangents[np.clip(np.searchsorted(u, np.arange(len(points))), 0, len(u) - 1)]
        else:
            tangents = np.tile([1.0, 0.0, 0.0], (len(u), 1))
            at_residues = tangents[:1]
        sides = _side_vectors(sides_in, at_residues)
        # Across-ribbon direction along the curve: between residues, blended from their two directions
        low = np.clip(np.floor(u).astype(int), 0, len(points) - 1)
        high = np.clip(low + 1, 0, len(points) - 1)
        t = (u - low)[:, None]
        across = _unit((1 - t) * sides[low] + t * sides[high])
        across = _unit(across - (across * tangents).sum(axis=1)[:, None] * tangents)
        normal = _unit(np.cross(tangents, across))
        report(done + 0.3 * share)

        residue = np.clip(np.rint(u).astype(int), 0, len(points) - 1)
        half = _ribbon_profile(part_kinds, u, scale)
        if bar_helix:
            helix = part_kinds[residue] == 'helix'
            half[helix] = 0
            ribbon.extend(_rods(points, part_kinds, scale))
        flat = half > 0
        if flat.any():
            thickness = max(ribbon_thickness * scale, 1.0)
            widths = np.arange(-ARROW_HALF_WIDTH * scale, ARROW_HALF_WIDTH * scale + SAMPLE_STEP, SAMPLE_STEP)
            depths = np.arange(-thickness / 2 + 0.5, thickness / 2, SAMPLE_STEP) if thickness > 1 else np.array([0.0])
            centre, a, n, h = curve[flat], across[flat], normal[flat], half[flat]
            for k, w in enumerate(widths):
                inside = np.abs(w) <= h + 1e-9
                for d in depths:
                    ribbon.append(np.rint(centre[inside] + w * a[inside] + d * n[inside]).astype(int))
                report(done + (0.3 + 0.5 * (k + 1) / len(widths)) * share)
        report(done + 0.8 * share)
        loop = ~flat
        if bar_helix:
            # Loops run right up to each rod's end, the helix's first and last alpha carbon
            loop &= ~_inside_helices(part_kinds, u)
        if loop.any():
            loops.append(_stamp(curve[loop], max(TUBE_RADIUS * scale, 0.5)))
        done += share
        report(done)
    as_array = lambda parts: np.unique(np.concatenate(parts), axis=0) if parts else np.zeros((0, 3), dtype=int)
    return as_array(ribbon), as_array(loops)


def _helix_runs(kinds):
    """(first, last) residue index of each helix."""
    runs, start = [], None
    for i in range(len(kinds) + 1):
        inside = i < len(kinds) and kinds[i] == 'helix'
        if inside and start is None:
            start = i
        elif not inside and start is not None:
            runs.append((start, i - 1))
            start = None
    return runs


def _inside_helices(kinds, u):
    """Samples strictly between a helix's first and last alpha carbon."""
    inside = np.zeros(len(u), dtype=bool)
    for first, last in _helix_runs(kinds):
        inside |= (u > first) & (u < last)
    return inside


def _rods(points, kinds, scale):
    """A straight rod from each helix's first alpha carbon to its last."""
    rods = []
    radius = max(ROD_DIAMETER * scale / 2, 0.5)
    for first, last in _helix_runs(kinds):
        start, end = points[first], points[last]
        steps = max(2, int(np.linalg.norm(end - start) / SAMPLE_STEP) + 1)
        line = start + (end - start) * np.linspace(0, 1, steps)[:, None]
        rods.append(_hollow(_stamp(line, radius), line, radius))
    return rods


def _hollow(cells, axis, radius):
    """Only the outer ROD_SHELL blocks of a solid rod: it looks the same and takes far fewer blocks."""
    if radius <= ROD_SHELL + 0.5:
        return cells
    cells = np.unique(cells, axis=0)
    distance, _ = cKDTree(axis).query(cells)
    return cells[distance >= radius - ROD_SHELL]


def chain_backbone(chain_df):
    return chain_df[chain_df['atom'].isin(RIBBON_BACKBONE_ATOMS)]


def nucleic_backbone(chain_df, dna_vectors, progress=None):
    trace = pdbm.find_intermediate_points(chain_backbone(chain_df), keep_columns=True)
    trace = pdbm.interpolate_dataframe(trace, SMOOTHNESS)
    return pdbm.flank_DNA(trace, dna_vectors, progress=progress)[['X', 'Y', 'Z']]


# The atom of a residue the ribbon or backbone trace passes through, where bonds from other molecules end
RIBBON_ANCHOR_ATOMS = ('CA', "C4'")


def bonds_to_ribbon(atoms, bonds):
    """
    `bonds` with every link between another molecule and a protein or nucleic acid atom moved to end at that
    residue's alpha carbon (or C4'). Ribbons don't draw the residue's own atoms, so a bond to one, such as heme's
    iron to a histidine nitrogen, would stop in mid air next to the ribbon.
    """
    rows = atoms.drop_duplicates('atom_num').set_index('atom_num')
    is_atom_row = (rows['row'] == 'ATOM').to_dict()
    residue_of = dict(zip(rows.index, zip(rows['chain'], rows['resid'])))
    anchors = atoms[atoms['atom'].isin(RIBBON_ANCHOR_ATOMS)].drop_duplicates(['chain', 'resid'])
    anchor_of = dict(zip(zip(anchors['chain'], anchors['resid']), anchors['atom_num']))
    moved = []
    for bond in bonds:
        a, b = int(bond['atom_num1']), int(bond['atom_num2'])
        if a in is_atom_row and b in is_atom_row and is_atom_row[a] != is_atom_row[b]:
            ribbon_end = a if is_atom_row[a] else b
            other = b if ribbon_end == a else a
            anchor = anchor_of.get(residue_of[ribbon_end])
            if anchor is not None:
                moved.append({'atom_num1': int(anchor), 'atom_num2': other})
                continue
        moved.append(bond)
    return moved


def split_chains(df):
    """{chain: its rows}, the same rows in the same order as pdbm.get_chain gives."""
    return {chain: rows for chain, rows in df.groupby('chain', sort=False)}


def chain_work(chain_df):
    """Expected work of a chain's ribbon and backbone."""
    residues = chain_df["residue"]
    if residues.isin(AMINO_ACIDS).any():
        return len(chain_df) * PROTEIN_WORK
    if residues.isin(NUCLEOTIDES).any():
        return len(chain_df) * NUCLEIC_WORK
    return 0


def build(builder):
    """Write <name>_<chain>_ribbon and <name>_<chain>_backbone per chain, plus _hetatm and _hetatm_bonds."""
    config = builder.config
    by_chain = config["by_chain"]
    bar_helix = config.get('bar_style', False)
    atoms = builder.df
    df = atoms[atoms['polymer']].drop(columns=['polymer', 'segment'])
    # Helices and strands from the file, worked out for chains it doesn't describe (from the unscaled atoms: the
    # hydrogen bond energies need real distances)
    unscaled = pdbm.structure_to_df(builder.structure)
    helices_and_strands = secondary_structure.complete(builder.structure, unscaled[unscaled['row'] == 'ATOM'])
    df = pdbm.add_structure_from_structured_data(df, SimpleNamespace(structural_info=helices_and_strands))

    dna_vectors = pdbm.DNA_vectors(df, width=1)
    chains = pdbm.enumerate_chains(df)
    # Each chain's rows, split off once: looking every chain up in the whole model is slow with many chains
    chain_frames = split_chains(df)
    het_work = part_work(atoms, config)
    builder.report(4)
    builder.plan({**{chain: chain_work(chain_frames[chain]) for chain in chains},
                  "hetatm": het_work["hetatm"] * HETATM_WORK, "hetatm_bonds": het_work["hetatm_bonds"] * HETATM_WORK})

    for chain in chains:
        chain_df = chain_frames[chain]
        colour = str(builder.numbers.get(chain, 1))
        residues = chain_df["residue"]
        within = builder.step(chain, f"Drawing chain {chain}...", compute=0.95)
        if residues.isin(AMINO_ACIDS).any():
            ribbon_cells, loop_cells = protein_cartoon(chain_df, config['scale'], bar_helix, progress=within)
            ribbon = pd.DataFrame(ribbon_cells, columns=['X', 'Y', 'Z'])
            backbone = pd.DataFrame(loop_cells, columns=['X', 'Y', 'Z']) if config["backbone"] else None
        elif residues.isin(NUCLEOTIDES).any():
            ribbon = pdbm.sidechain(chain_df[chain_df["atom"].isin(RIBOSE_ATOMS + BASE_ATOMS)])[['X', 'Y', 'Z']]
            backbone = nucleic_backbone(chain_df, dna_vectors, progress=within) if config["backbone"] else None
        else:
            continue
        within(1.0)

        ribbon = ribbon.astype(float).round().astype(int)
        ribbon['atom'] = colour if by_chain else "ribbon_atom"
        builder.write(ribbon, f"{chain}_ribbon", atoms=chain_df)
        if backbone is not None and not backbone.empty:
            backbone = backbone.astype(float).round().astype(int)
            backbone['atom'] = colour if by_chain else "backbone_atom"
            builder.write(backbone, f"{chain}_backbone", atoms=chain_df)

    if config["show_hetatm"]:
        builder.step("hetatm", "Placing the other molecules...")
        linked = SimpleNamespace(bonds=bonds_to_ribbon(atoms, builder.structure.bonds))
        spheres, bonds = hetatm_blocks(atoms, linked, config)
        builder.write(spheres, "hetatm")
        builder.step("hetatm_bonds")
        builder.write(bonds, "hetatm_bonds")
    builder.report(100)


def run_mode(config_data, pdb_name, structure, mc_dir, progress=None):
    build(ModelBuilder(config_data, structure, mc_dir, name=pdb_name, progress=progress))
