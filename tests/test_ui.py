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


# --- tool tips ---

def option_rows(window):
    from UI import base_mode_window as base
    for column in window.OPTION_COLUMNS:
        for row in column:
            if not isinstance(row, base.Gap):
                yield row


SHARED_CONTROLS = ("modelNameEdit", "modelNameLabel", "selectPDBFileButton", "selectIncludedPDBButton",
                   "selectMinecraftSaveButton", "simpleOutputCheck", "modifyResiduesButton", "createFunctionsButton",
                   "selectedPDBLabel", "selectedMinecraftLabel")


@pytest.mark.parametrize("mode", MODE_NAMES)
def test_every_option_has_a_tool_tip(qtbot, mode):
    from UI import base_mode_window as base
    window = make_window(qtbot, mode)
    rows = list(option_rows(window))
    assert rows
    for row in rows:
        assert getattr(window, row.name).toolTip().strip(), row.name
        if not isinstance(row, base.Check):
            assert getattr(window, row.name + "Label").toolTip().strip(), row.name
    for name in SHARED_CONTROLS:
        assert getattr(window, name).toolTip().strip(), name


def test_sidebar_tool_tips_are_descriptions(qtbot):
    from UI.sidebar import Sidebar
    sidebar = Sidebar()
    qtbot.addWidget(sidebar)
    for button in sidebar._buttons:
        assert len(button.toolTip()) > len(sidebar._button_texts[button]), button.text()


def test_other_windows_have_tool_tips(qtbot):
    from UI.chain_colors import ChainColorDialog
    from UI.settings_dialogs import DefaultFolderDialog, MetalIonDialog
    tools = make_window(qtbot, "Tools")
    from UI.tool_window import TOOL_BUTTONS
    for name, _ in TOOL_BUTTONS:
        assert getattr(tools, name).toolTip().strip(), name
    chain = ChainColorDialog()
    metal = MetalIonDialog()
    folder = DefaultFolderDialog()
    for dialog in (chain, metal, folder):
        qtbot.addWidget(dialog)
    for widget in (chain.list, chain.entry, chain.add_button, chain.up_button, chain.down_button,
                   chain.remove_button, chain.reset_button, metal.reset_button, folder.path,
                   folder.browse_button, folder.clear_button, *metal.boxes.values()):
        assert widget.toolTip().strip()


def test_all_tool_tip_text_is_in_one_file():
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sources = [os.path.join(root, "PDB2MC", "run_PDB2MC.py")]
    for folder, _, files in os.walk(os.path.join(root, "UI")):
        sources += [os.path.join(folder, f) for f in files if f.endswith(".py") and f != "tooltips.py"]
    for path in sources:
        with open(path, encoding="utf-8") as f:
            for number, line in enumerate(f, start=1):
                assert 'setToolTip("' not in line and "setToolTip(f\"" not in line, f"{path}:{number}"


def test_tool_tips_wrap():
    from UI import tooltips
    for text in tooltips.OPTIONS.values():
        assert all(len(line) <= tooltips.WRAP_WIDTH for line in tooltips.wrapped(text).splitlines())


def test_mode_specific_tool_tips(qtbot):
    assert "residue" in make_window(qtbot, "Amino Acids").aScaleSpinBox.toolTip()
    assert "surface" in make_window(qtbot, "Space Filling").colorByChainCheck.toolTip()
    assert "Alanine" in make_window(qtbot, "Amino Acids").AlaColorBox.toolTip()


# --- SASA radius ---

def test_sasa_radius_reaches_the_build(qtbot):
    window = make_window(qtbot, "Space Filling")
    assert window.sasaRadiusSpinBox.value() == 1.4
    window.sasaRadiusSpinBox.setValue(2.25)
    assert window.build_config()['sasa_radius'] == 2.25
    assert window.sasaRadiusSpinBox.minimum() == 0.0


def test_only_space_filling_has_a_sasa_radius(qtbot):
    assert not hasattr(make_window(qtbot, "Skeleton"), "sasaRadiusSpinBox")


# --- metal ion settings ---

@pytest.mark.parametrize("mode", MODE_NAMES)
def test_metal_settings_reach_every_mode(qtbot, mode):
    from PDB2MC import user_settings
    user_settings.set_metal_blocks({**defaults.default_metal_blocks(), "ZN": "gold_block"})
    assert make_window(qtbot, mode).build_config()['atoms']['ZN'] == "gold_block"


def test_metal_dialog_saves_for_next_time(qtbot):
    from PDB2MC import user_settings
    from UI.settings_dialogs import MetalIonDialog
    dialog = MetalIonDialog()
    qtbot.addWidget(dialog)
    assert set(dialog.boxes) == set(defaults.METAL_IONS)
    dialog.boxes["ZN"].setCurrentText("Gold Block")
    dialog.accept()
    assert user_settings.metal_blocks()["ZN"] == "gold_block"

    again = MetalIonDialog()
    qtbot.addWidget(again)
    assert again.boxes["ZN"].currentText() == "gold_block"
    again.reset_button.click()
    again.accept()
    assert user_settings.metal_blocks() == defaults.default_metal_blocks()
    assert user_settings.load()["metal_blocks"] == {}


def test_metal_dialog_swatches_show_each_block(qtbot):
    from UI.settings_dialogs import MetalIonDialog, select_block
    dialog = MetalIonDialog()
    qtbot.addWidget(dialog)
    assert dialog.boxes["ZN"].currentIndex() != dialog.boxes["FE"].currentIndex()
    select_block(dialog.boxes["ZN"], "gold_block")
    assert dialog.boxes["ZN"].currentIndex() == dialog.boxes["ZN"].findText("gold_block")


def test_metal_dialog_refuses_unknown_blocks(qtbot):
    from PDB2MC import user_settings
    from UI.settings_dialogs import MetalIonDialog
    dialog = MetalIonDialog()
    qtbot.addWidget(dialog)
    dialog.boxes["ZN"].setCurrentText("not_a_block")
    dialog.accept()
    assert "not_a_block" in dialog.message.text()
    assert user_settings.metal_blocks()["ZN"] == defaults.default_metal_blocks()["ZN"]


def test_metal_dialog_cancel_changes_nothing(qtbot):
    from PDB2MC import user_settings
    from UI.settings_dialogs import MetalIonDialog
    dialog = MetalIonDialog()
    qtbot.addWidget(dialog)
    dialog.boxes["ZN"].setCurrentText("gold_block")
    dialog.reject()
    assert user_settings.metal_blocks()["ZN"] == defaults.default_metal_blocks()["ZN"]


def test_tools_opens_the_settings_windows(qtbot, monkeypatch):
    from UI import settings_dialogs
    opened = []
    monkeypatch.setattr(settings_dialogs.MetalIonDialog, "exec", lambda self: opened.append("metal"))
    monkeypatch.setattr(settings_dialogs.DefaultFolderDialog, "exec", lambda self: opened.append("folder"))
    tools = make_window(qtbot, "Tools")
    tools.metalIonSettings.click()
    tools.defaultFolder.click()
    assert opened == ["metal", "folder"]


# --- default structure folder ---

def test_folder_dialog_saves_for_next_time(qtbot, tmp_path):
    from PDB2MC import user_settings
    from UI.settings_dialogs import DefaultFolderDialog
    dialog = DefaultFolderDialog()
    qtbot.addWidget(dialog)
    dialog.path.setText(str(tmp_path))
    dialog.accept()
    assert user_settings.structure_dir() == str(tmp_path)
    again = DefaultFolderDialog()
    qtbot.addWidget(again)
    assert again.path.text() == str(tmp_path)
    again.clear_button.click()
    again.accept()
    assert user_settings.structure_dir() == ""


def test_folder_dialog_refuses_missing_folder(qtbot, tmp_path):
    from PDB2MC import user_settings
    from UI.settings_dialogs import DefaultFolderDialog
    dialog = DefaultFolderDialog()
    qtbot.addWidget(dialog)
    dialog.path.setText(str(tmp_path / "missing"))
    dialog.accept()
    assert dialog.message.text() and user_settings.saved_structure_dir() == ""


def test_file_dialog_starts_in_the_default_folder(qtbot, tmp_path, monkeypatch):
    from PDB2MC import user_settings
    from UI import utilities
    user_settings.set_structure_dir(str(tmp_path))
    started = []
    def fake_dialog(parent, title, folder, filters):
        started.append(folder)
        return preset("Helix"), ""
    monkeypatch.setattr(utilities.QFileDialog, "getOpenFileName", staticmethod(fake_dialog))
    popup = utilities.FileExplorerPopup()
    qtbot.addWidget(popup)
    assert started == [str(tmp_path)] and popup.selected_file == preset("Helix")


# --- model names ---

def test_included_model_keeps_the_example_name(skeleton_window):
    skeleton_window.save_selected_text("Hemoglobin")
    assert skeleton_window.modelNameEdit.text() == "hemoglobin"    # Helix.pdb has the same PDB ID, 3BJ1


def test_selected_file_fills_in_its_pdb_id(skeleton_window, tmp_path):
    from shutil import copyfile
    path = tmp_path / "my download (3).pdb"
    copyfile(preset("Helix"), path)
    skeleton_window.set_pdb_file(str(path), announce=False)
    assert skeleton_window.modelNameEdit.text() == "3bj1"


def test_mmcif_fills_in_its_entry_id(skeleton_window, tmp_path):
    path = tmp_path / "file.cif"
    path.write_text(MMCIF_FILE)
    skeleton_window.set_pdb_file(str(path), announce=False)
    assert skeleton_window.modelNameEdit.text() == "9xyz"


MMCIF_FILE = """data_9XYZ
_entry.id 9XYZ
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
ATOM 1 N N . ALA A 1 1 0.0 0.0 0.0 1 ALA A N
ATOM 2 C CA . ALA A 1 1 1.4 0.0 0.0 1 ALA A CA
"""


def test_file_without_a_header_uses_its_file_name(skeleton_window, tmp_path):
    path = tmp_path / "my_protein.pdb"
    from conftest import pdb_line
    path.write_text(pdb_line("ATOM", 1, "CA", "ALA", "A", 1, 0, 0, 0, "C"))
    skeleton_window.set_pdb_file(str(path), announce=False)
    assert skeleton_window.modelNameEdit.text() == "my-protein"


def test_custom_name_reaches_the_build_and_other_modes(skeleton_window, qtbot):
    skeleton_window.save_selected_text("Helix")
    skeleton_window.modelNameEdit.setText("My Model")
    skeleton_window.modelNameEdit.textEdited.emit("My Model")
    skeleton_window.tidy_model_name()
    assert skeleton_window.modelNameEdit.text() == "my-model"
    assert skeleton_window.build_config()['model_name'] == "my-model"
    assert make_window(qtbot, "Ribbon").modelNameEdit.text() == "my-model"


def test_new_structure_replaces_the_custom_name(skeleton_window):
    skeleton_window.save_selected_text("Helix")
    skeleton_window.modelNameEdit.textEdited.emit("mine")
    skeleton_window.save_selected_text("GFP")
    assert skeleton_window.modelNameEdit.text() == "gfp"


def test_emptied_name_goes_back_to_the_structures_name(skeleton_window):
    skeleton_window.save_selected_text("Helix")
    skeleton_window.modelNameEdit.setText("   ")
    skeleton_window.tidy_model_name()
    assert skeleton_window.modelNameEdit.text() == "helix"


def test_create_button_uses_the_custom_name(skeleton_window, qtbot, mc_dir, quiet_popups):
    from PDB2MC import triggers
    skeleton_window.save_selected_text("Helix")
    skeleton_window.modelNameEdit.setText("custom-helix")
    skeleton_window.user_minecraft_save = mc_dir
    skeleton_window.createFunctionsButton.click()
    qtbot.waitUntil(lambda: skeleton_window.createFunctionsButton.isEnabled(), timeout=120000)
    assert quiet_popups[-1] == "Model generated"
    assert "/trigger build set 1" in skeleton_window.info_box.label1.text()
    assert "/trigger build_custom-helix" in skeleton_window.info_box.label1.text()
    assert triggers.model_number(mc_dir, "custom-helix") == 1


def test_finished_message_fits_in_its_box(qtbot):
    from PDB2MC import triggers
    from UI.utilities import InformationBox
    box = InformationBox()
    qtbot.addWidget(box)
    box.set_text("Finished!\n" + triggers.instructions("a-rather-long-model-name", 12))
    label = box.label1.geometry()
    assert label.left() >= 112 and label.right() <= box.width() and label.bottom() < box.okayButton.y()


# --- progress window ---

def test_progress_dialog_shows_status_and_fills(qtbot):
    from UI.base_mode_window import PleaseWaitDialog
    dialog = PleaseWaitDialog()
    qtbot.addWidget(dialog)
    dialog.set_status("Drawing the backbone...")
    dialog.set_progress(40)
    assert dialog.status_label.text() == "Drawing the backbone..."
    assert dialog.progress_bar.value() == 40 and dialog.volume.target == 0.4
    dialog.close()
    assert not dialog.volume._timer.isActive()


def test_worker_sends_status_and_model(qtbot, mc_dir):
    from UI.base_mode_window import WorkerThread
    window = make_window(qtbot, "Skeleton")
    window.user_pdb_file = preset("Helix")
    window.user_minecraft_save = mc_dir
    worker = WorkerThread("Skeleton", window.build_config())
    messages, models = [], []
    worker.status.connect(messages.append)
    worker.model_ready.connect(lambda positions, colours: models.append((positions, colours)))
    with qtbot.waitSignal(worker.result, timeout=60000):
        worker.start()
    worker.wait()
    qtbot.waitUntil(lambda: models and messages and messages[-1] == "Done!")
    assert len(models[0][0]) > 10 and "Reading structure file..." in messages


def test_animation_failure_does_not_stop_the_build(qtbot, mc_dir, monkeypatch):
    from UI import base_mode_window
    def boom(*args):
        raise ValueError("no animation today")
    monkeypatch.setattr(base_mode_window, "model_voxels", boom)
    window = make_window(qtbot, "Skeleton")
    window.user_pdb_file = preset("Helix")
    window.user_minecraft_save = mc_dir
    worker = base_mode_window.WorkerThread("Skeleton", window.build_config())
    with qtbot.waitSignal(worker.result, timeout=60000) as blocker:
        worker.start()
    worker.wait()
    assert blocker.args[0]["result"] == "done"


@pytest.mark.parametrize("structure", ["Helix", "Nucleosome"])
def test_model_fits_the_volume(structure):
    from UI import voxel_view
    positions, colours = voxel_view.model_voxels(pdbm.load_structure(preset(structure)))
    assert len(positions) == len(colours) > 0
    assert positions.min() >= 0 and positions.max() == voxel_view.GRID - 1
    assert len({tuple(p) for p in positions.tolist()}) == len(positions)     # one entry per voxel
    assert positions[:, 1].min() == 0                                        # stands on the floor


def test_water_stays_out_of_the_volume(write_pdb):
    from conftest import pdb_line
    from UI import voxel_view
    pdb = pdb_line("ATOM", 1, "CA", "ALA", "A", 1, 0, 0, 0, "C") + pdb_line("HETATM", 2, "O", "HOH", "A", 2, 90, 0, 0, "O")
    positions, _ = voxel_view.model_voxels(pdbm.load_structure(write_pdb(pdb)))
    assert len(positions) == 1


def test_voxel_colours_follow_the_settings():
    from UI import voxel_view
    structure = pdbm.load_structure(preset("ALA"))
    config = defaults.default_config("Custom")
    atom = voxel_view.model_voxels(structure, config)[1]
    chains = voxel_view.model_voxels(structure, {**config, 'by_chain': True})[1]
    assert len(set(map(tuple, atom.tolist()))) > 1
    assert len(set(map(tuple, chains.tolist()))) == 1


def test_empty_structure_has_no_voxels():
    from PDB2MC.structure_data import StructureData
    from UI import voxel_view
    positions, colours = voxel_view.model_voxels(StructureData())
    assert len(positions) == len(colours) == 0


def test_model_fills_from_the_bottom_up():
    import numpy as np
    from UI import voxel_view
    positions = np.array([(x, y, 15) for x in range(16) for y in range(32)])
    colours = np.full((len(positions), 3), 200, dtype=np.uint8)
    drawn = [np.count_nonzero(voxel_view.render(positions, colours, 30, level, 200, 200))
             for level in (-1, 4, 16, 31)]
    assert drawn[0] == 0 and drawn[0] < drawn[1] < drawn[2] < drawn[3]
    rows = np.nonzero(voxel_view.render(positions, colours, 30, 4, 200, 200))[0]
    assert rows.min() > 100                                                  # only the lower part so far


def test_volume_spins_and_catches_up_with_the_progress(qtbot):
    import numpy as np
    from UI import voxel_view
    volume = voxel_view.VoxelVolume()
    qtbot.addWidget(volume)
    volume._timer.stop()
    volume.set_model(np.array([[5, y, 5] for y in range(30)]), np.full((30, 3), 200, dtype=np.uint8))
    volume.set_progress(50)
    start = volume.angle
    qtbot.wait(40)
    volume.advance()
    assert volume.angle != start and 0 < volume.shown < 0.5
    volume.shown = volume.target = 1.0
    assert volume.level() == 29
    assert not volume.grab().isNull()


def test_view_of_the_volume_is_a_rotation():
    import numpy as np
    from UI import voxel_view
    view = voxel_view.rotation(33)
    assert np.allclose(view @ view.T, np.eye(3))


def test_every_angle_draws_a_cube():
    from UI import voxel_view
    view_counts = [len(voxel_view.cube_stamp(voxel_view.rotation(angle), 6)[0]) for angle in range(0, 360, 15)]
    assert min(view_counts) > 20


# --- removing files ---

def test_remove_function_files_updates_the_in_game_list(qtbot, mc_dir, monkeypatch, skeleton_config):
    from PDB2MC import build, triggers
    from UI import tool_window
    skeleton_config.update(pdb_file=preset("Helix"), save_path=mc_dir, triggers=True)
    build.build_model("Skeleton", skeleton_config)
    assert triggers.model_number(mc_dir, "helix") == 1

    class Picked:
        selected_directory = mc_dir
    monkeypatch.setattr(tool_window, "MinecraftPopup", Picked)
    make_window(qtbot, "Tools").removeFunctionFiles.click()
    assert triggers.models(mc_dir) == {}
