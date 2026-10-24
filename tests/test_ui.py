import os

import pytest

pytest.importorskip("pytestqt")

from PyQt6 import QtCore
from PyQt6.QtCore import QRect

from PDB2MC import minecraft_functions as mcf
from conftest import preset


@pytest.fixture
def skeleton_window(qtbot):
    from UI.skeleton_window import SkeletonWindow
    window = SkeletonWindow()
    qtbot.addWidget(window)
    return window


def test_main_window_opens_skeleton_mode(qtbot, monkeypatch):
    from PDB2MC import run_PDB2MC
    monkeypatch.setattr(run_PDB2MC.MainWindow, "is_outdated", lambda self: None)
    window = run_PDB2MC.MainWindow()
    qtbot.addWidget(window)
    window.handle_dropdown_change("Skeleton")   # raised NameError (ENABLE_HOT_RELOAD) before
    assert window.skeleton_window.isVisible()
    qtbot.addWidget(window.skeleton_window)


def test_skeleton_defaults(skeleton_window):
    w = skeleton_window
    assert w.backboneColorBox.currentText() == "gray_concrete"
    assert w.sidechainColorBox.currentText() == "gray_concrete"
    assert w.otherColorBox.currentText() == "pink_concrete"
    for box in (w.backboneColorBox, w.sidechainColorBox, w.otherColorBox):
        assert sum(box.itemText(i) == "" for i in range(box.count())) == 4   # separators in every box
    assert w.pScaleSpinBox.value() == 1.0 and w.aScaleSpinBox.value() == 1.5


def test_skeleton_widgets_do_not_overlap():
    from UI.skeleton_window import UI_GEOMETRY
    rects = {k: QRect(*v) for k, v in UI_GEOMETRY.items() if k != "bg"}
    overlaps = [(a, b) for a in rects for b in rects if a < b and rects[a].intersects(rects[b])]
    assert overlaps == []
    from UI.sidebar import SIDEBAR_WIDTH
    assert all(r.left() >= SIDEBAR_WIDTH and r.right() < 450 and r.bottom() < 450 for r in rects.values())


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


def test_preset_selection_uses_absolute_path(skeleton_window):
    skeleton_window.save_selected_text("GFP")
    assert os.path.isabs(skeleton_window.user_pdb_file) and os.path.exists(skeleton_window.user_pdb_file)
    assert skeleton_window.selectedPDBLabel.toolTip().endswith("GFP.pdb")


def test_worker_generates_model(skeleton_window, mc_dir, qtbot):
    from UI.skeleton_window import WorkerThread
    w = skeleton_window
    w.user_pdb_file = preset("Helix")
    w.user_minecraft_save = mc_dir
    worker = WorkerThread(w.build_config())
    progress = []
    worker.progress.connect(progress.append)
    with qtbot.waitSignal(worker.result, timeout=120000) as blocker:
        worker.start()
    assert blocker.args[0] == {"result": "done", "lower": "helix"}
    worker.wait()
    assert progress == sorted(progress) and progress[-1] == 100
    for d in mcf.structure_dirs(mc_dir):
        assert any(f.startswith("helix_backbone") for f in os.listdir(d))


def test_worker_reports_errors(mc_dir, qtbot, tmp_path):
    from UI.skeleton_window import WorkerThread
    worker = WorkerThread({"pdb_file": str(tmp_path / "missing.pdb"), "save_path": mc_dir})
    with qtbot.waitSignal(worker.result, timeout=10000) as blocker:
        worker.start()
    worker.wait()
    assert blocker.args[0]["result"] == "error"


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


def test_sidebar_switches_mode_and_keeps_window_alive(skeleton_window, qtbot):
    from UI import base_mode_window
    skeleton_window.show()
    skeleton_window.sidebar.SkeletonMode.click()
    assert skeleton_window.isVisible()             # re-selecting the current mode is a no-op
    skeleton_window.sidebar.RibbonMode.click()
    ribbon = base_mode_window._open_windows["Ribbon"]
    qtbot.addWidget(ribbon)
    assert ribbon.isVisible() and not skeleton_window.isVisible()


def test_base_mode_window_constructs(qtbot):
    from UI.base_mode_window import BaseModeWindow
    window = BaseModeWindow()
    qtbot.addWidget(window)
    assert window.sidebar.width() > 0
    assert os.path.exists(window.icon("logo.png"))
