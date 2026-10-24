import math
import os

import pytest

pytest.importorskip("pytestqt")

from PyQt6 import QtWidgets
from PyQt6.QtCore import QRect

from PDB2MC import defaults, minecraft_functions as mcf, pdb_manipulation as pdbm
from conftest import preset

MODE_NAMES = ["Custom", "Skeleton", "X-Ray", "Space Filling", "Ribbon", "Amino Acids"]


@pytest.fixture(autouse=True)
def fresh_session():
    """Each test starts without a model / save chosen in an earlier test."""
    from UI.session import SESSION
    SESSION.reset()
    yield SESSION
    SESSION.reset()


@pytest.fixture(autouse=True)
def quiet_popups(monkeypatch):
    """Information boxes are recorded instead of shown."""
    from UI import base_mode_window
    shown = []
    monkeypatch.setattr(base_mode_window.InformationBox, "show", lambda self: shown.append(self.windowTitle()))
    return shown


def make_window(qtbot, mode):
    from UI.base_mode_window import create_mode_window
    window = create_mode_window(mode)
    qtbot.addWidget(window)
    return window


@pytest.fixture
def skeleton_window(qtbot):
    return make_window(qtbot, "Skeleton")


def test_main_window_opens_skeleton_mode(qtbot, monkeypatch):
    from PDB2MC import run_PDB2MC
    monkeypatch.setattr(run_PDB2MC.MainWindow, "is_outdated", lambda self: None)
    window = run_PDB2MC.MainWindow()
    qtbot.addWidget(window)
    window.handle_dropdown_change("Skeleton")   # raised NameError (ENABLE_HOT_RELOAD) before
    assert window.skeleton_window.isVisible()
    qtbot.addWidget(window.skeleton_window)


@pytest.mark.parametrize("mode", MODE_NAMES)
def test_mode_window_layout(qtbot, mode):
    from UI.sidebar import SIDEBAR_WIDTH
    window = make_window(qtbot, mode)
    assert window.MODE_NAME == mode
    rects = {name: QRect(*geom) for name, geom in window.geometry_map.items()}
    overlaps = [(a, b) for a in rects for b in rects if a < b and rects[a].intersects(rects[b])]
    assert overlaps == []
    size = window.size()
    assert all(r.left() >= SIDEBAR_WIDTH and r.right() < size.width() and r.bottom() < size.height()
               for r in rects.values())
    # Every mode has the Skeleton window's shared controls
    for name in ("selectPDBFileButton", "selectIncludedPDBButton", "selectMinecraftSaveButton",
                 "selectedPDBLabel", "selectedMinecraftLabel", "modifyResiduesButton",
                 "createFunctionsButton", "pScaleSpinBox", "sidebar"):
        assert hasattr(window, name), name


@pytest.mark.parametrize("mode", MODE_NAMES)
def test_window_config_matches_defaults(qtbot, mode):
    window = make_window(qtbot, mode)
    config = window.build_config()
    expected = defaults.default_config(mode)
    for key in ("scale", "show_hetatm", "mesh", "backbone", "by_chain", "atom_scale", "bar_style"):
        assert config[key] == expected[key], key
    for key, block in expected['atoms'].items():
        assert config['atoms'][key] == block, key
    if mode == "Amino Acids":
        assert config['amino_acids'] == expected['amino_acids']


def test_color_boxes_have_separators(skeleton_window):
    w = skeleton_window
    for box in (w.backboneColorBox, w.sidechainColorBox, w.otherColorBox):
        assert sum(box.itemText(i) == "" for i in range(box.count())) == 4


def test_check_input_keeps_first_item_unique(skeleton_window):
    box = skeleton_window.otherColorBox
    count = box.count()
    box.setCurrentText(box.itemText(0))
    skeleton_window.check_input(box, ["red_concrete"])
    assert box.count() == count            # index 0 was treated as "missing" and duplicated before
    box.setCurrentText("Diamond Block")
    from PDB2MC.variables import decorative_blocks
    skeleton_window.check_input(box, decorative_blocks)
    assert box.currentText() == "diamond_block"


def test_preset_selection_sets_path_and_scale(skeleton_window, quiet_popups):
    skeleton_window.save_selected_text("GFP")
    assert os.path.isabs(skeleton_window.user_pdb_file) and os.path.exists(skeleton_window.user_pdb_file)
    assert skeleton_window.selectedPDBLabel.toolTip().endswith("GFP.pdb")
    maximum = pdbm.check_max_size(preset("GFP"), world_max=320)
    assert maximum > 2
    assert skeleton_window.pScaleSpinBox.value() == math.floor(maximum)   # whole number, rounded down
    assert quiet_popups == ["Maximum scale"]


def test_too_large_model_keeps_scale(skeleton_window, quiet_popups, monkeypatch):
    from UI import base_mode_window
    monkeypatch.setattr(base_mode_window, "suggested_scale", lambda path: (False, None))
    skeleton_window.set_pdb_file(preset("GFP"))
    assert skeleton_window.pScaleSpinBox.value() == 1.0
    assert quiet_popups == ["Model too large!"]


def test_switching_modes_keeps_model_save_and_window_alive(skeleton_window, qtbot, mc_dir):
    from UI import base_mode_window
    skeleton_window.show()
    skeleton_window.save_selected_text("Helix")
    skeleton_window.user_minecraft_save = mc_dir
    from UI.session import SESSION
    SESSION.save_path = mc_dir
    skeleton_window.sidebar.SkeletonMode.click()
    assert skeleton_window.isVisible()             # re-selecting the current mode is a no-op
    skeleton_window.sidebar.RibbonMode.click()
    ribbon = base_mode_window._open_windows["Ribbon"]
    qtbot.addWidget(ribbon)
    assert ribbon.isVisible() and not skeleton_window.isVisible()
    assert ribbon.user_pdb_file == skeleton_window.user_pdb_file
    assert ribbon.user_minecraft_save == mc_dir
    assert ribbon.pScaleSpinBox.value() == skeleton_window.pScaleSpinBox.value()
    assert ribbon.selectedPDBLabel.toolTip().endswith("Helix.pdb")


def test_residue_mods_shared_and_dropped_with_new_file(skeleton_window, qtbot):
    skeleton_window.save_selected_text("Helix")
    skeleton_window.set_residue_mods({"A": {"3": ["hide"]}})
    assert "1 residue modified" in skeleton_window.selectedPDBLabel.toolTip()
    custom = make_window(qtbot, "Custom")
    assert custom.build_config()['residue_mods'] == {"A": {"3": ["hide"]}}
    custom.save_selected_text("GFP")
    assert custom.build_config()['residue_mods'] == {}


@pytest.mark.parametrize("mode", MODE_NAMES)
def test_worker_generates_model(qtbot, mode, mc_dir):
    from UI.base_mode_window import WorkerThread
    window = make_window(qtbot, mode)
    window.user_pdb_file = preset("Helix")
    window.user_minecraft_save = mc_dir
    worker = WorkerThread(mode, window.build_config())
    progress = []
    worker.progress.connect(progress.append)
    with qtbot.waitSignal(worker.result, timeout=120000) as blocker:
        worker.start()
    assert blocker.args[0] == {"result": "done", "lower": "helix"}
    worker.wait()
    assert progress == sorted(progress) and progress[-1] == 100
    for d in mcf.structure_dirs(mc_dir):
        assert any(f.startswith("helix_") for f in os.listdir(d))


def test_create_button_runs_build(skeleton_window, qtbot, mc_dir, quiet_popups):
    skeleton_window.user_pdb_file = preset("Helix")
    skeleton_window.user_minecraft_save = mc_dir
    skeleton_window.createFunctionsButton.click()
    assert not skeleton_window.createFunctionsButton.isEnabled()
    qtbot.waitUntil(lambda: skeleton_window.createFunctionsButton.isEnabled(), timeout=120000)
    assert quiet_popups[-1] == "Model generated"


def test_worker_reports_errors(mc_dir, qtbot, tmp_path):
    from UI.base_mode_window import WorkerThread
    worker = WorkerThread("Skeleton", {"pdb_file": str(tmp_path / "missing.pdb"), "save_path": mc_dir})
    with qtbot.waitSignal(worker.result, timeout=10000) as blocker:
        worker.start()
    worker.wait()
    assert blocker.args[0]["result"] == "error"


@pytest.mark.parametrize("mode", ["Skeleton", "Custom", "Space Filling", "Ribbon"])
def test_color_by_chain_asks_for_chain_colours(qtbot, mode, monkeypatch):
    from UI.base_mode_window import ModeWindow
    asked = []
    monkeypatch.setattr(ModeWindow, "edit_chain_colors", lambda self: asked.append(True))
    window = make_window(qtbot, mode)
    check = window.colorByChainCheck
    if check.isChecked():
        check.click()
    check.click()
    assert asked == [True]
    check.click()                      # unchecking does not ask
    assert asked == [True]


def test_chain_colour_list_reaches_config(skeleton_window, qtbot, monkeypatch):
    from UI import chain_colors
    def accept(dialog):
        dialog.entry.setText("Stone, diamond_block, not_a_block")
        dialog.add_from_entry()
        assert "not_a_block" in dialog.message.text()
        dialog.list.clear()
        dialog.entry.setText("stone, diamond block")
        dialog.add_from_entry()
        return QtWidgets.QDialog.DialogCode.Accepted
    monkeypatch.setattr(chain_colors.ChainColorDialog, "exec", accept)
    skeleton_window.colorByChainCheck.click()
    assert skeleton_window.build_config()['chain_blocks'] == ["stone", "diamond_block"]
    assert skeleton_window.build_config()['by_chain'] is True


def test_chain_colour_dialog_defaults_and_order(qtbot):
    from PDB2MC.build import DEFAULT_CHAIN_BLOCKS
    from UI.chain_colors import ChainColorDialog, parse_blocks
    dialog = ChainColorDialog(["red_wool", "blue_wool", "stone"])
    qtbot.addWidget(dialog)
    dialog.list.item(2).setSelected(True)
    dialog.move_selected(-1)
    assert dialog.blocks() == ["red_wool", "stone", "blue_wool"]
    dialog.reset_button.click()
    assert dialog.blocks() == DEFAULT_CHAIN_BLOCKS
    assert parse_blocks("minecraft:Red Wool; x") == (["red_wool"], ["x"])


def test_amino_acid_colour_style(qtbot):
    window = make_window(qtbot, "Amino Acids")
    window.colorStyleBox.setCurrentText("Hydrophobicity")
    assert window.build_config()['amino_acids'] == defaults.AMINO_ACID_STYLES["Hydrophobicity"]


def test_sequence_selector_modifications(qtbot):
    from UI.utilities import SequenceSelectorPopup
    structure = pdbm.load_structure(preset("Helix"))
    chain = next(iter(structure.sequences))
    resids = [str(r) for r, _ in structure.sequences[chain]]
    popup = SequenceSelectorPopup(structure, {chain: {resids[0]: ["block:stone"]}})
    qtbot.addWidget(popup)
    assert not hasattr(popup, "add_chain_btn") and popup.clear_btn.text() == "Clear Changes"

    widget = popup.chain_widgets[chain]
    for row in (1, 2):
        widget.item(row).setSelected(True)
    popup.assign_hide()
    with qtbot.waitSignal(popup.selection_made) as blocker:
        popup.finish_selection()
    assert blocker.args[0] == {chain: {resids[0]: ["block:stone"], resids[1]: ["hide"], resids[2]: ["hide"]}}

    popup = SequenceSelectorPopup(structure, blocker.args[0])
    qtbot.addWidget(popup)
    popup.chain_widgets[chain].item(1).setSelected(True)
    popup.clear_changes()                          # only the selected residue
    popup.chain_widgets[chain].clearSelection()
    with qtbot.waitSignal(popup.selection_made) as blocker:
        popup.finish_selection()
    assert blocker.args[0] == {chain: {resids[0]: ["block:stone"], resids[2]: ["hide"]}}
    popup.clear_changes()                          # nothing selected: everything
    with qtbot.waitSignal(popup.selection_made) as blocker:
        popup.finish_selection()
    assert blocker.args[0] == {}


def test_sidebar_signals_and_layout(qtbot):
    from UI.sidebar import Sidebar
    sidebar = Sidebar()
    qtbot.addWidget(sidebar)
    assert callable(sidebar.layout)                 # was shadowed by an attribute
    with qtbot.waitSignal(sidebar.mode_selected) as blocker:
        sidebar.SpaceFillingMode.click()
    assert blocker.args == ["Space Filling"]        # full name even when the button text is elided
    with qtbot.waitSignal(sidebar.tools_requested):
        sidebar.tools.click()


def test_tool_window_uses_sidebar(qtbot):
    from UI import base_mode_window
    tools = make_window(qtbot, "Tools")
    tools.show()
    tools.sidebar.CustomMode.click()
    custom = base_mode_window._open_windows["Custom"]
    qtbot.addWidget(custom)
    assert custom.isVisible() and not tools.isVisible()


def test_update_check_runs_in_background(qtbot, monkeypatch):
    from PDB2MC import run_PDB2MC
    monkeypatch.setattr(run_PDB2MC, "latest_release", lambda: "v999.0")
    check = run_PDB2MC.UpdateCheck()
    with qtbot.waitSignal(check.newer_version, timeout=5000) as blocker:
        check.start()
    check.wait()
    assert blocker.args == ["999.0"]
    assert not run_PDB2MC.is_newer("0.0.1")
    assert not run_PDB2MC.is_newer("not a version")
