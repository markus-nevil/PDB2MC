"""Ribbon mode's protein cartoon, the secondary structure it is drawn from, and residue sizes in Amino Acids mode."""
import os

import numpy as np
import pandas as pd
import pytest

from PDB2MC import build, cli, defaults, pdb_manipulation as pdbm, ribbon, secondary_structure
from PDB2MC.structure_data import StructureData
from conftest import preset


def protein_atoms(name):
    structure = StructureData.from_file(preset(name))
    atoms = pdbm.structure_to_df(structure)
    return structure, atoms[atoms['row'] == 'ATOM']


def per_residue(info, keys):
    label = {}
    for chain, start, end, kind in zip(info['chain'], info['resid1'], info['resid2'], info['structure']):
        for r in range(int(start), int(end) + 1):
            label.setdefault((chain, r), kind)
    return np.array([label.get(key, '') for key in keys], dtype=object)


# --- secondary structure ---

@pytest.mark.parametrize("name, least", [("Hemoglobin", 0.85), ("Nucleosome", 0.85), ("Helix", 0.85)])
def test_worked_out_structure_agrees_with_the_file(name, least):
    structure, atoms = protein_atoms(name)
    residues = secondary_structure.backbone(atoms)
    keys = list(zip(residues['chain'], residues['resid']))
    given = per_residue(structure.structural_info, keys)
    found = per_residue(secondary_structure.structural_info(atoms), keys)
    assert (given == found).mean() >= least
    # Whatever is found as helix or strand, the file says so too (almost always)
    assert ((found != '') & (given != found)).sum() <= 0.02 * len(keys)


def test_sheet_example_has_strands_and_the_helix_example_a_helix():
    for name, kind in (("Sheet", "sheet"), ("Helix", "helix")):
        _, atoms = protein_atoms(name)
        assert set(secondary_structure.structural_info(atoms)['structure']) == {kind}


def test_files_with_good_records_keep_them():
    structure, atoms = protein_atoms("Hemoglobin")
    assert secondary_structure.complete(structure, atoms).equals(structure.structural_info)


def test_chains_without_records_get_worked_out_ones():
    structure, atoms = protein_atoms("Hemoglobin")
    structure.structural_info = structure.structural_info.iloc[0:0]
    info = secondary_structure.complete(structure, atoms)
    assert set(info['chain']) == {'A', 'B', 'C', 'D'} and set(info['structure']) == {'helix'}


def test_chains_the_file_barely_describes_get_worked_out_ones():
    # The GFP example has atoms for chain A only, but sheet records for chains B to D and just one strand for A
    structure, atoms = protein_atoms("GFP")
    file_sheets = structure.structural_info
    assert (file_sheets[file_sheets['chain'] == 'A']['structure'] == 'sheet').sum() == 1
    info = secondary_structure.complete(structure, atoms)
    assert (info[info['chain'] == 'A']['structure'] == 'sheet').sum() >= 10        # GFP's β-barrel has 11 strands


# --- the cartoon ---

def chain_frame(name, scale, chain='A'):
    structure = StructureData.from_file(preset(name))
    df = build.prepare_coordinates(structure, scale)
    df = df[df['polymer'] & (df['chain'] == chain)]
    atoms = pdbm.structure_to_df(structure)
    info = secondary_structure.complete(structure, atoms[atoms['row'] == 'ATOM'])
    from types import SimpleNamespace
    return pdbm.add_structure_from_structured_data(df, SimpleNamespace(structural_info=info))


def neighbours_of(cells):
    taken = set(map(tuple, cells.tolist()))
    steps = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1) if (a, b, c) != (0, 0, 0)]
    return [sum((x + a, y + b, z + c) in taken for a, b, c in steps) for x, y, z in taken]


@pytest.mark.parametrize("name, bars", [("GFP", False), ("Hemoglobin", False), ("Hemoglobin", True), ("Sheet", False)])
def test_cartoon_has_no_loose_blocks(name, bars):
    ribbon_cells, loop_cells = ribbon.protein_cartoon(chain_frame(name, 2), 2, bar_helix=bars)
    cells = np.unique(np.concatenate([ribbon_cells, loop_cells]), axis=0)
    assert len(cells) and min(neighbours_of(cells)) >= 1


def test_ribbon_follows_the_alpha_carbons():
    df = chain_frame("GFP", 3)
    ribbon_cells, loop_cells = ribbon.protein_cartoon(df, 3)
    cells = np.concatenate([ribbon_cells, loop_cells])
    ca = df[df['atom'] == 'CA'][['Xf', 'Yf', 'Zf']].to_numpy(dtype=float)
    from scipy.spatial import cKDTree
    distance, _ = cKDTree(cells).query(ca)
    assert distance.max() <= 1.5           # the curve goes through every residue


def test_strands_end_in_arrows_and_are_wider_than_helices():
    kinds = np.array(['None'] + ['sheet'] * 5 + ['None'] + ['helix'] * 5 + ['None'], dtype=object)
    u = np.linspace(0, len(kinds) - 1, 1201)
    half = ribbon._ribbon_profile(kinds, u, 1)
    at = lambda residue: half[np.argmin(np.abs(u - residue))]
    assert at(3) == ribbon.STRAND_HALF_WIDTH > at(9) == ribbon.HELIX_HALF_WIDTH
    assert at(4.4) > at(3)                  # the arrow head starts wider than the strand
    assert at(5.49) < 0.1 * ribbon.ARROW_HALF_WIDTH  # and comes to a point
    assert at(0) == at(6) == 0              # loops are tubes, not ribbons


def helix_points(count, scale):
    turn = 100 / 180 * np.pi
    return np.array([[2.3 * np.cos(t), 1.5 * t / turn, 2.3 * np.sin(t)] for t in np.arange(count) * turn]) * scale


def test_helix_rods_are_straight_from_first_to_last_alpha_carbon():
    points = helix_points(12, 3)
    kinds = np.array(['None'] + ['helix'] * 10 + ['None'], dtype=object)
    rods = ribbon._rods(points, kinds, 3)
    assert len(rods) == 1
    cells = rods[0].astype(float)
    start, end = points[1], points[10]
    direction = (end - start) / np.linalg.norm(end - start)
    offset = cells - start
    from_axis = np.linalg.norm(offset - (offset @ direction)[:, None] * direction, axis=1)
    assert from_axis.max() <= ribbon.ROD_DIAMETER * 3 / 2 + 1       # a straight rod around the start-end line
    along = offset @ direction
    assert along.min() <= 1 and along.max() >= np.linalg.norm(end - start) - 1
    middle = np.rint((start + end) / 2).astype(int)
    assert not (rods[0] == middle).all(axis=1).any()                # and hollow


def test_loops_meet_the_rods():
    df = chain_frame("Hemoglobin", 2)
    ribbon_cells, loop_cells = ribbon.protein_cartoon(df, 2, bar_helix=True)
    from scipy.spatial import cKDTree
    distance, _ = cKDTree(ribbon_cells).query(loop_cells)
    assert (distance <= 1.8).sum() >= 2 * len(ribbon._helix_runs(
        df.drop_duplicates('resid')['structure'].to_numpy(dtype=object)))  # each rod touched at both ends


def test_ribbons_are_one_block_thick_at_scale_3():
    assert max(ribbon.ribbon_thickness * 3, 1.0) == 1.0


@pytest.mark.parametrize("name, moved", [("Hemoglobin", 4), ("GFP", 2)])
def test_bonds_from_other_molecules_end_on_the_ribbon(name, moved):
    structure = StructureData.from_file(preset(name))
    df = build.prepare_coordinates(structure, 3)
    bonds = ribbon.bonds_to_ribbon(df, structure.bonds)
    changed = [new for new, old in zip(bonds, structure.bonds) if new != old]
    assert len(changed) == moved
    rows = df.drop_duplicates('atom_num').set_index('atom_num')
    for bond in changed:
        assert rows.at[bond['atom_num1'], 'atom'] in ribbon.RIBBON_ANCHOR_ATOMS
        assert rows.at[bond['atom_num2'], 'row'] == 'HETATM'
    # Bonds within the other molecules stay as they were
    assert len(bonds) == len(structure.bonds)


def test_chain_gaps_are_not_bridged():
    ca = np.array([[0, 0, 0], [3.8, 0, 0], [7.6, 0, 0], [30, 0, 0], [33.8, 0, 0]], dtype=float)
    assert ribbon._segments(ca, 1) == [(0, 3), (3, 5)]


# --- residue sizes in Amino Acids mode ---

def test_residue_scale_follows_the_protein_scale():
    assert defaults.residue_scale(1) == 1.0 and defaults.residue_scale(4) == 4.0     # 1:1
    config = defaults.scaled_config("Amino Acids", 3)
    assert config['scale'] == 3 and config['atom_scale'] == 3.0
    assert defaults.scaled_config("Skeleton", 3)['atom_scale'] == defaults.default_config("Skeleton")['atom_scale']


def test_command_line_scales_the_residues(tmp_path, monkeypatch):
    world = tmp_path / "saves" / "world"
    world.mkdir(parents=True)
    seen = {}
    monkeypatch.setattr(build, "build_model", lambda mode, config, **kwargs: seen.update(config) or "helix")
    assert cli.main(["Amino Acids", preset("Helix"), str(world), "--scale", "4"]) == 0
    assert seen['atom_scale'] == 4.0
