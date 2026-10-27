"""Dialog for the list of blocks used when a model is coloured by chain."""
from PyQt6 import QtCore, QtGui, QtWidgets

from PDB2MC.build import DEFAULT_CHAIN_BLOCKS
from PDB2MC.variables import decorative_blocks, hex_dict


def block_icon(block, size=16):
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtGui.QColor(hex_dict.get(block, "#ff00ff")))
    return QtGui.QIcon(pixmap)


def parse_blocks(text):
    """Block names typed as 'red concrete, blue_wool; Stone' -> (valid names, invalid names)."""
    valid, invalid = [], []
    for raw in text.replace(";", ",").replace("\n", ",").split(","):
        name = raw.strip().lower().replace(" ", "_").removeprefix("minecraft:")
        if not name:
            continue
        (valid if name in decorative_blocks else invalid).append(name)
    return valid, invalid


class ChainColorDialog(QtWidgets.QDialog):
    """
    Edit the chain colour list: chain 1 gets the first block, chain 2 the second, and so on; the list
    repeats when there are more chains than blocks.
    """

    def __init__(self, blocks=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chain colours")
        self.setModal(True)
        self.resize(360, 420)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel(
            "Blocks used for each chain, in order.\nThe list repeats when a model has more chains."))

        self.list = QtWidgets.QListWidget(self)
        self.list.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.list)

        entry_row = QtWidgets.QHBoxLayout()
        self.entry = QtWidgets.QLineEdit(self)
        self.entry.setPlaceholderText("Type a block, e.g. red_concrete (or several, comma separated)")
        completer = QtWidgets.QCompleter(decorative_blocks, self.entry)
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        self.entry.setCompleter(completer)
        self.add_button = QtWidgets.QPushButton("Add", self)
        entry_row.addWidget(self.entry)
        entry_row.addWidget(self.add_button)
        layout.addLayout(entry_row)

        button_row = QtWidgets.QHBoxLayout()
        self.up_button = QtWidgets.QPushButton("Up", self)
        self.down_button = QtWidgets.QPushButton("Down", self)
        self.remove_button = QtWidgets.QPushButton("Remove", self)
        self.reset_button = QtWidgets.QPushButton("Default", self)
        self.reset_button.setToolTip("Restore the preset chain colours")
        for button in (self.up_button, self.down_button, self.remove_button, self.reset_button):
            button_row.addWidget(button)
        layout.addLayout(button_row)

        self.message = QtWidgets.QLabel("", self)
        self.message.setStyleSheet("color: #a00;")
        layout.addWidget(self.message)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)

        self.add_button.clicked.connect(self.add_from_entry)
        self.entry.returnPressed.connect(self.add_from_entry)
        self.up_button.clicked.connect(lambda: self.move_selected(-1))
        self.down_button.clicked.connect(lambda: self.move_selected(1))
        self.remove_button.clicked.connect(self.remove_selected)
        self.reset_button.clicked.connect(lambda: self.set_blocks(DEFAULT_CHAIN_BLOCKS))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.set_blocks(blocks or DEFAULT_CHAIN_BLOCKS)

    def set_blocks(self, blocks):
        self.list.clear()
        for block in blocks:
            self.add_block(block)

    def add_block(self, block):
        item = QtWidgets.QListWidgetItem(block_icon(block), block)
        self.list.addItem(item)

    def blocks(self):
        return [self.list.item(i).text() for i in range(self.list.count())]

    def add_from_entry(self):
        valid, invalid = parse_blocks(self.entry.text())
        for block in valid:
            self.add_block(block)
        self.message.setText(f"Not a block: {', '.join(invalid)}" if invalid else "")
        if not invalid:
            self.entry.clear()

    def remove_selected(self):
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))

    def move_selected(self, step):
        rows = sorted((self.list.row(item) for item in self.list.selectedItems()), reverse=step > 0)
        for row in rows:
            target = row + step
            if 0 <= target < self.list.count():
                item = self.list.takeItem(row)
                self.list.insertItem(target, item)
                item.setSelected(True)

    def accept(self):
        if not self.blocks():
            self.message.setText("Add at least one block.")
            return
        super().accept()
