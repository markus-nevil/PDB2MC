import os

import pandas as pd
import pytest
from nbt import nbt

from PDB2MC import minecraft_functions as mcf, variables


def read_blocks(path):
    """{(x, y, z): block} of an .nbt structure file."""
    n = nbt.NBTFile(path)
    palette = [str(p["Name"].value).replace("minecraft:", "") for p in n["palette"]]
    return {tuple(int(v.value) for v in b["pos"]): palette[b["state"].value] for b in n["blocks"]}


windows_only = pytest.mark.skipif(os.sep != "\\", reason="backslash is only a path separator on Windows")


@pytest.mark.parametrize("path", [
    pytest.param(r"C:\Users\me\AppData\Roaming\.minecraft\saves\My World\datapacks/mcPDB/data/protein/functions",
                 marks=windows_only),
    "C:/Users/me/AppData/Roaming/.minecraft/saves/My World/datapacks/mcPDB/data/protein/functions",
    pytest.param(r"C:\Users\me\AppData\Roaming\.minecraft\saves\My World\datapacks\mcPDB\data\protein\function",
                 marks=windows_only),
])
def test_world_dir_handles_any_separator_mix(path):
    assert os.path.normpath(mcf.world_dir(path)).endswith(os.path.normpath("saves/My World"))


def test_structure_dirs_cover_old_and_new_minecraft(mc_dir):
    dirs = mcf.structure_dirs(mc_dir)
    world = mcf.world_dir(mc_dir)
    assert dirs == [os.path.join(world, "generated", "mc", "structures"),
                    os.path.join(world, "generated", "mc", "structure")]
    assert all(os.path.isdir(d) for d in dirs)


def test_create_nbt_writes_parts_and_delete_structures_to_both_folders(mc_dir):
    df = pd.DataFrame({'X': range(10), 'Y': 0, 'Z': 0, 'atom': ['C', 'O', 'ZN', '3', '2b'] * 2})
    blocks = {'C': 'black_wool', 'O': 'red_wool', 'other_atom': 'cyan_concrete'}
    mcf.create_nbt(df, "1ABC_hetatm", air=False, dir=mc_dir, blocks=blocks)
    contents = []
    for d in mcf.structure_dirs(mc_dir):
        names = sorted(os.listdir(d))
        assert names == sorted([f"1abc_hetatm_part{i}.nbt" for i in range(4)]
                               + [f"delete_1abc_hetatm_part{i}.nbt" for i in range(4)])
        placed, cleared = {}, {}
        for name in names:
            (cleared if name.startswith("delete_") else placed).update(read_blocks(os.path.join(d, name)))
        contents.append((placed, cleared))
        # +40 X/Z offset; colours: atom, "other" fallback, chain number, dark chain number
        assert placed[(40, 0, 40)] == 'black_wool'
        assert placed[(42, 0, 40)] == 'cyan_concrete'
        assert placed[(43, 0, 40)] == variables.chain_blocks['3']
        assert placed[(44, 0, 40)] == variables.dark_skeleton_blocks['2b']
        assert set(cleared) == set(placed) and set(cleared.values()) == {'air'}
    assert contents[0] == contents[1]


def test_create_nbt_skips_empty_frames(mc_dir):
    assert mcf.create_nbt(pd.DataFrame(columns=['X', 'Y', 'Z']), "x_backbone", False, mc_dir, {}) == []
    assert os.listdir(mcf.structure_dirs(mc_dir)[0]) == []


def test_create_nbt_raises_instead_of_failing_silently(mc_dir, monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("disk full")
    monkeypatch.setattr(mcf, "_write_structure", boom)
    with pytest.raises(OSError, match="disk full"):
        mcf.create_nbt(pd.DataFrame({'X': [0], 'Y': [0], 'Z': [0]}), "x_backbone", False, mc_dir, {})


def test_create_nbt_works_with_read_only_numpy_views(mc_dir):
    # pandas copy-on-write hands out read-only arrays; the +40 offset must not write into them
    df = pd.DataFrame({'X': [0, 1], 'Y': [0, 0], 'Z': [0, 0]})
    mcf.create_nbt(df, "ro_backbone", False, mc_dir, {'backbone_atom': 'stone'})
    assert df['X'].tolist() == [0, 1]


def test_chain_blocks_are_real_blocks():
    known = set(variables.decorative_blocks)
    for block in list(variables.chain_blocks.values()) + list(variables.dark_skeleton_blocks.values()):
        assert block in known, block


def touch(directory, *names):
    os.makedirs(directory, exist_ok=True)
    for name in names:
        open(os.path.join(directory, name), "w").close()


def test_delete_old_files_only_touches_this_model(mc_dir):
    funcs = mcf.function_dirs(mc_dir)
    for d in funcs:
        touch(d, "build_1abc.mcfunction", "clear_1abc.mcfunction", "build_1abc_backbone_part0.mcfunction",
              "build_1abcd.mcfunction", "clear_1abcd.mcfunction", "my_own.mcfunction")
    for d in mcf.structure_dirs(mc_dir):
        touch(d, "1abc_backbone_part0.nbt", "delete_1abc_backbone_part0.nbt", "1abcd_backbone_part0.nbt",
              "delete_1abcd_backbone_part0.nbt")
    mcf.delete_old_files(mc_dir, "1ABC")
    for d in funcs:
        assert sorted(os.listdir(d)) == ["build_1abcd.mcfunction", "clear_1abcd.mcfunction", "my_own.mcfunction"]
    for d in mcf.structure_dirs(mc_dir):
        assert sorted(os.listdir(d)) == ["1abcd_backbone_part0.nbt", "delete_1abcd_backbone_part0.nbt"]


def test_finish_functions_written_to_both_function_folders(mc_dir):
    df = pd.DataFrame({'X': [0, 1], 'Y': [0, 0], 'Z': [0, 0]})
    mcf.create_nbt(df, "m_backbone", False, mc_dir, {'backbone_atom': 'stone'})
    mcf.create_nbt(df.assign(atom='C'), "m_hetatm", False, mc_dir, {'C': 'black_wool'})
    mcf.create_nbt(df, "mm_backbone", False, mc_dir, {'backbone_atom': 'stone'})   # another model
    mcf.finish_nbts(mc_dir, {"simple": True}, "M")
    mcf.create_nbt_delete("M", mc_dir)
    mcf.finish_delete_nbts(mc_dir, "M")
    for d in mcf.function_dirs(mc_dir):
        build = open(os.path.join(d, "build_m.mcfunction")).read().splitlines()
        clear = open(os.path.join(d, "clear_m.mcfunction")).read().splitlines()
        placed = [line.split(":", 1)[1] for line in build if line.startswith("place template")]
        assert set(placed) == {"m_backbone_part0", "m_backbone_part1", "m_hetatm_part0", "m_hetatm_part1"}
        assert placed[-2:] == ["m_backbone_part0", "m_backbone_part1"]   # backbone placed last
        assert {line.split(":", 1)[1] for line in clear if line.startswith("place")} == {f"delete_{p}" for p in placed}


def test_individual_functions(mc_dir):
    mcf.create_nbt(pd.DataFrame({'X': [0], 'Y': [0], 'Z': [0]}), "m_backbone", False, mc_dir, {})
    mcf.finish_nbts(mc_dir, {"simple": False}, "m")
    for d in mcf.function_dirs(mc_dir):
        assert os.listdir(d) == ["build_m_backbone_part0.mcfunction"]


def test_create_nbt_delete_converts_only_missing_delete_files(mc_dir):
    nbt_dir = mcf.structure_dirs(mc_dir)[0]
    mcf.create_nbt(pd.DataFrame({'X': [0], 'Y': [0], 'Z': [0]}), "m_backbone", False, mc_dir, {})
    os.remove(os.path.join(nbt_dir, "delete_m_backbone_part0.nbt"))
    mcf.create_nbt_delete("m", mc_dir)
    for d in mcf.structure_dirs(mc_dir):
        assert set(read_blocks(os.path.join(d, "delete_m_backbone_part0.nbt")).values()) == {'air'}


def test_delete_all_keeps_unrelated_functions(mc_dir):
    funcs = mcf.function_dirs(mc_dir)[0]
    touch(funcs)
    with open(os.path.join(funcs, "build_x.mcfunction"), "w") as f:
        f.write("place template mc:x_part0\n")
    with open(os.path.join(funcs, "hello.mcfunction"), "w") as f:
        f.write("say hello\n")
    touch(mcf.structure_dirs(mc_dir)[1], "x_part0.nbt")
    mcf.delete_nbt_mcfunctions_from_dir(mc_dir)
    assert os.listdir(funcs) == ["hello.mcfunction"]
    assert os.listdir(mcf.structure_dirs(mc_dir)[1]) == []
