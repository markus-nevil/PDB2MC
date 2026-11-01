"""Windows of the settings that are kept between runs (see PDB2MC.user_settings), opened from the Tools window."""
import os

from PyQt6 import QtCore, QtGui, QtWidgets

from PDB2MC import defaults, user_settings
from PDB2MC.variables import decorative_blocks
from . import tooltips
from .chain_colors import block_icon, parse_blocks

METAL_COLUMNS = 2


def block_model(parent):
    """All blocks with their colours, shared by every dropdown so each doesn't have to build its own."""
    model = QtGui.QStandardItemModel(parent)
    for block in decorative_blocks:
        model.appendRow(QtGui.QStandardItem(block_icon(block), block))
    return model


def select_block(box, block):
    """Show a block in an editable dropdown; selecting it by index is what updates the colour swatch."""
    index = box.findText(block)
    if index >= 0:
        box.setCurrentIndex(index)
    else:
        box.setCurrentText(block)


class MetalIonDialog(QtWidgets.QDialog):
    """Choose the block of each metal ion. "Okay" saves the choices; they apply to every mode."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Metal Ion Settings")
        self.setModal(True)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Blocks for metal ions, in every mode. These stay until you change them."))

        grid = QtWidgets.QGridLayout()
        blocks = user_settings.metal_blocks()
        model = block_model(self)
        self.boxes = {}
        per_column = -(-len(defaults.METAL_IONS) // METAL_COLUMNS)
        for index, (metal, (name, _)) in enumerate(defaults.METAL_IONS.items()):
            column, row = divmod(index, per_column)
            label = QtWidgets.QLabel(f"{name} ({metal.capitalize()}):", self)
            box = QtWidgets.QComboBox(self)
            box.setEditable(True)
            box.setModel(model)
            box.setMaxVisibleItems(20)
            completer = QtWidgets.QCompleter(decorative_blocks, box)
            completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
            box.setCompleter(completer)
            select_block(box, blocks[metal])
            box.lineEdit().editingFinished.connect(lambda box=box: select_block(box, box.currentText()))
            tip = tooltips.tip(tooltips.METAL_DIALOG, "metalBlock", name=name.lower())
            label.setToolTip(tip)
            box.setToolTip(tip)
            grid.addWidget(label, row, column * 2)
            grid.addWidget(box, row, column * 2 + 1)
            self.boxes[metal] = box
        layout.addLayout(grid)

        self.message = QtWidgets.QLabel("", self)
        self.message.setStyleSheet("color: #a00;")
        layout.addWidget(self.message)

        buttons = QtWidgets.QHBoxLayout()
        self.reset_button = QtWidgets.QPushButton("Default", self)
        self.reset_button.setToolTip(tooltips.tip(tooltips.METAL_DIALOG, "reset"))
        buttons.addWidget(self.reset_button)
        buttons.addStretch(1)
        box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                         | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.addWidget(box)
        layout.addLayout(buttons)

        self.reset_button.clicked.connect(self.reset)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)

    def reset(self):
        for metal, block in defaults.default_metal_blocks().items():
            select_block(self.boxes[metal], block)
        self.message.setText("")

    def chosen(self):
        """({metal: block}, typed names that are not blocks)."""
        blocks, invalid = {}, []
        for metal, box in self.boxes.items():
            valid, wrong = parse_blocks(box.currentText())
            if valid:
                blocks[metal] = valid[0]
            invalid += wrong or ([] if valid else [box.currentText()])
        return blocks, invalid

    def accept(self):
        blocks, invalid = self.chosen()
        if invalid:
            self.message.setText(f"Not a block: {', '.join(invalid)}")
            return
        user_settings.set_metal_blocks(blocks)
        super().accept()


class DefaultFolderDialog(QtWidgets.QDialog):
    """Choose the folder the "Select PDB File" window starts in."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Default PDB/CIF Folder")
        self.setModal(True)
        self.resize(460, 120)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Select PDB File starts in this folder. It stays until you change it."))

        row = QtWidgets.QHBoxLayout()
        self.path = QtWidgets.QLineEdit(user_settings.saved_structure_dir(), self)
        self.path.setPlaceholderText("No folder chosen")
        self.path.setToolTip(tooltips.tip(tooltips.FOLDER_DIALOG, "path"))
        self.browse_button = QtWidgets.QPushButton("Browse...", self)
        self.browse_button.setToolTip(tooltips.tip(tooltips.FOLDER_DIALOG, "browse"))
        self.clear_button = QtWidgets.QPushButton("Clear", self)
        self.clear_button.setToolTip(tooltips.tip(tooltips.FOLDER_DIALOG, "clear"))
        row.addWidget(self.path)
        row.addWidget(self.browse_button)
        row.addWidget(self.clear_button)
        layout.addLayout(row)

        self.message = QtWidgets.QLabel("", self)
        self.message.setStyleSheet("color: #a00;")
        layout.addWidget(self.message)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)
        self.browse_button.clicked.connect(self.browse)
        self.clear_button.clicked.connect(self.path.clear)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def browse(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Default PDB/CIF folder", self.path.text())
        if folder:
            self.path.setText(os.path.normpath(folder))

    def accept(self):
        folder = self.path.text().strip()
        if folder and not os.path.isdir(folder):
            self.message.setText("That folder does not exist.")
            return
        user_settings.set_structure_dir(folder)
        super().accept()
