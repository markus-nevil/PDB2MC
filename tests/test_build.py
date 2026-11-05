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
    if mode == "Space Filling":
        # the surface is recomputed without the hidden residue; the gap it leaves can add surface
        assert modified['surface'] != plain['surface']
    else:
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

def test_shrake_rupley_points():
    # a lone sphere keeps every test point, on its surface
    points, owner = space_filling.accessible_points([[0, 0, 0]], [2.0])
    assert len(points) >= space_filling.MIN_POINTS and (owner == 0).all()
    assert np.allclose(np.linalg.norm(points, axis=1), 2.0)
    # two overlapping spheres: no kept point lies inside the other sphere
    centres = np.array([[0.0, 0, 0], [2.0, 0, 0]])
    points, owner = space_filling.accessible_points(centres, [2.0, 1.5])
    assert set(owner) == {0, 1}
    other = centres[1 - owner]
    assert (np.linalg.norm(points - other, axis=1) >= np.array([2.0, 1.5])[1 - owner] - 1e-6).all()
    # a sphere inside a bigger one has no accessible points
    points, owner = space_filling.accessible_points([[0, 0, 0], [0.5, 0, 0]], [3.0, 1.0])
    assert set(owner) == {0}


def test_sas_is_probe_centre_distance_from_atoms():
    structure, atoms = atoms_of(preset("Helix"))
    polymer = atoms[atoms['polymer']].reset_index(drop=True)
    coords, owner = space_filling.sas_surface(polymer, 1.0)
    radii = space_filling.vdw_radii(polymer['element']) + space_filling.SASA_radius
    centres = polymer[['Xf', 'Yf', 'Zf']].to_numpy()
    # every block is (within rounding) one probe radius beyond the van der Waals surface of its atom
    distance = np.linalg.norm(coords - centres[owner], axis=1)
    assert np.abs(distance - radii[owner]).max() <= 0.87
    # and no closer than that to any atom
    from scipy.spatial import cKDTree
    gap, nearest = cKDTree(centres).query(coords)
    assert (gap >= radii[nearest] - 0.87).all()


@pytest.mark.parametrize("name, scale", [("Helix", 1.0), ("GFP", 1.0), ("GFP", 2.0)])
def test_sas_surface_is_closed(name, scale):
    from scipy import ndimage
    structure, atoms = atoms_of(preset(name)) if scale == 1.0 else (None, build.prepare_coordinates(
        pdbm.load_structure(preset(name)), scale))
    polymer = atoms[atoms['polymer']].reset_index(drop=True)
    coords, _ = space_filling.sas_surface(polymer, scale)
    origin = coords.min(axis=0) - 1
    grid = np.zeros(coords.max(axis=0) - origin + 2, dtype=bool)
    grid[tuple((coords - origin).T)] = True
    empty, _ = ndimage.label(~grid)
    outside = empty == empty[0, 0, 0]
    # no atom can be reached from outside without passing through the surface
    assert not outside[tuple((polymer[['X', 'Y', 'Z']].to_numpy(dtype=int) - origin).T)].any()


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


def test_chains_differing_in_case_keep_their_own_files(tmp_path, mc_dir):
    # mmCIF chain ids are case sensitive ('A' and 'a'); Minecraft file names are lowercase
    text = open(preset("Helix")).read()
    atom_lines = [line for line in text.splitlines(keepends=True) if line.startswith("ATOM")]
    second = [line[:21] + "a" + line[22:] for line in atom_lines]
    first = [line[:21] + "A" + line[22:] for line in atom_lines]
    path = tmp_path / "cases.pdb"
    path.write_text("".join(first) + "TER\n" + "".join(second) + "END\n")
    parts = build_parts("Ribbon", mc_dir, str(path))
    assert {"a_backbone", "a_backbone_2"} <= set(parts)
    assert build.safe_name("My Model:A") == "my_model_a"


def test_unknown_mode():
    with pytest.raises(ValueError):
        build.mode_module("Nope")
    with pytest.raises(ValueError):
        defaults.default_config("Nope")


# --- SASA radius ---

def surface_blocks(mc_dir, radius):
    config = defaults.default_config("Space Filling")
    config.update(pdb_file=preset("Helix"), save_path=mc_dir, sasa_radius=radius)
    build.build_model("Space Filling", config)
    directory = mcf.structure_dirs(mc_dir)[0]
    return sum(len(read_positions(os.path.join(directory, f))) for f in os.listdir(directory)
               if f.startswith("helix_surface"))


def test_sasa_radius_changes_the_surface(mc_dir):
    assert surface_blocks(mc_dir, 3.0) > surface_blocks(mc_dir, 1.4) > surface_blocks(mc_dir, 0.0) > 0


def test_sasa_radius_default_is_the_water_probe():
    assert defaults.default_config("Space Filling")['sasa_radius'] == space_filling.SASA_radius == 1.4


def test_sas_surface_uses_the_radius_it_is_given():
    atoms = build.prepare_coordinates(pdbm.load_structure(preset("ALA")), 2.0).reset_index(drop=True)
    small, _ = space_filling.sas_surface(atoms, 2.0, probe_radius=0.5)
    large, _ = space_filling.sas_surface(atoms, 2.0, probe_radius=2.5)
    assert np.ptp(large, axis=0).max() > np.ptp(small, axis=0).max()


def test_faster_voxel_search_gives_the_same_result():
    """sas_surface numbers the voxels instead of using np.unique(axis=0); which atom owns a voxel must not change."""
    voxels = np.random.default_rng(0).integers(-50, 50, size=(5000, 3))
    coords, first = np.unique(voxels, axis=0, return_index=True)
    low = voxels.min(axis=0)
    span = voxels.max(axis=0) - low + 1
    keys = ((voxels[:, 0] - low[0]) * span[1] + voxels[:, 1] - low[1]) * span[2] + voxels[:, 2] - low[2]
    _, fast = np.unique(keys, return_index=True)
    assert (fast == first).all() and (voxels[fast] == coords).all()


# --- model names ---

@pytest.mark.parametrize("typed, expected", [
    ("1UBQ", "1ubq"), ("My Model", "my-model"), ("gfp_red", "gfp-red"), ("  a  b ", "a-b"), ("../../x", "x"),
    ("v1.2", "v1.2"), ("Ünï", "n"), ("---", ""), ("", ""),
])
def test_custom_model_names(typed, expected):
    assert build.custom_model_name(typed) == expected


def test_custom_name_replaces_the_structure_name(mc_dir, skeleton_config):
    skeleton_config.update(pdb_file=preset("Helix"), save_path=mc_dir, model_name="My Helix")
    assert build.build_model("Skeleton", skeleton_config) == "my-helix"
    functions = os.listdir(mcf.function_dirs(mc_dir)[0])
    assert "build_my-helix.mcfunction" in functions and "clear_my-helix.mcfunction" in functions
    assert any(f.startswith("my-helix_") for f in os.listdir(mcf.structure_dirs(mc_dir)[0]))


def test_blank_name_uses_the_structure_name(mc_dir, skeleton_config):
    skeleton_config.update(pdb_file=preset("Helix"), save_path=mc_dir, model_name="  ")
    assert build.build_model("Skeleton", skeleton_config) == "helix"


def test_similar_custom_names_do_not_touch_each_other(mc_dir, skeleton_config):
    """With '_' allowed, "gfp_red" would count as a part of "gfp" and be deleted when "gfp" is rebuilt."""
    skeleton_config.update(pdb_file=preset("Helix"), save_path=mc_dir)
    build.build_model("Skeleton", {**skeleton_config, 'model_name': "gfp_red"})
    build.build_model("Skeleton", {**skeleton_config, 'model_name': "gfp"})
    build.build_model("Skeleton", {**skeleton_config, 'model_name': "gfp"})
    assert "build_gfp-red.mcfunction" in os.listdir(mcf.function_dirs(mc_dir)[0])


def test_dotted_name_with_per_part_functions(mc_dir, skeleton_config):
    """Each part needs its own function; os.path.splitext used to cut 'v1.2_backbone_part0' down to 'v1'."""
    skeleton_config.update(pdb_file=preset("Helix"), save_path=mc_dir, model_name="v1.2", simple=False)
    build.build_model("Skeleton", skeleton_config)
    functions = os.listdir(mcf.function_dirs(mc_dir)[0])
    assert "build_v1.2_backbone_part0.mcfunction" in functions
    assert len([f for f in functions if f.startswith("build_")]) > 2


# --- metal ions ---

def all_blocks(mc_dir, prefix):
    """The set of blocks in every structure part of a model whose name starts with prefix."""
    directory = mcf.structure_dirs(mc_dir)[0]
    blocks = set()
    for filename in os.listdir(directory):
        if filename.startswith(prefix):
            blocks |= set(read_blocks(os.path.join(directory, filename)).values())
    return blocks


METAL_PDB = "".join(pdb_line("HETATM", i + 1, name, name, "A", 200 + i, 3.0 * i, 0, 0, element)
                    for i, (name, element) in enumerate([("ZN", "ZN"), ("CA", "CA"), ("FE", "FE"), ("XE", "XE")]))
PROTEIN_ATOM = pdb_line("ATOM", 10, "CA", "ALA", "A", 1, 20, 20, 20, "C")


@pytest.mark.parametrize("mode", ["Custom", "Skeleton", "X-Ray", "Space Filling", "Ribbon", "Amino Acids"])
def test_metal_ions_use_their_blocks_in_every_mode(mode, mc_dir, write_pdb):
    config = defaults.default_config(mode)
    config['atoms'].update(ZN="gold_block", CA="stone", other_atom="dirt")
    # Ribbons need more than one atom, and this test is about the metals
    pdb = METAL_PDB if mode == "Ribbon" else METAL_PDB + PROTEIN_ATOM
    config.update(pdb_file=write_pdb(pdb), save_path=mc_dir, scale=3.0)
    build.build_model(mode, config)
    blocks = all_blocks(mc_dir, "test_hetatm")
    assert {"gold_block", "stone", "iron_block", "dirt"} <= blocks       # xenon is not a metal: "other" colour


def test_calcium_setting_leaves_alpha_carbons_alone(mc_dir, write_pdb):
    """'CA' is both calcium and the alpha carbon atom name."""
    config = defaults.default_config("Custom")
    config['atoms'].update(CA="stone", C="black_wool")
    pdb = pdb_line("ATOM", 1, "CA", "ALA", "A", 1, 0, 0, 0, "C") + pdb_line("ATOM", 2, "CB", "ALA", "A", 1, 1.5, 0, 0, "C")
    config.update(pdb_file=write_pdb(pdb), save_path=mc_dir, atom_scale=1.0)
    build.build_model("Custom", config)
    assert all_blocks(mc_dir, "test_atoms") == {"black_wool"}


# --- progress ---

ALL_MODES = ["Custom", "Skeleton", "X-Ray", "Space Filling", "Ribbon", "Amino Acids"]


def run_with_progress(mode, mc_dir, structure="Helix", **changes):
    config = defaults.default_config(mode)
    config.update(pdb_file=preset(structure), save_path=mc_dir, scale=2.0, **changes)
    values, messages = [], []
    build.build_model(mode, config, progress=values.append, status=messages.append)
    return values, messages


@pytest.mark.parametrize("mode", ALL_MODES)
def test_progress_rises_steadily_to_100(mode, mc_dir):
    values, messages = run_with_progress(mode, mc_dir)
    assert values == sorted(set(values)) and values[0] == 0 and values[-1] == 100
    assert all(isinstance(value, int) for value in values)
    assert len(values) >= 12                                     # used to be about 8 steps
    assert max(b - a for a, b in zip(values, values[1:])) <= 34  # no big jumps
    assert messages[0] == "Reading structure file..." and messages[-1] == "Done!"
    assert len(messages) >= 4


def test_progress_handles_switched_off_parts(mc_dir):
    values, _ = run_with_progress("Custom", mc_dir, backbone=False, sidechain=False, show_atoms=False,
                                  show_hetatm=False)
    assert values == sorted(set(values)) and values[-1] == 100


def test_surface_search_reports_as_it_goes():
    fractions = []
    centres = np.random.default_rng(1).random((500, 3)) * 30
    space_filling.accessible_points(centres, np.full(500, 3.0), progress=fractions.append)
    assert len(fractions) >= space_filling.MIN_BATCHES and fractions == sorted(fractions) and fractions[-1] == 1.0


def test_surface_search_with_fewer_atoms_than_batches():
    points, owners = space_filling.accessible_points(np.zeros((1, 3)), np.array([2.0]))
    assert len(points) >= space_filling.MIN_POINTS and set(owners) == {0}


def test_chain_order_of_ribbon_work():
    """A DNA strand is far slower than a protein chain of the same size; the bar has to know."""
    from PDB2MC import ribbon
    protein = pd.DataFrame({"residue": ["ALA"] * 100})
    dna = pd.DataFrame({"residue": ["DA"] * 100})
    assert ribbon.chain_work(dna) > 3 * ribbon.chain_work(protein) > 0
    assert ribbon.chain_work(pd.DataFrame({"residue": ["XYZ"] * 100})) == 0


def test_progress_object_never_falls_and_skips_repeats():
    seen = []
    progress = build.Progress(seen.append)
    for value in (0, 10.2, 10.9, 5, 50, 500):
        progress.update(value)
    assert seen == [0, 10, 50, 100]


def test_progress_span_maps_a_part_of_the_work():
    seen = []
    build.Progress(seen.append).span(20, 40)(50)
    assert seen == [30]


def test_plan_gives_steps_room_by_work():
    class Host(build.ModelBuilder):
        def __init__(self):
            self._position, self._steps, self._write_range = 0, {}, None
            self._progress, self._status = reported.append, messages.append

    reported, messages = [], []
    host = Host()
    host.plan({"a": 1, "b": 0, "c": 3})
    host.step("a", "first")
    host.step("c")
    assert reported == [0, 25] and messages == ["first"]
    assert host._steps["b"] == (25, 25)


def test_on_structure_receives_the_structure(mc_dir, skeleton_config):
    skeleton_config.update(pdb_file=preset("Helix"), save_path=mc_dir)
    seen = []
    build.build_model("Skeleton", skeleton_config, on_structure=seen.append)
    assert seen[0].name == "helix"


# --- structure parts ---

def test_parts_are_slices_of_the_model(mc_dir):
    """Minecraft walks the bounding box of each placed structure: parts must not all span the whole model."""
    x = np.random.default_rng(2).permutation(1000)
    df = pd.DataFrame({'X': x, 'Y': 0, 'Z': 0, 'atom': 'C'})
    mcf.create_nbt(df, "wide_atoms", False, mc_dir, {'C': 'stone'})
    directory = mcf.structure_dirs(mc_dir)[0]
    spans = [np.ptp(read_positions(os.path.join(directory, f"wide_atoms_part{i}.nbt"))[:, 0]) for i in range(4)]
    assert max(spans) < 300


def test_read_positions_matches_the_slow_reader(tmp_path):
    from nbt import nbt
    from PDB2MC.nbt_writer import write_structure
    coords = np.array([[0, 1, 2], [-5, 70, 300], [7, 7, 7]])
    path = write_structure(str(tmp_path / "s.nbt"), coords, ["stone", "dirt", "stone"])
    slow = [[int(v.value) for v in block["pos"]] for block in nbt.NBTFile(path)["blocks"]]
    assert read_positions(path).tolist() == slow == coords.tolist()


def test_read_positions_of_an_empty_structure(tmp_path):
    from PDB2MC.nbt_writer import write_structure
    path = write_structure(str(tmp_path / "s.nbt"), np.zeros((0, 3), dtype=int), [])
    assert read_positions(path).shape == (0, 3)


def test_read_positions_of_a_file_saved_by_minecraft(tmp_path):
    """Vanilla structure files have their keys in another order."""
    from nbt import nbt
    root = nbt.NBTFile()
    root.name = ""
    block = nbt.TAG_Compound()
    block.tags.append(nbt.TAG_Int(name="state", value=0))
    pos = nbt.TAG_List(name="pos", type=nbt.TAG_Int)
    pos.tags.extend(nbt.TAG_Int(value=v) for v in (1, 2, 3))
    block.tags.append(pos)
    blocks = nbt.TAG_List(name="blocks", type=nbt.TAG_Compound)
    blocks.tags.append(block)
    root.tags.append(blocks)
    path = str(tmp_path / "vanilla.nbt")
    root.write_file(path)
    assert read_positions(path).tolist() == [[1, 2, 3]]


def test_write_structure_reports_up_to_one(tmp_path):
    from PDB2MC.nbt_writer import write_structure
    seen = []
    write_structure(str(tmp_path / "s.nbt"), np.zeros((50000, 3), dtype=int), ["stone"] * 50000, progress=seen.append)
    assert seen == sorted(seen) and seen[-1] == 1.0 and len(seen) >= 2


def test_create_nbt_reports_up_to_one(mc_dir):
    seen = []
    df = pd.DataFrame({'X': range(1000), 'Y': 0, 'Z': 0})
    mcf.create_nbt(df, "m_backbone", False, mc_dir, {'backbone_atom': 'stone'}, progress=seen.append)
    assert seen[-1] == 1.0 and max(seen) == 1.0
