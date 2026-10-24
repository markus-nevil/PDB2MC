from PyQt6.QtWidgets import QMainWindow, QCompleter, QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QThread, pyqtSignal
import os
import traceback

from .utilities import MyComboBox, IncludedPDBPopup, MinecraftPopup, FileExplorerPopup, SequenceSelectorPopup, get_presets_path
from .sidebar import Sidebar, SIDEBAR_WIDTH
from .base_mode_window import connect_sidebar, show_information_box
from PDB2MC.variables import decorative_blocks, hex_dict
from PDB2MC import minecraft_functions as mcf, pdb_manipulation as pdbm, skeleton, resources

# Height (blocks) a model may occupy; used for the size check and the suggested maximum scale
WORLD_MAX = 320

# Colour choices in each dropdown, in display order; separators go between the four groups
COLOR_CHOICES = [
    f"{color}_{material}"
    for material in ("concrete", "glazed_terracotta", "terracotta", "wool")
    for color in ("red", "orange", "yellow", "lime", "green", "cyan", "light_blue", "blue",
                  "purple", "magenta", "pink", "brown", "black", "gray", "light_gray", "white")
] + [
    f"{color}_stained_glass"
    for color in ("red", "orange", "yellow", "lime", "green", "cyan", "light_blue", "blue",
                  "purple", "magenta", "pink", "brown", "black", "gray", "light_gray", "white")
]
DEFAULT_OTHER_COLOR = "pink_concrete"
DEFAULT_BACKBONE_COLOR = "gray_concrete"
DEFAULT_SIDECHAIN_COLOR = "gray_concrete"

# Widget geometry, one place to adjust the layout: (X, Y, WIDTH, HEIGHT)
UI_GEOMETRY = {
    "bg": (-90, -50, 881, 500),
    "backboneColorLabel": (120, 10, 120, 21),
    "backboneColorBox": (240, 10, 195, 22),
    "showBackboneCheck": (240, 37, 121, 17),
    "colorByBackboneCheck": (240, 55, 175, 20),
    "bScaleLabel": (120, 80, 111, 21),
    "backboneScaleSpinBox": (240, 80, 62, 22),
    "pScaleLabel": (120, 108, 111, 21),
    "pScaleSpinBox": (240, 108, 62, 22),
    "sidechainColorLabel": (120, 150, 120, 21),
    "sidechainColorBox": (240, 150, 195, 22),
    "showSidechainCheck": (240, 175, 121, 17),
    "otherColorLabel": (120, 210, 120, 21),
    "otherColorBox": (240, 210, 195, 22),
    "otherMoleculeCheck": (240, 238, 151, 17),
    "aScaleLabel": (120, 260, 111, 21),
    "aScaleSpinBox": (240, 260, 62, 22),
    "selectPDBFileButton": (120, 298, 101, 23),
    "orText": (221, 298, 25, 23),
    "selectIncludedPDBButton": (246, 298, 189, 23),
    "selectedPDBLabel": (120, 322, 315, 18),
    "andText": (120, 344, 30, 23),
    "selectMinecraftSaveButton": (150, 344, 285, 23),
    "selectedMinecraftLabel": (120, 368, 315, 18),
    "simpleOutputCheck": (120, 392, 110, 20),
    "modifyResiduesButton": (120, 414, 110, 26),
    "createFunctionsButton": (240, 396, 195, 40),
}


class WorkerThread(QThread):
    # Named `result` so it does not shadow QThread's own `finished` signal
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

    def __init__(self, config_data, parent=None):
        super().__init__(parent)
        self.config_data = config_data

    def run(self):
        config_data = self.config_data
        try:
            # The file was already read when it was selected; load_structure reuses that parse
            structure = pdbm.load_structure(config_data['pdb_file'])
            pdb_name = structure.name
            mc_dir = config_data['save_path']
            self.progress.emit(5)

            mcf.delete_old_files(mc_dir, pdb_name)
            self.progress.emit(10)

            # skeleton.run_mode reports 0-100 for its own work; map it onto 10-80
            skeleton.run_mode(config_data, pdb_name, structure, mc_dir,
                              progress=lambda value: self.progress.emit(10 + int(value * 0.7)))

            mcf.finish_nbts(mc_dir, config_data, pdb_name)
            self.progress.emit(85)
            mcf.create_nbt_delete(pdb_name, mc_dir)
            mcf.finish_delete_nbts(mc_dir, pdb_name)
            self.progress.emit(100)
            self.result.emit({"result": "done", "lower": pdb_name})
        except Exception as e:
            traceback.print_exc()
            self.result.emit({"result": "error", "error": f"{type(e).__name__}: {e}"})


class PleaseWaitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Please wait")
        layout = QVBoxLayout()
        self.status_label = QLabel("Processing, please wait...")
        layout.addWidget(self.status_label)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        self.setModal(True)

    def set_progress(self, value):
        self.progress_bar.setValue(value)
        if value < 10:
            self.status_label.setText("Reading structure file...")
        elif value < 17:
            self.status_label.setText("Scaling and positioning atoms...")
        elif value < 38:
            self.status_label.setText("Building backbone...")
        elif value < 59:
            self.status_label.setText("Building sidechains...")
        elif value < 80:
            self.status_label.setText("Building other molecules...")
        elif value < 100:
            self.status_label.setText("Writing Minecraft functions...")
        else:
            self.status_label.setText("Done!")


def get_images_path():
    """The UI directory; relative paths like 'images/icons/logo.png' resolve against it."""
    return resources.ui_dir()


def icon_path(name):
    return resources.image('icons', name)


class SkeletonWindow(QMainWindow):
    MODE_NAME = "Skeleton"

    def __init__(self):
        super().__init__()
        self.user_pdb_file = None
        self.user_minecraft_save = None
        self.last_sequence_selection = None
        self.worker = None

        self.setWindowTitle("Skeleton Mode")
        self.setWindowIcon(QIcon(icon_path('logo.png')))
        self.resize(450, 450)
        self.centralwidget = QtWidgets.QWidget(parent=self)
        self.centralwidget.setObjectName("centralwidget")

        self.bg = QtWidgets.QLabel(parent=self.centralwidget)
        self.bg.setPixmap(QtGui.QPixmap(resources.image("MC2PDB bg.png")))
        self.bg.setScaledContents(True)
        self.bg.setObjectName("bg")

        # Colour dropdowns
        self.backboneColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.sidechainColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.otherColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.otherColorBox = self._make_color_box("otherColorBox", DEFAULT_OTHER_COLOR)
        self.backboneColorBox = self._make_color_box("backboneColorBox", DEFAULT_BACKBONE_COLOR)
        self.sidechainColorBox = self._make_color_box("sidechainColorBox", DEFAULT_SIDECHAIN_COLOR)

        # Options
        self.aScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.otherMoleculeCheck = self._make_check("otherMoleculeCheck", True,
                                                   "Check to show other non-protein, DNA, or RNA molecules.")
        self.aScaleSpinBox = self._make_spin("aScaleSpinBox", 1.5, "Change the diameter (rounded up) of each atom.")
        self.showBackboneCheck = self._make_check("showBackboneCheck", True, "Show the N-C-C backbone of the main models.")
        self.showSidechainCheck = self._make_check("showSidechainCheck", True, "Show amino acid R-groups")
        self.colorByBackboneCheck = self._make_check("colorByBackboneCheck", False,
                                                     "Color the backbones of the main models by the molecule number.")
        self.pScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.pScaleSpinBox = self._make_spin("pScaleSpinBox", 1.0, "Scale the entire model by this factor.")
        self.bScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.backboneScaleSpinBox = self._make_spin("backboneScaleSpinBox", 1.0,
                                                    "Scale the width of the backbone by this factor.")
        self.simpleOutputCheck = self._make_check("simpleOutputCheck", True,
                                                  "Un-select to create individual commands for each molecule")

        # File selection
        self.selectPDBFileButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.selectIncludedPDBButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.selectMinecraftSaveButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.orText = self._make_small_label()
        self.andText = self._make_small_label()
        self.selectedPDBLabel = self._make_path_label()
        self.selectedMinecraftLabel = self._make_path_label()

        self.modifyResiduesButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.modifyResiduesButton.setToolTip("Preview: choose residues to annotate (does not change the output yet)")
        font = QtGui.QFont()
        font.setPointSize(9)
        self.modifyResiduesButton.setFont(font)

        self.createFunctionsButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.createFunctionsButton.setToolTip("Add the selected PDB file to the Minecraft world")
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.createFunctionsButton.setFont(font)

        for name, geom in UI_GEOMETRY.items():
            getattr(self, name).setGeometry(QtCore.QRect(*geom))
        self.bg.lower()

        # Sidebar on top of the background, on the left
        self.sidebar = Sidebar(self.centralwidget, width=SIDEBAR_WIDTH)
        self.sidebar.setGeometry(0, 0, SIDEBAR_WIDTH, self.height())
        self.sidebar.setFixedHeight(self.height())
        self.sidebar.raise_()
        connect_sidebar(self, self.sidebar)

        self.setCentralWidget(self.centralwidget)
        self.retranslateUi()
        self.update_selection_labels()
        self.setFixedSize(self.size())

        # Signals
        self.selectIncludedPDBButton.clicked.connect(self.handle_included_pdb_button)
        self.selectPDBFileButton.clicked.connect(self.handle_select_pdb_file_button)
        self.selectMinecraftSaveButton.clicked.connect(self.handle_select_minecraft_button)
        self.createFunctionsButton.clicked.connect(self.handle_make_function_button)
        self.modifyResiduesButton.clicked.connect(self.handle_modify_residues_button)
        for box in (self.otherColorBox, self.backboneColorBox, self.sidechainColorBox):
            box.focusOut.connect(lambda box=box: self.check_input(box, decorative_blocks))
        self.showBackboneCheck.stateChanged.connect(self.on_showBackboneCheck_changed)
        self.showSidechainCheck.stateChanged.connect(self.on_showSidechainCheck_changed)
        self.colorByBackboneCheck.stateChanged.connect(self.on_colorByBackboneCheck_changed)
        self.otherMoleculeCheck.stateChanged.connect(self.on_otherMoleculeCheck_changed)

    # --- widget factories ---
    def _make_color_box(self, name, default):
        box = MyComboBox(self.centralwidget)
        box.setObjectName(name)
        box.setEditable(True)
        for value in COLOR_CHOICES:
            box.addItem(create_icon(hex_dict.get(value, "#ff00ff")), value)
        # separators between concrete / glazed terracotta / terracotta / wool / stained glass
        for index in (64, 48, 32, 16):
            box.insertSeparator(index)
        set_combobox_by_text(box, default)
        completer = QCompleter(decorative_blocks, box)
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        box.setCompleter(completer)
        return box

    def _make_check(self, name, checked, tooltip):
        check = QtWidgets.QCheckBox(parent=self.centralwidget)
        check.setObjectName(name)
        check.setChecked(checked)
        check.setToolTip(tooltip)
        return check

    def _make_spin(self, name, value, tooltip):
        spin = QtWidgets.QDoubleSpinBox(parent=self.centralwidget)
        spin.setObjectName(name)
        spin.setDecimals(1)
        spin.setMinimum(1.0)
        spin.setMaximum(50.0)
        spin.setSingleStep(0.5)
        spin.setValue(value)
        spin.setToolTip(tooltip)
        return spin

    def _make_small_label(self):
        label = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(9)
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        return label

    def _make_path_label(self):
        label = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(8)
        label.setFont(font)
        label.setStyleSheet("background-color: rgba(255, 255, 255, 140);")
        return label

    # --- state handlers ---
    def on_showBackboneCheck_changed(self, state):
        if not self.colorByBackboneCheck.isChecked():
            self.backboneColorBox.setEnabled(state != 0)
        self.backboneScaleSpinBox.setEnabled(state != 0)

    def on_showSidechainCheck_changed(self, state):
        if not self.colorByBackboneCheck.isChecked():
            self.sidechainColorBox.setEnabled(state != 0)

    def on_colorByBackboneCheck_changed(self, state):
        self.backboneColorBox.setEnabled(state == 0 and self.showBackboneCheck.isChecked())
        self.sidechainColorBox.setEnabled(state == 0 and self.showSidechainCheck.isChecked())

    def on_otherMoleculeCheck_changed(self, state):
        self.otherColorBox.setEnabled(state != 0)
        self.aScaleSpinBox.setEnabled(state != 0)

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
        show(self.selectedPDBLabel, self.user_pdb_file, "No PDB file selected.")
        save = mcf.world_dir(self.user_minecraft_save) if self.user_minecraft_save else None
        show(self.selectedMinecraftLabel, save, "No Minecraft save selected.")

    # --- file selection ---
    def handle_select_pdb_file_button(self):
        self.selectPDB = FileExplorerPopup()
        if self.selectPDB.selected_file:
            self.set_pdb_file(self.selectPDB.selected_file, show_scale=True)

    def set_pdb_file(self, path, show_scale=False):
        self.user_pdb_file = path
        self.update_selection_labels()
        if not show_scale:
            return
        try:
            if not pdbm.check_model_size(path, world_max=WORLD_MAX):
                self.show_information_box("Model too large!", "The chosen model is too large for Minecraft.",
                                          icon_path("icon_bad.png"))
            else:
                size_factor = pdbm.check_max_size(path, world_max=WORLD_MAX)
                self.show_information_box(
                    "Maximum scale",
                    f"The suggested maximum protein scale is: {size_factor}x\n\nSet 'Protein Scale' below this for best results.",
                    icon_path("icon_info.png"))
        except Exception as e:
            self.show_information_box("Scale error", f"Could not determine recommended scale.\nError: {e}",
                                      icon_path("icon_bad.png"))

    def handle_select_minecraft_button(self):
        self.selectMinecraft = MinecraftPopup()
        if self.selectMinecraft.selected_directory is None:
            self.show_information_box(title_text="Error",
                                      text="Remember to select a Minecraft save.",
                                      icon_path=icon_path("icon_bad.png"))
            return
        self.user_minecraft_save = self.selectMinecraft.selected_directory
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
        popup = SequenceSelectorPopup(structure)
        self.seq_selector = popup
        popup.destroyed.connect(lambda obj=None, p=popup: setattr(self, "last_sequence_selection",
                                                                  getattr(p, "selection_output", None)))
        popup.show()

    def handle_included_pdb_button(self):
        self.includedPDB = IncludedPDBPopup()
        self.includedPDB.selected.connect(self.save_selected_text)
        self.includedPDB.show()

    def save_selected_text(self, text):
        # IncludedPDBPopup already showed the size / scale message
        self.set_pdb_file(os.path.join(get_presets_path(), f"{text}.pdb"))

    # --- generation ---
    def build_config(self):
        config_data = {'atoms': {
            'O': 'red_wool',
            'N': 'blue_wool',
            'P': 'lime_wool',
            'S': 'yellow_wool',
            'C': 'black_wool',
            'FE': 'iron_block',
            'other_atom': self.otherColorBox.currentText(),
            'backbone_atom': self.backboneColorBox.currentText(),
            'sidechain_atom': self.sidechainColorBox.currentText(),
        }}
        config_data['backbone_size'] = self.backboneScaleSpinBox.value()
        config_data['atom_scale'] = self.aScaleSpinBox.value()
        config_data['scale'] = self.pScaleSpinBox.value()
        config_data['show_hetatm'] = self.otherMoleculeCheck.isChecked()
        config_data['backbone'] = self.showBackboneCheck.isChecked()
        config_data['sidechain'] = self.showSidechainCheck.isChecked()
        config_data['by_chain'] = self.colorByBackboneCheck.isChecked()
        config_data['simple'] = self.simpleOutputCheck.isChecked()
        config_data['pdb_file'] = self.user_pdb_file
        config_data['save_path'] = self.user_minecraft_save
        return config_data

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

        self.worker = WorkerThread(self.build_config(), parent=self)
        self.worker.progress.connect(self.wait_dialog.set_progress)
        self.worker.result.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_finished(self, result):
        self.createFunctionsButton.setEnabled(True)
        self.wait_dialog.close()
        if result.get("result") == "done":
            lower = result.get("lower", "")
            self.show_information_box(
                title_text="Model generated",
                text=f"Finished! \n Remember to use /reload\n Make your model with: /function protein:build_{lower}",
                icon_path=icon_path("icon_good.png")
            )
        else:
            self.show_information_box(
                title_text="Error encountered",
                text=f"Model has not generated! \nError: {result.get('error', '')}",
                icon_path=icon_path("icon_bad.png")
            )

    def show_information_box(self, title_text, text, icon_path):
        return show_information_box(self, title_text, text, icon_path)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("SkeletonWindow", "Skeleton Mode"))
        self.backboneColorLabel.setText(_translate("SkeletonWindow", "Select backbone color:"))
        self.sidechainColorLabel.setText(_translate("SkeletonWindow", "Select sidechain color:"))
        self.otherColorLabel.setText(_translate("SkeletonWindow", "Select other color:"))
        self.aScaleLabel.setText(_translate("SkeletonWindow", "Atom scale:"))
        self.otherMoleculeCheck.setText(_translate("SkeletonWindow", "Show other molecules"))
        self.showBackboneCheck.setText(_translate("SkeletonWindow", "Show backbone"))
        self.showSidechainCheck.setText(_translate("SkeletonWindow", "Show sidechain"))
        self.colorByBackboneCheck.setText(_translate("SkeletonWindow", "Color backbone by chain"))
        self.pScaleLabel.setText(_translate("SkeletonWindow", "Protein scale:"))
        self.bScaleLabel.setText(_translate("SkeletonWindow", "Backbone scale:"))
        self.selectIncludedPDBButton.setText(_translate("SkeletonWindow", "Select Included PDB File"))
        self.selectMinecraftSaveButton.setText(_translate("SkeletonWindow", "Select Minecraft Save"))
        self.simpleOutputCheck.setText(_translate("SkeletonWindow", "Simple output"))
        self.selectPDBFileButton.setText(_translate("SkeletonWindow", "Select PDB File"))
        self.modifyResiduesButton.setText(_translate("SkeletonWindow", "Modify Residues"))
        self.createFunctionsButton.setText(_translate("SkeletonWindow", "Create Minecraft\nFunctions"))
        self.orText.setText(_translate("SkeletonWindow", "or"))
        self.andText.setText(_translate("SkeletonWindow", "and"))


def set_combobox_by_text(combobox, text):
    index = combobox.findText(text)
    if index >= 0:  # If the text is found
        combobox.setCurrentIndex(index)


def create_icon(hex_color: str, size: int = 100) -> QIcon:
    pixmap = QPixmap(size, size)
    painter = QPainter(pixmap)
    painter.setBrush(QColor(hex_color))
    painter.drawRect(0, 0, size, size)
    painter.end()
    return QIcon(pixmap)
