import os
import sys

import pytest

# Qt must run headless in tests / CI; set before anything imports PyQt6
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

PRESETS = os.path.join(REPO, "UI", "presets")


def pdb_line(record, serial, name, resname, chain, resid, x, y, z, element="", altloc=" "):
    """One fixed-column PDB ATOM/HETATM line."""
    name_field = name if len(name) == 4 else f" {name:<3}"
    return (f"{record:<6}{serial:>5} {name_field}{altloc}{resname:>3} {chain}{resid:>4}    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}{1.0:6.2f}{0.0:6.2f}          {element:>2}\n")


@pytest.fixture
def write_pdb(tmp_path):
    """write_pdb(text, name='test.pdb') -> path"""
    def _write(text, name="test.pdb"):
        path = tmp_path / name
        path.write_text(text)
        return str(path)
    return _write


@pytest.fixture
def mc_dir(tmp_path):
    """
    The datapack function folder of a fresh world, in the mixed-separator form MinecraftPopup produces
    on Windows (<world>\\datapacks/mcPDB/data/protein/functions).
    """
    world = tmp_path / "saves" / "world"
    functions = world / "datapacks" / "mcPDB" / "data" / "protein" / "functions"
    functions.mkdir(parents=True)
    return str(world) + os.sep + "datapacks/mcPDB/data/protein/functions"


def preset(name):
    return os.path.join(PRESETS, f"{name}.pdb")


SKELETON_CONFIG = {
    'atoms': {'O': 'red_wool', 'N': 'blue_wool', 'P': 'lime_wool', 'S': 'yellow_wool', 'C': 'black_wool',
              'FE': 'iron_block', 'other_atom': 'pink_concrete', 'backbone_atom': 'gray_concrete',
              'sidechain_atom': 'light_gray_concrete'},
    'backbone_size': 1.0, 'atom_scale': 1.5, 'scale': 1.0, 'show_hetatm': True,
    'backbone': True, 'sidechain': True, 'by_chain': False, 'simple': True,
}


@pytest.fixture
def skeleton_config():
    import copy
    return copy.deepcopy(SKELETON_CONFIG)
