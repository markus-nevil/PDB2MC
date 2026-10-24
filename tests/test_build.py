import gzip
import os

import numpy as np
import pandas as pd
import pytest
from nbt import nbt

from PDB2MC import amino_acids, build, cli, defaults, minecraft_functions as mcf, pdb_manipulation as pdbm, space_filling
from PDB2MC.nbt_writer import read_positions, structure_bytes, write_structure
from PDB2MC.structure_data import StructureData, infer_bonds
from conftest import pdb_line, preset
from test_minecraft_functions import read_blocks


def build_parts(mode, mc_dir, path, **changes):
    """Run build_model for a mode; return {part: {(x, y, z): block}} of the 'structure' folder."""
    config = defaults.default_config(mode)
    config.update(pdb_file=path, save_path=mc_dir, **changes)
    name = build.build_model(mode, config)
    folder = mcf.structure_dirs(mc_dir)[1]
    parts = {}
    for filename in os.listdir(folder):
        if not filename.startswith("delete_"):
            part = filename.rsplit("_part", 1)[0][len(name) + 1:]
            parts.setdefault(part, {}).update(read_blocks(os.path.join(folder, filename)))
    return parts


def atoms_of(path):
    structure = pdbm.load_structure(path)
    return structure, build.prepare_coordinates(structure, 1.0)


# --- NBT writer ---

def test_nbt_writer_layout(tmp_path):
    coords = np.array([[1, -2, 3], [4, 1, 0], [50, 0, 0]])
    path = write_structure(str(tmp_path / "x.nbt"), coords, ["stone", "minecraft:red_wool", "stone"])
    n = nbt.NBTFile(path)
    assert [t.name for t in n.tags] == ["size", "entities", "blocks", "palette", "DataVersion"]
    assert [t.value for t in n["size"]] == [32, 4, 4]          # capped at 32 like nbt-structure-utils
    assert [p["Name"].value for p in n["palette"]] == ["minecraft:stone", "minecraft:red_wool"]
    assert read_blocks(path) == {(1, -2, 3): "stone", (4, 1, 0): "red_wool", (50, 0, 0): "stone"}
    assert read_positions(path).tolist() == coords.tolist()


def test_nbt_writer_matches_nbt_structure_utils(tmp_path):
    utils = pytest.importorskip("nbt_structure_utils")
    rng = np.random.default_rng(3)
    coords = np.unique(rng.integers(-3, 40, (400, 3)), axis=0)
    blocks = rng.choice(["stone", "air", "red_wool"], len(coords))
    structure = utils.NBTStructure()
    for (x, y, z), block in zip(coords, blocks):
        structure.set_block(utils.Vector(int(x), int(y), int(z)), utils.BlockData(block))
    path = str(tmp_path / "ref.nbt")
    structure.get_nbt(pressurize=False, align_to_origin=False).write_file(filename=path)
    assert gzip.open(path).read() == structure_bytes(coords, blocks)


def test_empty_structure_file(tmp_path):
    path = write_structure(str(tmp_path / "e.nbt"), np.zeros((0, 3)), [])
    assert read_blocks(path) == {}


# --- bonds ---

def test_gfp_chromophore_bonds_and_links():
    structure = StructureData.from_pdb(preset("GFP"))
    by_num = {a['atom_num']: a for a in structure.atoms}
    cro = [b for b in structure.bonds
           if by_num[b['atom_num1']]['residue'] == by_num[b['atom_num2']]['residue'] == 'CRO']
    assert len(cro) >= 20              # GFP has no CONECT records: these are inferred from distances
    links = {tuple(sorted((by_num[b['atom_num1']]['atom'], by_num[b['atom_num2']]['atom'])))
             for b in structure.bonds if by_num[b['atom_num1']]['hetatm'] != by_num[b['atom_num2']]['hetatm']}
    assert links == {("C", "N1"), ("C3", "N")}     # the LINK records to Phe64 and Val68


def test_bonds_from_conect_are_not_replaced(write_pdb):
    text = (pdb_line("HETATM", 1, "C1", "LIG", "A", 1, 0, 0, 0, "C")
            + pdb_line("HETATM", 2, "C2", "LIG", "A", 1, 1.5, 0, 0, "C")
            + pdb_line("HETATM", 3, "C3", "LIG", "A", 1, 3.0, 0, 0, "C")
            + "CONECT    1    2\n")
    structure = StructureData.from_pdb(write_pdb(text))
    assert [(b['atom_num1'], b['atom_num2']) for b in structure.bonds] == [(1, 2)]


def test_infer_bonds_by_covalent_radius():
    atoms = [dict(atom_num=i, x=x, y=0.0, z=0.0, element=e)
             for i, (x, e) in enumerate([(0, 'C'), (1.5, 'C'), (3.5, 'C'), (6.2, 'FE'), (8.2, 'N')], 1)]
    assert infer_bonds(atoms) == [(1, 2), (4, 5)]


def test_waters_get_no_bonds(write_pdb):
    text = (pdb_line("HETATM", 1, "O", "HOH", "A", 1, 0, 0, 0, "O")
            + pdb_line("HETATM", 2, "O", "HOH", "A", 2, 1.0, 0, 0, "O"))
    assert StructureData.from_pdb(write_pdb(text)).bonds == []


def test_mmcif_struct_conn(tmp_path):
    cif = tmp_path / "link.cif"
    cif.write_text("""data_TEST
_entry.id TEST
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
ATOM   1 C C   . GLY A 1 ? 0.0 0.0 0.0 1 GLY A C   1
HETATM 2 N N1  . LIG B . ? 1.3 0.0 0.0 2 LIG A N1  1
HETATM 3 C C2  . LIG B . ? 2.7 0.0 0.0 2 LIG A C2  1
loop_
_struct_conn.id
_struct_conn.conn_type_id
_struct_conn.ptnr1_auth_asym_id
_struct_conn.ptnr1_auth_seq_id
_struct_conn.ptnr1_label_atom_id
_struct_conn.ptnr2_auth_asym_id
_struct_conn.ptnr2_auth_seq_id
_struct_conn.ptnr2_label_atom_id
covale1 covale A 1 C A 2 N1
""")
    structure = StructureData.from_mmcif(str(cif))
    assert {(b['atom_num1'], b['atom_num2']) for b in structure.bonds} == {(1, 2), (2, 3)}


# --- backbone through linked HETATM residues ---

@pytest.mark.parametrize("mode", ["Skeleton", "Amino Acids", "Custom"])
def test_backbone_passes_through_gfp_chromophore(mode, mc_dir):
    structure, atoms = atoms_of(preset("GFP"))
    parts = build_parts(mode, mc_dir, preset("GFP"), show_hetatm=False, show_atoms=False, sidechain=False)
    backbone = {(x - 40, y, z - 40) for x, y, z in parts["backbone"]}
    # the shortest bond path N1-CA1-C1-N3-CA3-C3 is the chromophore's backbone
    cro = atoms[(atoms['residue'] == 'CRO') & atoms['atom'].isin(['CA1', 'CA3'])]
    assert len(cro)
    # without the fix there were no backbone blocks anywhere in the chromophore
    for x, y, z in cro[['X', 'Y', 'Z']].to_numpy():
        assert (x, y, z) in backbone or mode == "Amino Acids"
    if mode == "Amino Acids":
        assert any(np.abs(np.array(list(backbone)) - cro[['X', 'Y', 'Z']].to_numpy()[1]).sum(axis=1) <= 3)


def test_linked_residue_lines_follow_bond_path():
    structure, atoms = atoms_of(preset("GFP"))
    lines = build.linked_residue_lines(atoms, structure.bonds, False, {})
    assert set(lines['atom']) == {'backbone_atom'}
    cro_n1 = atoms[(atoms['residue'] == 'CRO') & (atoms['atom'] == 'N1')][['X', 'Y', 'Z']].to_numpy()[0]
    assert (lines[['X', 'Y', 'Z']].to_numpy() == cro_n1).all(axis=1).any()


# --- residue modifications ---

def test_residue_modifications_parse():
    mods = build.ResidueModifications({"A": {"3": ["hide"], "4": ["block:stone", "hide"], 5: ["block:glass"]}})
    assert mods.hidden == {"A:3", "A:4"} and mods.blocks == {"A:4": "stone", "A:5": "glass"}
    assert not build.ResidueModifications({})


@pytest.mark.parametrize("mode", defaults.MODES)
def test_hide_and_block_apply_to_every_mode(mode, mc_dir):
    path = preset("Helix")
    structure, atoms = atoms_of(path)
    chain = atoms['chain'].iloc[0]
    resids = sorted(atoms.loc[atoms['polymer'], 'resid'].unique())
    hidden, coloured = int(resids[3]), int(resids[6])
    mods = {chain: {str(hidden): ["hide"], str(coloured): ["block:diamond_block"]}}
    plain = build_parts(mode, mc_dir, path)
    modified = build_parts(mode, mc_dir, path, residue_mods=mods)

    owner = build.ResidueModifications.key
    # Amino Acids attributes blocks to the nearest residue centre, the other modes to the nearest atom
    tree_atoms = amino_acids.residue_centres(atoms) if mode == "Amino Acids" else atoms[atoms['polymer']]
    from scipy.spatial import cKDTree
    tree = cKDTree(tree_atoms[['X', 'Y', 'Z']].to_numpy(dtype=float))
    keys = np.array([owner(c, r) for c, r in zip(tree_atoms['chain'], tree_atoms['resid'])])
    all_blocks = {pos: block for part in modified.values() for pos, block in part.items()}
    blocks = np.array(list(all_blocks.values()))
    assert "diamond_block" in blocks
    # Space filling models are lifted to start at y=0, so their blocks are not in atom coordinates
    if mode != "Space Filling":
        _, nearest = tree.query(np.array([(x - 40, y, z - 40) for x, y, z in all_blocks]))
        assert (blocks[keys[nearest] == owner(chain, coloured)] == "diamond_block").all()
        assert not (keys[nearest] == owner(chain, hidden)).any()
    assert sum(map(len, modified.values())) < sum(map(len, plain.values()))


# --- chain colours ---

def test_chain_colour_list_repeats(mc_dir):
    parts = build_parts("Skeleton", mc_dir, preset("Hemoglobin"), by_chain=True,
                        chain_blocks=["stone", "diamond_block"], show_hetatm=False)
    assert set(parts["backbone"].values()) == {"stone", "diamond_block"}
    assert set(parts["sidechain"].values()) == {"stone", "diamond_block"}


def test_invalid_chain_colours_fall_back_to_default():
    assert build.valid_chain_blocks(["nope"]) == build.DEFAULT_CHAIN_BLOCKS
    assert build.valid_chain_blocks(["nope", "stone"]) == ["stone"]
    assert build.dark_block("red_concrete") == "red_terracotta"
    assert build.dark_block("stone") == "stone"
    assert build.chain_block_dict(["red_wool"]) == {"1": "red_wool", "1b": "red_terracotta"}


def test_space_filling_by_chain_uses_list(mc_dir):
    parts = build_parts("Space Filling", mc_dir, preset("Hemoglobin"), by_chain=True,
                        chain_blocks=["stone", "glass"], show_hetatm=False)
    assert set(parts["surface"].values()) == {"stone", "glass"}
    assert set(parts["branch"].values()) == {"stone", "glass"}     # stone/glass have no darker partner


# --- space filling ---

def test_surface_encloses_atoms_and_skeleton():
    structure, atoms = atoms_of(preset("Helix"))
    polymer = atoms[atoms['polymer']]
    points = polymer[['X', 'Y', 'Z']].to_numpy(dtype=int)
    shell, (solid, origin) = space_filling.surface_shell(points, 1.0, return_solid=True)
    inside = solid[tuple((points - origin).T)]
    assert inside.all()
    # the shell is the outer layer of the solid: every shell block touches empty space
    padded = np.pad(solid, 1)
    s = shell - origin + 1
    neighbours = [padded[s[:, 0] + dx, s[:, 1] + dy, s[:, 2] + dz]
                  for dx, dy, dz in [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]]
    assert (~np.array(neighbours)).any(axis=0).all()


def test_space_filling_parts_line_up(mc_dir):
    parts = build_parts("Space Filling", mc_dir, preset("GFP"))
    surface = np.array(list(parts["surface"]))
    lo, hi = surface.min(axis=0), surface.max(axis=0)
    for name in ("branch", "hetatm", "hetatm_bonds"):
        coords = np.array(list(parts[name]))
        assert (coords >= lo).all() and (coords <= hi).all(), name
    assert surface[:, 1].min() == min(c[1] for part in parts.values() for c in part) == 0


def test_mesh_keeps_a_tenth_of_the_surface(mc_dir):
    full = build_parts("Space Filling", mc_dir, preset("Helix"))["surface"]
    mesh = build_parts("Space Filling", mc_dir, preset("Helix"), mesh=True)["surface"]
    assert 0.05 < len(mesh) / len(full) < 0.15
    assert set(mesh) <= set(full)


# --- every mode / preset ---

@pytest.mark.parametrize("mode", defaults.MODES)
@pytest.mark.parametrize("name", ["DNA", "ATP", "Sheet"])
def test_modes_build_presets(mode, name, mc_dir):
    parts = build_parts(mode, mc_dir, preset(name))
    assert parts and all(parts.values())
    expected = {"DNA": "backbone", "ATP": "hetatm", "Sheet": "backbone"}[name]
    if mode == "Space Filling":
        expected = {"DNA": "surface", "ATP": "hetatm", "Sheet": "surface"}[name]
    assert any(part.endswith(expected) for part in parts), parts.keys()


def test_cli(tmp_path, capsys):
    world = tmp_path / "saves" / "world"
    assert cli.main(["Skeleton", preset("Helix"), str(world), "--scale", "2"]) == 0
    assert "build_helix" in capsys.readouterr().out
    assert (world / "datapacks" / "mcPDB" / "pack.mcmeta").exists()
    assert any(f.startswith("helix_backbone") for f in os.listdir(world / "generated" / "mc" / "structure"))


def test_unknown_mode():
    with pytest.raises(ValueError):
        build.mode_module("Nope")
    with pytest.raises(ValueError):
        defaults.default_config("Nope")
