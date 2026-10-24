import os

import pytest

from PDB2MC import minecraft_functions as mcf, pdb_manipulation as pdbm, skeleton, variables
from PDB2MC.structure_data import StructureData
from conftest import pdb_line, preset
from test_minecraft_functions import read_blocks


def build(config, path, mc_dir):
    """Run the full skeleton pipeline the way SkeletonWindow's worker does; return {category: blocks}."""
    structure = pdbm.load_structure(path)
    name = structure.name
    mcf.delete_old_files(mc_dir, name)
    skeleton.run_mode(config, name, structure, mc_dir)
    mcf.finish_nbts(mc_dir, config, name)
    mcf.create_nbt_delete(name, mc_dir)
    mcf.finish_delete_nbts(mc_dir, name)
    out = {}
    for d in mcf.structure_dirs(mc_dir):
        for filename in os.listdir(d):
            category = filename.rsplit("_part", 1)[0]
            out.setdefault((os.path.basename(d), category), {}).update(read_blocks(os.path.join(d, filename)))
    return name, out


def test_gfp_end_to_end(skeleton_config, mc_dir):
    name, blocks = build(skeleton_config, preset("GFP"), mc_dir)
    assert name == "gfp"
    for folder in mcf.STRUCTURE_DIRS:
        for part in ("backbone", "sidechain", "hetatm"):
            assert blocks[(folder, f"gfp_{part}")], part
            assert blocks[(folder, f"delete_gfp_{part}")].keys() == blocks[(folder, f"gfp_{part}")].keys()
    assert blocks[("structures", "gfp_backbone")] == blocks[("structure", "gfp_backbone")]
    assert set(blocks[("structures", "gfp_backbone")].values()) == {"gray_concrete"}
    assert set(blocks[("structures", "gfp_sidechain")].values()) == {"light_gray_concrete"}
    for d in mcf.function_dirs(mc_dir):
        assert {"build_gfp.mcfunction", "clear_gfp.mcfunction"} <= set(os.listdir(d))


def test_rebuild_is_deterministic_and_replaces_old_files(skeleton_config, mc_dir):
    _, first = build(skeleton_config, preset("Helix"), mc_dir)
    _, second = build(skeleton_config, preset("Helix"), mc_dir)
    assert first == second
    skeleton_config["sidechain"] = False
    _, third = build(skeleton_config, preset("Helix"), mc_dir)
    assert ("structures", "helix_sidechain") not in third


def test_color_by_chain(skeleton_config, mc_dir):
    skeleton_config["by_chain"] = True
    _, blocks = build(skeleton_config, preset("Hemoglobin"), mc_dir)
    chains = {b["chain"] for b in StructureData.from_pdb(preset("Hemoglobin")).atoms if not b["hetatm"]}
    expected = {variables.chain_blocks[str(i + 1)] for i in range(len(chains))}
    assert set(blocks[("structures", "hemoglobin_backbone")].values()) == expected
    assert set(blocks[("structures", "hemoglobin_sidechain")].values()) <= expected


def test_backbone_not_drawn_across_missing_residues(skeleton_config, mc_dir, write_pdb):
    # residues 1 and 3 (residue 2 missing): no backbone blocks between x=5 and x=12
    text = "".join(pdb_line("ATOM", i + 1, atom, "GLY", "A", resid, x, 0, 0, atom[0])
                   for i, (atom, resid, x) in enumerate([("N", 1, 0), ("CA", 1, 1.46), ("C", 1, 2.98),
                                                         ("N", 3, 14), ("CA", 3, 15.46), ("C", 3, 16.98)]))
    skeleton_config.update(sidechain=False, show_hetatm=False)
    _, blocks = build(skeleton_config, write_pdb(text, "gap.pdb"), mc_dir)
    xs = sorted({x - 40 for x, _, _ in blocks[("structures", "gap_backbone")]})
    assert not any(5 <= x <= 12 for x in xs)


def test_other_colour_used_for_unlisted_elements(skeleton_config, mc_dir, write_pdb):
    text = (pdb_line("HETATM", 1, "ZN", "ZN", "A", 1, 0, 0, 0, "ZN")
            + pdb_line("HETATM", 2, "FE", "HEM", "A", 2, 10, 0, 0, "FE"))
    skeleton_config["atoms"]["other_atom"] = "cyan_wool"
    _, blocks = build(skeleton_config, write_pdb(text, "ions.pdb"), mc_dir)
    assert set(blocks[("structures", "ions_hetatm")].values()) == {"cyan_wool", "iron_block"}


def test_empty_structure_raises(skeleton_config, mc_dir, write_pdb):
    structure = StructureData.from_pdb(write_pdb("END\n", "empty.pdb"))
    with pytest.raises(ValueError):
        skeleton.run_mode(skeleton_config, "empty", structure, mc_dir)


def test_dna_preset(skeleton_config, mc_dir):
    _, blocks = build(skeleton_config, preset("DNA"), mc_dir)
    assert blocks[("structure", "dna_backbone")] and blocks[("structure", "dna_sidechain")]
