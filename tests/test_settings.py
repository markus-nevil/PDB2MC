import json
import os
import subprocess
import sys

import pytest

from PDB2MC import defaults, user_settings
from PDB2MC.variables import decorative_blocks


def test_default_metal_blocks_are_real_blocks():
    assert set(defaults.default_metal_blocks().values()) <= set(decorative_blocks)


def test_iron_keeps_its_block():
    assert defaults.default_metal_blocks()["FE"] == "iron_block"


def test_every_mode_has_the_metal_blocks():
    for mode in defaults.MODES:
        atoms = defaults.default_config(mode)['atoms']
        for metal, block in defaults.default_metal_blocks().items():
            assert atoms[metal] == block


def test_settings_start_empty():
    assert user_settings.load() == {}
    assert user_settings.metal_blocks() == defaults.default_metal_blocks()
    assert user_settings.structure_dir() == ""


def test_metal_blocks_survive_a_new_process():
    user_settings.set_metal_blocks({**defaults.default_metal_blocks(), "ZN": "gold_block"})
    code = "from PDB2MC import user_settings; print(user_settings.metal_blocks()['ZN'])"
    output = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True,
                            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assert output.stdout.strip() == "gold_block"


def test_only_changed_metals_are_saved():
    user_settings.set_metal_blocks({**defaults.default_metal_blocks(), "ZN": "gold_block"})
    assert user_settings.load()["metal_blocks"] == {"ZN": "gold_block"}


def test_saved_values_that_make_no_sense_are_ignored():
    user_settings.save({"metal_blocks": {"ZN": "not_a_block", "UNOBTANIUM": "gold_block", "CU": "stone"}})
    blocks = user_settings.metal_blocks()
    assert blocks["ZN"] == defaults.default_metal_blocks()["ZN"]
    assert blocks["CU"] == "stone"
    assert "UNOBTANIUM" not in blocks


@pytest.mark.parametrize("content", ["not json {", "[1, 2]", ""])
def test_damaged_file_gives_defaults(content):
    os.makedirs(user_settings.settings_dir(), exist_ok=True)
    with open(user_settings.settings_path(), "w") as f:
        f.write(content)
    assert user_settings.metal_blocks() == defaults.default_metal_blocks()
    user_settings.set_structure_dir("")         # and can be saved over


def test_damaged_file_is_kept():
    os.makedirs(user_settings.settings_dir(), exist_ok=True)
    with open(user_settings.settings_path(), "w") as f:
        f.write("not json {")
    user_settings.load()
    assert os.path.isfile(user_settings.settings_path() + ".bad")


def test_saving_leaves_no_temporary_files():
    user_settings.update(a=1)
    user_settings.update(b=2)
    assert os.listdir(user_settings.settings_dir()) == ["settings.json"]
    assert user_settings.load() == {"a": 1, "b": 2}


def test_structure_folder(tmp_path):
    user_settings.set_structure_dir(str(tmp_path))
    assert user_settings.structure_dir() == str(tmp_path)


def test_missing_structure_folder_is_not_offered_but_stays_saved(tmp_path):
    folder = tmp_path / "unplugged"
    folder.mkdir()
    user_settings.set_structure_dir(str(folder))
    folder.rmdir()
    assert user_settings.structure_dir() == ""
    assert user_settings.saved_structure_dir() == str(folder)


@pytest.mark.parametrize("platform, variable, expected", [
    ("win32", "APPDATA", os.path.join("users", "me", "Roaming", "PDB2MC")),
    ("linux", "XDG_CONFIG_HOME", os.path.join("users", "me", "Roaming", "PDB2MC")),
])
def test_settings_live_in_the_users_folder_not_next_to_the_program(monkeypatch, platform, variable, expected):
    """A --onefile .exe unpacks to a temporary folder, so a file beside the code would be lost on exit."""
    monkeypatch.delenv(user_settings.DIRECTORY_VARIABLE)
    monkeypatch.setattr(sys, "platform", platform)
    monkeypatch.setenv(variable, os.path.join("users", "me", "Roaming"))
    assert user_settings.settings_dir() == expected


def test_settings_do_not_depend_on_the_frozen_bundle(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "temporary_bundle"), raising=False)
    user_settings.update(a=1)
    assert user_settings.load() == {"a": 1}
    assert "temporary_bundle" not in user_settings.settings_path()


def test_settings_file_is_plain_json():
    user_settings.update(structure_dir="x")
    with open(user_settings.settings_path()) as f:
        assert json.load(f) == {"structure_dir": "x"}
