"""
Mode windows: the shared ModeWindow base class, its worker thread, and switching between modes.

A mode window lists its options as columns of rows (see Color, Check, Spin, Choice, Gap); ModeWindow lays
them out next to the sidebar, adds the shared model / save selection, Modify Residues and Create
buttons, and runs the build for its MODE_NAME through PDB2MC.build.build_model. Tool tips come from
UI/tooltips.py, looked up by the option's name.
"""
import math
import os
import traceback
from dataclasses import dataclass, field

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QDesktopServices, QIcon, QPainter, QPixmap

from PDB2MC import build, fetch, minecraft_functions as mcf, pdb_manipulation as pdbm, resources, triggers, user_settings
from PDB2MC.variables import decorative_blocks, hex_dict
from . import messages, tooltips
from .chain_colors import ChainColorDialog
from .session import SESSION
from .sidebar import Sidebar, SIDEBAR_WIDTH
from .utilities import (FileExplorerPopup, IncludedPDBPopup, MinecraftPopup, MyComboBox, SequenceSelectorPopup,
                        apply_message_style, get_presets_path, show_message, showing_message)
from .voxel_view import VoxelVolume, model_voxels

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
BOTTOM_HEIGHT = 202
# Every mode window is at least this tall, so switching modes doesn't resize the window
MIN_HEIGHT = 458

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


@dataclass
class Check:
    """Checkbox under the dropdown column."""
    name: str
    text: str
    default: bool


@dataclass
class Spin:
    """Label and number box."""
    name: str
    label: str
    default: float
    minimum: float = 1.0
    maximum: float = 50.0
    step: float = 0.5
    decimals: int = 1


@dataclass
class Choice:
    """Label and a plain dropdown of fixed choices."""
    name: str
    label: str
    items: list = field(default_factory=list)
    default: str = ""


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
    status = pyqtSignal(str)
    # Voxel positions and colours of the model, for the progress animation
    model_ready = pyqtSignal(object, object)

    def __init__(self, mode, config_data, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.config_data = config_data

    def send_model(self, structure):
        try:
            self.model_ready.emit(*model_voxels(structure, self.config_data))
        except Exception:
            # The animation is a nicety; it must never stop a build
            traceback.print_exc()

    def run(self):
        try:
            name = build.build_model(self.mode, self.config_data, progress=self.progress.emit,
                                     status=self.status.emit, on_structure=self.send_model)
            self.result.emit({"result": "done", "lower": name})
        except Exception as e:
            traceback.print_exc()
            self.result.emit({"result": "error", "error": f"{type(e).__name__}: {e}"})


class PleaseWaitDialog(QtWidgets.QDialog):
    """Progress of a build: the model filling a rotating voxel volume, what is happening, and a progress bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(messages.BUILD_PROGRESS.title)
        apply_message_style(self)
        layout = QtWidgets.QVBoxLayout()
        self.volume = VoxelVolume(self)
        layout.addWidget(self.volume, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.status_label = QtWidgets.QLabel(messages.BUILD_PROGRESS.body)
        layout.addWidget(self.status_label)
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        self.setModal(True)

    def set_progress(self, value):
        self.progress_bar.setValue(value)
        self.volume.set_progress(value)

    def set_status(self, text):
        self.status_label.setText(text)

    def closeEvent(self, event):
        self.volume.stop()
        super().closeEvent(event)


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


def default_model_name(path):
    """
    The name a model starts with: the PDB ID in the file, or the file's name if it has none. The included
    examples keep the example's name; several of them are cut from the same PDB entry.
    """
    stem = build.custom_model_name(os.path.splitext(os.path.basename(path))[0])
    if os.path.normcase(os.path.dirname(os.path.abspath(path))) == os.path.normcase(os.path.abspath(get_presets_path())):
        return stem
    try:
        return build.custom_model_name(pdbm.load_structure(path).metadata.get('id', "")) or stem
    except Exception:
        return stem


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
        width, column_bottoms = self._build_options()
        # The file and Minecraft controls go under the first column; later columns may reach down beside them
        first = column_bottoms[0] if column_bottoms else MARGIN
        height = max(first + BOTTOM_HEIGHT + MARGIN, max(column_bottoms, default=MARGIN) + MARGIN, MIN_HEIGHT)
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
            chain_check = getattr(self, self.CHAIN_CHECK)
            chain_check.clicked.connect(self.on_chain_check_clicked)
            if hasattr(self, "colorSchemeBox"):
                chain_check.stateChanged.connect(self.refresh_scheme_box)
                self.refresh_scheme_box()
        self.restore_session()

    # --- layout ---
    def _build_options(self):
        """Create the option widgets column by column; returns the width they need and where each column ends."""
        left = SIDEBAR_WIDTH + MARGIN
        bottoms = []
        for column in self.OPTION_COLUMNS:
            y = MARGIN
            for row in column:
                y = self._add_row(row, left, y)
            bottoms.append(y)
            left += COLUMN_WIDTH + COLUMN_GAP
        return left - COLUMN_GAP + MARGIN, bottoms

    def _place(self, name, widget, x, y, w, h):
        widget.setObjectName(name)
        widget.setGeometry(QtCore.QRect(x, y, w, h))
        self.geometry_map[name] = (x, y, w, h)
        setattr(self, name, widget)

    def _add_row(self, row, x, y):
        field_x = x + LABEL_WIDTH
        if isinstance(row, Gap):
            return y + row.height
        tooltip = tooltips.option(row.name, self.MODE_NAME)
        if isinstance(row, Check):
            check = QtWidgets.QCheckBox(row.text, parent=self.centralwidget)
            check.setChecked(row.default)
            check.setToolTip(tooltip)
            self._place(row.name, check, field_x, y, FIELD_WIDTH, CHECK_HEIGHT)
            return y + CHECK_HEIGHT + 2
        label = QtWidgets.QLabel(row.label, parent=self.centralwidget)
        label.setToolTip(tooltip)
        self._place(row.name + "Label", label, x, y, LABEL_WIDTH, ROW_HEIGHT)
        if isinstance(row, Color):
            widget = self.make_color_box(row.default)
            self._place(row.name, widget, field_x, y, FIELD_WIDTH, ROW_HEIGHT)
        elif isinstance(row, Spin):
            widget = make_spin(self.centralwidget, row)
            self._place(row.name, widget, field_x, y, 62, ROW_HEIGHT)
        elif isinstance(row, Choice):
            widget = QtWidgets.QComboBox(parent=self.centralwidget)
            widget.addItems(row.items)
            widget.setCurrentText(row.default or row.items[0])
            self._place(row.name, widget, field_x, y, FIELD_WIDTH, ROW_HEIGHT)
        else:
            raise TypeError(f"Unknown option row: {row!r}")
        widget.setToolTip(tooltip)
        return y + ROW_HEIGHT + ROW_SPACING

    def _build_bottom(self, top):
        x = SIDEBAR_WIDTH + MARGIN

        def button(name, text, rect, point=None, bold=False):
            widget = QtWidgets.QPushButton(text, parent=self.centralwidget)
            if point:
                font = QtGui.QFont()
                font.setPointSize(point)
                font.setBold(bold)
                widget.setFont(font)
            widget.setToolTip(tooltips.option(name, self.MODE_NAME))
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

        button("selectPDBFileButton", "Select PDB File", (0, 0, 103, 23))
        button("selectIncludedPDBButton", "Included Model", (106, 0, 103, 23))
        button("pdbIdButton", "Load PDB ID", (212, 0, 103, 23))
        path_label("selectedPDBLabel", (0, 24, COLUMN_WIDTH, 18))
        name_label = QtWidgets.QLabel("Model name:", parent=self.centralwidget)
        name_label.setToolTip(tooltips.option("modelNameEdit", self.MODE_NAME))
        self._place("modelNameLabel", name_label, x, top + 46, 80, 22)
        name_edit = QtWidgets.QLineEdit(parent=self.centralwidget)
        name_edit.setToolTip(tooltips.option("modelNameEdit", self.MODE_NAME))
        name_edit.setPlaceholderText("Filled in when you select a structure")
        self._place("modelNameEdit", name_edit, x + 80, top + 46, COLUMN_WIDTH - 80, 22)
        small_label("andText", "and", (0, 72, 30, 23))
        button("selectMinecraftSaveButton", "Select Minecraft Save", (30, 72, 285, 23))
        path_label("selectedMinecraftLabel", (0, 96, COLUMN_WIDTH, 18))
        check = QtWidgets.QCheckBox("Simple output", parent=self.centralwidget)
        check.setChecked(True)
        check.setToolTip(tooltips.option("simpleOutputCheck", self.MODE_NAME))
        button("previewButton", "Preview Model and Size", (0, 120, COLUMN_WIDTH - 5, 24))
        self._place("simpleOutputCheck", check, x, top + 148, 110, 20)
        button("modifyResiduesButton", "Modify Residues", (0, 170, 110, 26), point=9)
        button("createFunctionsButton", "Create Minecraft\nFunctions", (120, 152, 195, 44), point=11, bold=True)

        self.selectPDBFileButton.clicked.connect(self.handle_select_pdb_file_button)
        self.selectIncludedPDBButton.clicked.connect(self.handle_included_pdb_button)
        self.pdbIdButton.clicked.connect(self.handle_pdb_id_button)
        self.selectMinecraftSaveButton.clicked.connect(self.handle_select_minecraft_button)
        self.modifyResiduesButton.clicked.connect(self.handle_modify_residues_button)
        self.previewButton.clicked.connect(self.handle_preview_button)
        self.createFunctionsButton.clicked.connect(self.handle_make_function_button)
        self.modelNameEdit.textEdited.connect(self.on_model_name_edited)
        self.modelNameEdit.editingFinished.connect(self.tidy_model_name)

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

    def on_model_name_edited(self, text):
        SESSION.model_name = text

    def tidy_model_name(self):
        """Show the name as it will be used; an emptied box goes back to the structure's own name."""
        name = build.custom_model_name(self.modelNameEdit.text())
        if not name and self.user_pdb_file:
            name = default_model_name(self.user_pdb_file)
        SESSION.model_name = name
        self.modelNameEdit.setText(name)

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
            show_message(self, messages.INVALID_BLOCK, block_name=text)
            combobox.setCurrentIndex(0)
            return
        if combobox.findText(text) < 0:
            combobox.addItem(create_icon(hex_dict.get(text, "#ff00ff")), text)
        combobox.setCurrentIndex(combobox.findText(text))

    def on_chain_check_clicked(self, checked):
        # Only the chain and molecule schemes use the chain colour list
        if checked and self.color_scheme() in ("Chain", "Molecule"):
            self.edit_chain_colors()

    def color_scheme(self):
        box = getattr(self, "colorSchemeBox", None)
        return box.currentText() if box is not None else "Chain"

    def refresh_scheme_box(self, *_):
        self.colorSchemeBox.setEnabled(getattr(self, self.CHAIN_CHECK).isChecked())

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
                label.setToolTip(tooltips.tip(tooltips.SELECTION_LABELS, label.objectName()))
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
            self.open_structure(self.selectPDB.selected_file)

    def handle_pdb_id_button(self):
        text, accepted = QtWidgets.QInputDialog.getText(self, messages.ASK_PDB_ID.title,
                                                        messages.ASK_PDB_ID.body)
        if not accepted or not text.strip():
            return
        pdb_id = fetch.normalize_id(text)
        if pdb_id is None:
            show_message(self, messages.INVALID_PDB_ID, text=text.strip())
            return
        download_error = path = None
        with showing_message(self, messages.DOWNLOADING, pdb_id=pdb_id):
            try:
                # Keep the window drawing while the file comes in
                path = fetch.download(pdb_id, progress=lambda done, total: QtWidgets.QApplication.processEvents())
            except fetch.DownloadError as e:
                download_error = e
        if download_error is not None:
            show_message(self, messages.DOWNLOAD_ERROR, pdb_id=pdb_id, error=download_error)
            return
        self.open_structure(path)

    def open_structure(self, path):
        """Use a structure file: load it, set the scale, and tell the user the scale or what went wrong."""
        load_error = announce_scale = None
        # The next window opens only after this one has closed, so it isn't left behind this window
        with showing_message(self, messages.CALCULATING_SIZE):
            try:
                # Load the file now to catch errors early; the parsed result is cached for later steps
                pdbm.load_structure(path)
            except Exception as e:
                load_error = e
            else:
                announce_scale = self.use_pdb_file(path)
        if load_error is not None:
            show_message(self, messages.FILE_LOAD_ERROR, block=True, error=load_error)
        else:
            announce_scale()

    def handle_included_pdb_button(self):
        self.includedPDB = IncludedPDBPopup()
        self.includedPDB.selected.connect(self.save_selected_text)
        self.includedPDB.show()

    def save_selected_text(self, text):
        self.set_pdb_file(os.path.join(get_presets_path(), f"{text}.pdb"))

    def set_pdb_file(self, path, announce=True):
        """Use the structure at path, and optionally tell the user the protein scale that came with it."""
        announce_scale = self.use_pdb_file(path)
        if announce:
            announce_scale()

    def use_pdb_file(self, path):
        """
        Use the structure at path: shared with the other modes, and the protein scale is set to the
        largest whole number that fits in the world. Returns a function that shows the result to the user.
        """
        self.user_pdb_file = path
        SESSION.set_pdb_file(path)
        if not SESSION.model_name:
            SESSION.model_name = default_model_name(path)
        self.modelNameEdit.setText(SESSION.model_name)
        self.update_selection_labels()
        try:
            fits, maximum = suggested_scale(path)
        except Exception as e:
            return lambda error=e: show_message(self, messages.SCALE_ERROR, error=error)
        if not fits:
            return lambda: show_message(self, messages.MODEL_TOO_LARGE)
        if hasattr(self, "pScaleSpinBox"):
            self.pScaleSpinBox.setValue(max(1, math.floor(maximum)))
        return lambda: show_message(self, messages.MAXIMUM_SCALE, maximum=maximum,
                                    scale=f"{self.pScaleSpinBox.value():g}")

    def handle_select_minecraft_button(self):
        self.selectMinecraft = MinecraftPopup()
        if self.selectMinecraft.selected_directory is None:
            show_message(self, messages.SAVE_REMINDER)
            return
        self.user_minecraft_save = self.selectMinecraft.selected_directory
        SESSION.save_path = self.user_minecraft_save
        self.update_selection_labels()

    def handle_preview_button(self):
        if not self.user_pdb_file:
            show_message(self, messages.NO_STRUCTURE)
            return
        from .preview import PreviewDialog
        try:
            structure = pdbm.load_structure(self.user_pdb_file)
            self.preview = PreviewDialog(structure, self.build_config(), self.MODE_NAME, parent=self)
        except Exception as e:
            show_message(self, messages.FILE_LOAD_ERROR, block=True, error=e)
            return
        self.preview.show()

    def handle_modify_residues_button(self):
        if not self.user_pdb_file:
            show_message(self, messages.NO_STRUCTURE)
            return
        try:
            structure = pdbm.load_structure(self.user_pdb_file)
        except Exception as e:
            show_message(self, messages.STRUCTURE_LOAD_ERROR, block=True, error=e)
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
                      'C': 'black_wool', 'other_atom': 'pink_concrete', **user_settings.metal_blocks(),
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
            'model_name': build.custom_model_name(self.modelNameEdit.text()) or None,
            'triggers': True,
            'color_scheme': self.color_scheme(),
        }
        self.mode_config(config)
        return config

    def handle_make_function_button(self):
        if self.user_pdb_file is None:
            show_message(self, messages.NO_PDB_FILE)
            return
        if self.user_minecraft_save is None:
            show_message(self, messages.NO_MINECRAFT_SAVE)
            return
        if self.worker is not None and self.worker.isRunning():
            return

        self.createFunctionsButton.setEnabled(False)
        self.wait_dialog = PleaseWaitDialog(self)
        self.wait_dialog.show()
        self.worker = WorkerThread(self.MODE_NAME, self.build_config(), parent=self)
        self.worker.progress.connect(self.wait_dialog.set_progress)
        self.worker.status.connect(self.wait_dialog.set_status)
        self.worker.model_ready.connect(self.wait_dialog.volume.set_model)
        self.worker.result.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_finished(self, result):
        self.createFunctionsButton.setEnabled(True)
        if self.wait_dialog is not None:
            self.wait_dialog.close()
        if result.get("result") == "done":
            lower = result.get("lower", "")
            number = triggers.model_number(self.user_minecraft_save, lower)
            show_message(self, messages.MODEL_FINISHED, name=lower, **triggers.commands(lower, number))
        else:
            show_message(self, messages.BUILD_ERROR, error=result.get('error', ''))

    @staticmethod
    def icon(name):
        """Absolute path of an icon in UI/images/icons."""
        return icon_path(name)


def make_spin(parent, row):
    spin = QtWidgets.QDoubleSpinBox(parent=parent)
    spin.setDecimals(row.decimals)
    spin.setMinimum(row.minimum)
    spin.setMaximum(row.maximum)
    spin.setSingleStep(row.step)
    spin.setValue(row.default)
    return spin


def set_enabled(enabled, *widgets):
    for widget in widgets:
        widget.setEnabled(bool(enabled))
