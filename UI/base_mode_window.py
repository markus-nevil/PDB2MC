"""
Mode windows: the shared ModeWindow base class, its worker thread, and switching between modes.

A mode window lists its options as columns of rows (see Color, Check, Spin, Choice, Gap); ModeWindow lays
them out next to the sidebar, adds the shared model / save selection, Modify Residues and Create
buttons, and runs the build for its MODE_NAME through PDB2MC.build.build_model.
"""
import math
import os
import traceback
from dataclasses import dataclass, field

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QDesktopServices, QIcon, QPainter, QPixmap

from PDB2MC import build, minecraft_functions as mcf, pdb_manipulation as pdbm, resources
from PDB2MC.variables import decorative_blocks, hex_dict
from .chain_colors import ChainColorDialog
from .session import SESSION
from .sidebar import Sidebar, SIDEBAR_WIDTH
from .utilities import (FileExplorerPopup, IncludedPDBPopup, InformationBox, MinecraftPopup, MyComboBox,
                        SequenceSelectorPopup, get_presets_path)

GITHUB_URL = "https://github.com/markus-nevil/PDB2MC"
RCSB_URL = "https://www.rcsb.org/"

# Height (blocks) a model may occupy; used for the size check and the automatic protein scale
WORLD_MAX = 320

# Colour choices in each dropdown, in display order; separators go between the five groups
_COLORS = ("red", "orange", "yellow", "lime", "green", "cyan", "light_blue", "blue",
           "purple", "magenta", "pink", "brown", "black", "gray", "light_gray", "white")
COLOR_CHOICES = ([f"{color}_{material}" for material in ("concrete", "glazed_terracotta", "terracotta", "wool")
                  for color in _COLORS]
                 + [f"{color}_stained_glass" for color in _COLORS])
COLOR_GROUP_SIZE = len(_COLORS)

# Layout (pixels)
MARGIN = 10
LABEL_WIDTH = 135
FIELD_WIDTH = 185
COLUMN_WIDTH = LABEL_WIDTH + FIELD_WIDTH
COLUMN_GAP = 20
ROW_HEIGHT = 22
CHECK_HEIGHT = 18
ROW_SPACING = 6
BOTTOM_HEIGHT = 148
# Every mode window is at least this tall, so switching modes doesn't resize the window
MIN_HEIGHT = 432

# Windows opened through open_mode_window. Holding a reference keeps a window alive after the
# window that opened it is hidden; without one, PyQt garbage-collects it and it vanishes immediately.
_open_windows = {}


# --- option rows ---

@dataclass
class Color:
    """Label and block dropdown."""
    name: str
    label: str
    default: str
    tooltip: str = ""


@dataclass
class Check:
    """Checkbox under the dropdown column."""
    name: str
    text: str
    default: bool
    tooltip: str = ""


@dataclass
class Spin:
    """Label and number box (1.0-50.0)."""
    name: str
    label: str
    default: float
    tooltip: str = ""


@dataclass
class Choice:
    """Label and a plain dropdown of fixed choices."""
    name: str
    label: str
    items: list = field(default_factory=list)
    default: str = ""
    tooltip: str = ""


@dataclass
class Gap:
    height: int = 10


def create_icon(hex_color: str, size: int = 100) -> QIcon:
    pixmap = QPixmap(size, size)
    painter = QPainter(pixmap)
    painter.setBrush(QColor(hex_color))
    painter.drawRect(0, 0, size, size)
    painter.end()
    return QIcon(pixmap)


def set_combobox_by_text(combobox, text):
    """Select text in combobox, adding it (with its colour) when it is a block not in the list."""
    index = combobox.findText(text)
    if index < 0 and text in decorative_blocks:
        combobox.addItem(create_icon(hex_dict.get(text, "#ff00ff")), text)
        index = combobox.findText(text)
    if index >= 0:
        combobox.setCurrentIndex(index)


def icon_path(name):
    return resources.image('icons', name)


# --- worker ---

class WorkerThread(QThread):
    # Named `result` so it does not shadow QThread's own `finished` signal
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

    def __init__(self, mode, config_data, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.config_data = config_data

    def run(self):
        try:
            name = build.build_model(self.mode, self.config_data, progress=self.progress.emit)
            self.result.emit({"result": "done", "lower": name})
        except Exception as e:
            traceback.print_exc()
            self.result.emit({"result": "error", "error": f"{type(e).__name__}: {e}"})


class PleaseWaitDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Please wait")
        layout = QtWidgets.QVBoxLayout()
        self.status_label = QtWidgets.QLabel("Processing, please wait...")
        layout.addWidget(self.status_label)
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        self.setModal(True)

    def set_progress(self, value):
        self.progress_bar.setValue(value)
        if value < 10:
            self.status_label.setText("Reading structure file...")
        elif value < 85:
            self.status_label.setText("Building model...")
        elif value < 100:
            self.status_label.setText("Writing Minecraft functions...")
        else:
            self.status_label.setText("Done!")


# --- switching modes ---

def create_mode_window(mode_name):
    """Instantiate the window for a sidebar mode name, or None for an unknown name."""
    if mode_name == "Custom":
        from .custom_window import CustomWindow
        return CustomWindow()
    if mode_name == "Skeleton":
        from .skeleton_window import SkeletonWindow
        return SkeletonWindow()
    if mode_name == "X-Ray":
        from .xray_window import XrayWindow
        return XrayWindow()
    if mode_name == "Space Filling":
        from .space_filling_window import SpaceFillingWindow
        return SpaceFillingWindow()
    if mode_name == "Amino Acids":
        from .amino_acids_window import AminoAcidsWindow
        return AminoAcidsWindow()
    if mode_name == "Ribbon":
        from .ribbon_window import RibbonWindow
        return RibbonWindow()
    if mode_name == "Tools":
        from .tool_window import ToolWindow
        return ToolWindow()
    return None


def open_mode_window(mode_name, current=None):
    """Show the window for mode_name and hide `current`. Re-selecting the current mode does nothing."""
    if current is not None and getattr(current, "MODE_NAME", None) == mode_name:
        return current
    window = create_mode_window(mode_name)
    if window is None:
        return None
    _open_windows[mode_name] = window
    if current is not None:
        window.move(current.pos())
    window.show()
    if current is not None:
        current.hide()
    return window


def open_help(parent=None):
    from .help_window import HelpWindow
    help_window = HelpWindow.instance()
    help_window.show()
    help_window.raise_()
    help_window.activateWindow()
    if parent is not None and parent.screen() is not None:
        # centre on the screen of the window that asked for help
        frame_geometry = help_window.frameGeometry()
        frame_geometry.moveCenter(parent.screen().availableGeometry().center())
        help_window.move(frame_geometry.topLeft())
    return help_window


def show_information_box(owner, title_text, text, icon_path):
    """Show an InformationBox, keeping a reference on `owner` so it is not garbage-collected."""
    box = InformationBox()
    box.set_text(text)
    box.set_title(title_text)
    box.set_icon(icon_path)
    box.show()
    owner.info_box = box
    return box


def connect_sidebar(window, sidebar):
    """Wire a Sidebar's signals to the standard actions for `window`."""
    sidebar.mode_selected.connect(lambda mode: open_mode_window(mode, window))
    sidebar.tools_requested.connect(lambda: open_mode_window("Tools", window))
    sidebar.help_requested.connect(lambda: open_help(window))
    sidebar.github_requested.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
    sidebar.rcsb_requested.connect(lambda: QDesktopServices.openUrl(QUrl(RCSB_URL)))


def suggested_scale(path):
    """(fits, maximum scale) for a structure file; the automatic scale is the maximum rounded down."""
    if not pdbm.check_model_size(path, world_max=WORLD_MAX):
        return False, None
    return True, pdbm.check_max_size(path, world_max=WORLD_MAX)


# --- base window ---

class ModeWindow(QtWidgets.QMainWindow):
    """
    Base of every mode window. Subclasses set MODE_NAME and TITLE, list OPTION_COLUMNS and implement
    mode_config() (and optionally connect_options()) for their own settings.
    """
    MODE_NAME = None
    TITLE = "PDB2MC"
    OPTION_COLUMNS = []
    # Name of the "colour by chain" checkbox, if the mode has one
    CHAIN_CHECK = None

    def __init__(self):
        super().__init__()
        self.worker = None
        self.wait_dialog = None
        self.user_pdb_file = None
        self.user_minecraft_save = None
        self.setWindowTitle(self.TITLE)
        self.setWindowIcon(QIcon(icon_path('logo.png')))
        self.centralwidget = QtWidgets.QWidget(parent=self)
        self.setCentralWidget(self.centralwidget)
        self.bg = QtWidgets.QLabel(parent=self.centralwidget)
        self.bg.setPixmap(QtGui.QPixmap(resources.image("MC2PDB bg.png")))
        self.bg.setScaledContents(True)

        self.geometry_map = {}
        width, height = self._build_options()
        height = max(height + BOTTOM_HEIGHT + MARGIN, MIN_HEIGHT)
        self._build_bottom(height - BOTTOM_HEIGHT - MARGIN)
        width = max(width, SIDEBAR_WIDTH + MARGIN + COLUMN_WIDTH + MARGIN)
        self.resize(width, height)
        self.bg.setGeometry(0, 0, width, height)
        self.bg.lower()

        self.sidebar = Sidebar(self.centralwidget, width=SIDEBAR_WIDTH)
        self.sidebar.setGeometry(0, 0, SIDEBAR_WIDTH, height)
        self.sidebar.setFixedHeight(height)
        self.sidebar.raise_()
        connect_sidebar(self, self.sidebar)
        self.setFixedSize(width, height)

        for column in self.OPTION_COLUMNS:
            for row in column:
                if isinstance(row, Check):
                    getattr(self, row.name).stateChanged.connect(self.refresh_enabled)
        self.connect_options()
        self.refresh_enabled()
        if self.CHAIN_CHECK:
            getattr(self, self.CHAIN_CHECK).clicked.connect(self.on_chain_check_clicked)
        self.restore_session()

    # --- layout ---
    def _build_options(self):
        """Create the option widgets column by column; returns the (width, height) they need."""
        left = SIDEBAR_WIDTH + MARGIN
        bottom = MARGIN
        for column in self.OPTION_COLUMNS:
            y = MARGIN
            for row in column:
                y = self._add_row(row, left, y)
            bottom = max(bottom, y)
            left += COLUMN_WIDTH + COLUMN_GAP
        return left - COLUMN_GAP + MARGIN, bottom

    def _place(self, name, widget, x, y, w, h):
        widget.setObjectName(name)
        widget.setGeometry(QtCore.QRect(x, y, w, h))
        self.geometry_map[name] = (x, y, w, h)
        setattr(self, name, widget)

    def _add_row(self, row, x, y):
        field_x = x + LABEL_WIDTH
        if isinstance(row, Gap):
            return y + row.height
        if isinstance(row, Check):
            check = QtWidgets.QCheckBox(row.text, parent=self.centralwidget)
            check.setChecked(row.default)
            check.setToolTip(row.tooltip)
            self._place(row.name, check, field_x, y, FIELD_WIDTH, CHECK_HEIGHT)
            return y + CHECK_HEIGHT + 2
        label = QtWidgets.QLabel(row.label, parent=self.centralwidget)
        self._place(row.name + "Label", label, x, y, LABEL_WIDTH, ROW_HEIGHT)
        if isinstance(row, Color):
            widget = self.make_color_box(row.default)
            widget.setToolTip(row.tooltip)
            self._place(row.name, widget, field_x, y, FIELD_WIDTH, ROW_HEIGHT)
        elif isinstance(row, Spin):
            widget = make_spin(self.centralwidget, row.default, row.tooltip)
            self._place(row.name, widget, field_x, y, 62, ROW_HEIGHT)
        elif isinstance(row, Choice):
            widget = QtWidgets.QComboBox(parent=self.centralwidget)
            widget.addItems(row.items)
            widget.setCurrentText(row.default or row.items[0])
            widget.setToolTip(row.tooltip)
            self._place(row.name, widget, field_x, y, FIELD_WIDTH, ROW_HEIGHT)
        else:
            raise TypeError(f"Unknown option row: {row!r}")
        return y + ROW_HEIGHT + ROW_SPACING

    def _build_bottom(self, top):
        x = SIDEBAR_WIDTH + MARGIN

        def button(name, text, rect, point=None, bold=False, tooltip=""):
            widget = QtWidgets.QPushButton(text, parent=self.centralwidget)
            if point:
                font = QtGui.QFont()
                font.setPointSize(point)
                font.setBold(bold)
                widget.setFont(font)
            widget.setToolTip(tooltip)
            self._place(name, widget, x + rect[0], top + rect[1], rect[2], rect[3])
            return widget

        def small_label(name, text, rect):
            label = QtWidgets.QLabel(text, parent=self.centralwidget)
            font = QtGui.QFont()
            font.setPointSize(9)
            label.setFont(font)
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self._place(name, label, x + rect[0], top + rect[1], rect[2], rect[3])

        def path_label(name, rect):
            label = QtWidgets.QLabel(parent=self.centralwidget)
            font = QtGui.QFont()
            font.setPointSize(8)
            label.setFont(font)
            label.setStyleSheet("background-color: rgba(255, 255, 255, 140);")
            self._place(name, label, x + rect[0], top + rect[1], rect[2], rect[3])

        button("selectPDBFileButton", "Select PDB File", (0, 0, 101, 23))
        small_label("orText", "or", (101, 0, 25, 23))
        button("selectIncludedPDBButton", "Select Included PDB File", (126, 0, 189, 23))
        path_label("selectedPDBLabel", (0, 24, COLUMN_WIDTH, 18))
        small_label("andText", "and", (0, 46, 30, 23))
        button("selectMinecraftSaveButton", "Select Minecraft Save", (30, 46, 285, 23))
        path_label("selectedMinecraftLabel", (0, 70, COLUMN_WIDTH, 18))
        check = QtWidgets.QCheckBox("Simple output", parent=self.centralwidget)
        check.setChecked(True)
        check.setToolTip("Un-select to create individual commands for each molecule")
        self._place("simpleOutputCheck", check, x, top + 94, 110, 20)
        button("modifyResiduesButton", "Modify Residues", (0, 116, 110, 26), point=9,
               tooltip="Give residues their own block, or hide them")
        button("createFunctionsButton", "Create Minecraft\nFunctions", (120, 98, 195, 44), point=11, bold=True,
               tooltip="Add the selected PDB file to the Minecraft world")

        self.selectPDBFileButton.clicked.connect(self.handle_select_pdb_file_button)
        self.selectIncludedPDBButton.clicked.connect(self.handle_included_pdb_button)
        self.selectMinecraftSaveButton.clicked.connect(self.handle_select_minecraft_button)
        self.modifyResiduesButton.clicked.connect(self.handle_modify_residues_button)
        self.createFunctionsButton.clicked.connect(self.handle_make_function_button)

    def make_color_box(self, default):
        box = MyComboBox(self.centralwidget)
        box.setEditable(True)
        for value in COLOR_CHOICES:
            box.addItem(create_icon(hex_dict.get(value, "#ff00ff")), value)
        # separators between concrete / glazed terracotta / terracotta / wool / stained glass
        for index in range(4 * COLOR_GROUP_SIZE, 0, -COLOR_GROUP_SIZE):
            box.insertSeparator(index)
        set_combobox_by_text(box, default)
        completer = QtWidgets.QCompleter(decorative_blocks, box)
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        box.setCompleter(completer)
        box.focusOut.connect(lambda box=box: self.check_input(box, decorative_blocks))
        return box

    # --- hooks for subclasses ---
    def connect_options(self):
        """Connect option widgets to each other (enable/disable)."""

    def mode_config(self, config):
        """Add the mode's own settings to config."""

    def refresh_enabled(self, *_):
        """Enable / disable options that depend on checkboxes; called whenever one changes."""

    # --- shared state ---
    def restore_session(self):
        if SESSION.pdb_file and os.path.exists(SESSION.pdb_file):
            self.set_pdb_file(SESSION.pdb_file, announce=False)
        if SESSION.save_path:
            self.user_minecraft_save = SESSION.save_path
        self.update_selection_labels()

    @property
    def residue_mods(self):
        return SESSION.residue_mods

    @property
    def chain_blocks(self):
        return SESSION.chain_blocks or list(build.DEFAULT_CHAIN_BLOCKS)

    # --- option helpers ---
    def check_input(self, combobox, valid_options):
        text = combobox.currentText().lower().replace(' ', '_')
        if text not in valid_options:
            self.show_information_box(title_text="Invalid block input",
                                      text=f"{text} is not a valid block option.",
                                      icon_path=icon_path("icon_bad.png"))
            combobox.setCurrentIndex(0)
            return
        if combobox.findText(text) < 0:
            combobox.addItem(create_icon(hex_dict.get(text, "#ff00ff")), text)
        combobox.setCurrentIndex(combobox.findText(text))

    def on_chain_check_clicked(self, checked):
        if checked:
            self.edit_chain_colors()

    def edit_chain_colors(self):
        """Ask for the chain colour list; returns True when it was accepted."""
        dialog = ChainColorDialog(self.chain_blocks, parent=self)
        self.chain_dialog = dialog
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            SESSION.chain_blocks = dialog.blocks()
            return True
        return False

    def update_selection_labels(self):
        def show(label, path, empty_text):
            if path:
                text = os.path.normpath(path)
                metrics = QtGui.QFontMetrics(label.font())
                label.setText(metrics.elidedText(text, QtCore.Qt.TextElideMode.ElideMiddle, label.width() - 4))
                label.setToolTip(text)
            else:
                label.setText(empty_text)
                label.setToolTip("")
        pdb_text = self.user_pdb_file
        if pdb_text and self.residue_mods:
            count = sum(len(residues) for residues in self.residue_mods.values())
            pdb_text = f"{pdb_text}  ({count} residue{'s' if count != 1 else ''} modified)"
        show(self.selectedPDBLabel, pdb_text, "No PDB file selected.")
        save = mcf.world_dir(self.user_minecraft_save) if self.user_minecraft_save else None
        show(self.selectedMinecraftLabel, save, "No Minecraft save selected.")

    # --- file selection ---
    def handle_select_pdb_file_button(self):
        self.selectPDB = FileExplorerPopup()
        if self.selectPDB.selected_file:
            self.set_pdb_file(self.selectPDB.selected_file)

    def handle_included_pdb_button(self):
        self.includedPDB = IncludedPDBPopup()
        self.includedPDB.selected.connect(self.save_selected_text)
        self.includedPDB.show()

    def save_selected_text(self, text):
        self.set_pdb_file(os.path.join(get_presets_path(), f"{text}.pdb"))

    def set_pdb_file(self, path, announce=True):
        """
        Use the structure at path: shared with the other modes, and the protein scale is set to the
        largest whole number that fits in the world.
        """
        self.user_pdb_file = path
        SESSION.set_pdb_file(path)
        self.update_selection_labels()
        try:
            fits, maximum = suggested_scale(path)
        except Exception as e:
            if announce:
                self.show_information_box("Scale error", f"Could not determine recommended scale.\nError: {e}",
                                          icon_path("icon_bad.png"))
            return
        if not fits:
            if announce:
                self.show_information_box("Model too large!", "The chosen model is too large for Minecraft.",
                                          icon_path("icon_bad.png"))
            return
        if hasattr(self, "pScaleSpinBox"):
            self.pScaleSpinBox.setValue(max(1, math.floor(maximum)))
        if announce:
            self.show_information_box(
                "Maximum scale",
                f"The suggested maximum protein scale is: {maximum}x\n\n"
                f"'Protein Scale' has been set to {self.pScaleSpinBox.value():g}.",
                icon_path("icon_info.png"))

    def handle_select_minecraft_button(self):
        self.selectMinecraft = MinecraftPopup()
        if self.selectMinecraft.selected_directory is None:
            self.show_information_box(title_text="Error",
                                      text="Remember to select a Minecraft save.",
                                      icon_path=icon_path("icon_bad.png"))
            return
        self.user_minecraft_save = self.selectMinecraft.selected_directory
        SESSION.save_path = self.user_minecraft_save
        self.update_selection_labels()

    def handle_modify_residues_button(self):
        if not self.user_pdb_file:
            self.show_information_box(title_text="No structure selected",
                                      text="Please select a PDB or mmCIF file first.",
                                      icon_path=icon_path("icon_bad.png"))
            return
        try:
            structure = pdbm.load_structure(self.user_pdb_file)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "File Error", f"Failed to load structure for sequence selection:\n{e}")
            return
        popup = SequenceSelectorPopup(structure, self.residue_mods)
        popup.selection_made.connect(self.set_residue_mods)
        self.seq_selector = popup
        popup.show()

    def set_residue_mods(self, mods):
        SESSION.residue_mods = mods
        self.update_selection_labels()

    # --- generation ---
    def build_config(self):
        config = {
            'atoms': {'O': 'red_wool', 'N': 'blue_wool', 'P': 'lime_wool', 'S': 'yellow_wool',
                      'C': 'black_wool', 'FE': 'iron_block', 'other_atom': 'pink_concrete',
                      'backbone_atom': 'gray_concrete', 'sidechain_atom': 'gray_concrete'},
            'backbone_size': 1.0,
            'atom_scale': 1.5,
            'scale': self.pScaleSpinBox.value() if hasattr(self, "pScaleSpinBox") else 1.0,
            'show_atoms': True,
            'show_hetatm': True,
            'mesh': False,
            'backbone': True,
            'sidechain': True,
            'by_chain': False,
            'bar_style': False,
            'simple': self.simpleOutputCheck.isChecked(),
            'chain_blocks': self.chain_blocks,
            'residue_mods': self.residue_mods,
            'pdb_file': self.user_pdb_file,
            'save_path': self.user_minecraft_save,
        }
        self.mode_config(config)
        return config

    def handle_make_function_button(self):
        if self.user_pdb_file is None:
            self.show_information_box(title_text="Error: No PDB file",
                                      text="Please select a PDB file.",
                                      icon_path=icon_path("icon_bad.png"))
            return
        if self.user_minecraft_save is None:
            self.show_information_box(title_text="Error: No Minecraft save",
                                      text="Please select a Minecraft save.",
                                      icon_path=icon_path("icon_bad.png"))
            return
        if self.worker is not None and self.worker.isRunning():
            return

        self.createFunctionsButton.setEnabled(False)
        self.wait_dialog = PleaseWaitDialog(self)
        self.wait_dialog.show()
        self.worker = WorkerThread(self.MODE_NAME, self.build_config(), parent=self)
        self.worker.progress.connect(self.wait_dialog.set_progress)
        self.worker.result.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_finished(self, result):
        self.createFunctionsButton.setEnabled(True)
        if self.wait_dialog is not None:
            self.wait_dialog.close()
        if result.get("result") == "done":
            lower = result.get("lower", "")
            self.show_information_box(
                title_text="Model generated",
                text=f"Finished! \n Remember to use /reload\n Make your model with: /function protein:build_{lower}",
                icon_path=icon_path("icon_good.png"))
        else:
            self.show_information_box(
                title_text="Error encountered",
                text=f"Model has not generated! \nError: {result.get('error', '')}",
                icon_path=icon_path("icon_bad.png"))

    def show_information_box(self, title_text, text, icon_path):
        return show_information_box(self, title_text, text, icon_path)

    @staticmethod
    def icon(name):
        """Absolute path of an icon in UI/images/icons."""
        return icon_path(name)


def make_spin(parent, value, tooltip=""):
    spin = QtWidgets.QDoubleSpinBox(parent=parent)
    spin.setDecimals(1)
    spin.setMinimum(1.0)
    spin.setMaximum(50.0)
    spin.setSingleStep(0.5)
    spin.setValue(value)
    spin.setToolTip(tooltip)
    return spin


def set_enabled(enabled, *widgets):
    for widget in widgets:
        widget.setEnabled(bool(enabled))
