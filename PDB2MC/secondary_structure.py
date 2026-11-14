"""
Working out where the helices and β-strands are, for files that don't say (most AlphaFold predictions and many
homemade models have no HELIX / SHEET records, which left their ribbons as plain lines).

This is the core of DSSP (Kabsch & Sander 1983), the method the Protein Data Bank itself uses: backbone hydrogen
bonds from an electrostatic energy, α-helices from two consecutive i -> i+4 turns, and β-strands from ladders of
bridges between residues (in the same chain or another). 3-10 and π helices and β-bulges are left out.
"""
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from PDB2MC.structure_data import STRUCTURAL_INFO_COLUMNS

# DSSP's constants: energy in kcal/mol, a hydrogen bond below -0.5
ENERGY_FACTOR = 0.084 * 332
HBOND_ENERGY = -0.5
# Residues further apart than this (CA to CA, angstrom) can't share a backbone hydrogen bond
PAIR_DISTANCE = 9.0
# Length of N-H, angstrom
NH_LENGTH = 1.0
# A chain's own HELIX / SHEET records are used when they cover at least this share of the residues found here
COVERAGE = 0.5
# Helix turn lengths, in order of precedence: α, then 3-10 and π helices
HELIX_TURNS = (4, 3, 5)
# Neighbouring residues further apart than this (C to N, angstrom) are not joined: a gap in the chain
PEPTIDE_BOND = 2.0


def backbone(atoms):
    """
    One row per protein residue with all of N, CA, C, O, in file order: chain, resid, residue and their coordinates
    (n_x ... o_z). `atoms` is a DataFrame with chain, resid, residue, atom, X, Y, Z.
    """
    atoms = atoms[atoms['atom'].isin(['N', 'CA', 'C', 'O'])]
    keys = ['chain', 'resid']
    first = atoms.drop_duplicates(keys + ['atom'])
    wide = first.pivot_table(index=keys, columns='atom', values=['X', 'Y', 'Z'], aggfunc='first', sort=False)
    wide = wide.dropna()
    if wide.empty:
        return pd.DataFrame()
    order = atoms.drop_duplicates(keys).set_index(keys).index
    wide = wide.reindex([key for key in order if key in wide.index])
    residues = atoms.drop_duplicates(keys).set_index(keys)['residue']
    out = pd.DataFrame(index=wide.index)
    out['residue'] = residues.reindex(wide.index).to_numpy()
    for atom in ('N', 'CA', 'C', 'O'):
        for axis in 'XYZ':
            out[f"{atom.lower()}_{axis.lower()}"] = wide[(axis, atom)].to_numpy(dtype=float)
    return out.reset_index()


def _xyz(res, atom):
    return res[[f"{atom}_x", f"{atom}_y", f"{atom}_z"]].to_numpy(dtype=float)


def hydrogen_bonds(res):
    """
    Boolean matrix-like set of DSSP hydrogen bonds as {(i, j)}: the C=O of residue i bonded to the N-H of residue j
    (indices into res).
    """
    n, ca, c, o = (_xyz(res, atom) for atom in ('n', 'ca', 'c', 'o'))
    count = len(res)
    chain = res['chain'].to_numpy()
    # Residue j continues from j-1 when they're in the same chain and joined by a peptide bond
    joined = np.zeros(count, dtype=bool)
    joined[1:] = (chain[1:] == chain[:-1]) & (np.linalg.norm(n[1:] - c[:-1], axis=1) < PEPTIDE_BOND)
    # Amide hydrogen: on N, opposite the previous residue's C=O (none for a chain's first residue or a proline)
    h = np.full_like(n, np.nan)
    direction = c[:-1] - o[:-1]
    direction /= np.linalg.norm(direction, axis=1)[:, None]
    h[1:] = n[1:] + NH_LENGTH * direction
    has_h = joined & (res['residue'].to_numpy() != 'PRO')

    pairs = cKDTree(ca).query_pairs(PAIR_DISTANCE, output_type='ndarray')
    if not len(pairs):
        return set(), joined
    # Both directions: acceptor i (C=O) to donor j (N-H)
    acceptor = np.concatenate([pairs[:, 0], pairs[:, 1]])
    donor = np.concatenate([pairs[:, 1], pairs[:, 0]])
    keep = has_h[donor] & (np.abs(acceptor - donor) > 1)
    acceptor, donor = acceptor[keep], donor[keep]

    def distance(a, b):
        return np.linalg.norm(a - b, axis=1)
    energy = ENERGY_FACTOR * (1 / distance(o[acceptor], n[donor]) + 1 / distance(c[acceptor], h[donor])
                              - 1 / distance(o[acceptor], h[donor]) - 1 / distance(c[acceptor], n[donor]))
    bonded = energy < HBOND_ENERGY
    return set(zip(acceptor[bonded].tolist(), donor[bonded].tolist())), joined


def assign(res):
    """'H' (α-helix), 'E' (β-strand) or '' for each residue of `res` (see backbone())."""
    count = len(res)
    hbonds, joined = hydrogen_bonds(res)
    # Residue i and i+k are in one unbroken stretch of chain
    run_start = np.zeros(count, dtype=int)
    for i in range(1, count):
        run_start[i] = run_start[i - 1] if joined[i] else i

    def linked(i, k):
        return 0 <= i and i + k < count and run_start[i + k] == run_start[i] if k >= 0 else \
            0 <= i + k and i < count and run_start[i + k] == run_start[i]

    labels = np.array([''] * count, dtype=object)

    # Helices: n-turns starting at i-1 and at i make i .. i+n-1 helical. α (n = 4) first; then 3-10 (n = 3) and π
    # (n = 5) helices where nothing else is, which ribbons draw as helices too
    for n in HELIX_TURNS:
        turn = np.array([linked(i, n) and (i, i + n) in hbonds for i in range(count)])
        for i in range(1, count):
            if turn[i - 1] and turn[i]:
                span = slice(i, i + n)
                if n == 4:
                    labels[span] = 'H'
                elif not any(labels[span]):
                    labels[span] = 'H'

    # β-bridges between residues i and j (not near each other in one chain)
    def hb(a, b):
        return (a, b) in hbonds

    bridges = {}
    candidates = {(min(a, b), max(a, b)) for a, b in hbonds}
    for a, b in list(candidates):
        for i0 in (a - 1, a, a + 1):
            for j0 in (b - 1, b, b + 1):
                if 0 <= i0 < j0 < count and not (run_start[i0] == run_start[j0] and j0 - i0 < 3):
                    candidates.add((i0, j0))
    for i, j in candidates:
        if i < 1 or j < 1 or i + 1 >= count or j + 1 >= count:
            continue
        if not (linked(i, -1) and linked(i, 1) and linked(j, -1) and linked(j, 1)):
            continue
        if (hb(i - 1, j) and hb(j, i + 1)) or (hb(j - 1, i) and hb(i, j + 1)):
            bridges[(i, j)] = 'parallel'
        elif (hb(i, j) and hb(j, i)) or (hb(i - 1, j + 1) and hb(j - 1, i + 1)):
            bridges[(i, j)] = 'antiparallel'

    # Ladders: two or more bridges in a row make β-strands on both sides
    for (i, j), kind in bridges.items():
        step = 1 if kind == 'parallel' else -1
        if (i + 1, j + step) in bridges and bridges[(i + 1, j + step)] == kind:
            for k in (i, i + 1, j, j + step):
                if labels[k] != 'H':
                    labels[k] = 'E'
    return labels


def structural_info(atoms):
    """The helix and sheet ranges of `atoms` worked out with assign(), as StructureData.structural_info rows."""
    res = backbone(atoms)
    if res.empty:
        return pd.DataFrame(columns=STRUCTURAL_INFO_COLUMNS)
    labels = assign(res)
    rows = []
    start = None
    for k in range(len(res) + 1):
        same = (k < len(res) and start is not None and labels[k] == labels[start]
                and res['chain'].iat[k] == res['chain'].iat[start] and res['resid'].iat[k] == res['resid'].iat[k - 1] + 1)
        if same:
            continue
        if start is not None and labels[start]:
            end = k - 1
            rows.append([res['chain'].iat[start], res['residue'].iat[start], int(res['resid'].iat[start]),
                         res['residue'].iat[end], int(res['resid'].iat[end]),
                         'helix' if labels[start] == 'H' else 'sheet'])
        start = k if k < len(res) else None
    return pd.DataFrame(rows, columns=STRUCTURAL_INFO_COLUMNS)


def _residue_count(info):
    return (info['resid2'].astype(int) - info['resid1'].astype(int) + 1).clip(lower=0).groupby(info['chain']).sum()


def complete(structure, atoms):
    """
    The structure's helix and sheet ranges for drawing: the file's own ranges for each chain they describe well,
    and ranges worked out here for chains the file says nothing (or much too little) about, such as AlphaFold
    predictions or files cut down from a bigger entry.
    """
    given = structure.structural_info
    worked_out = structural_info(atoms)
    if worked_out.empty:
        return given
    if given.empty:
        return worked_out
    found = _residue_count(worked_out)
    described = _residue_count(given).reindex(found.index, fill_value=0)
    # The file's ranges stand when they cover at least COVERAGE of what is found here
    replace = set(found.index[described < COVERAGE * found])
    if not replace:
        return given
    return pd.concat([given[~given['chain'].isin(replace)], worked_out[worked_out['chain'].isin(replace)]],
                     ignore_index=True)
