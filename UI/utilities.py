import os
from shutil import copyfile
from PyQt6.QtWidgets import QFileDialog, QApplication, QListWidget, QPushButton, QMainWindow, QMessageBox, QLabel
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6 import QtCore, QtGui, QtWidgets

from PDB2MC import pdb_manipulation as pdbm
import sys
import pkg_resources


class MyComboBox(QtWidgets.QComboBox):
    focusOut = pyqtSignal()
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focusOut.emit()

class InformationBox(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle("Custom Popup")
        os.chdir(get_images_path())

        self.setWindowIcon(QIcon('images/icons/logo.png'))

        # Set background image
        self.setStyleSheet("background-image: url(images/MC2PDB bg.png);")
        self.resize(500, 150)

        labelTitle = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap("images/icons/icon_info.png")
        pixmap = pixmap.scaled(200, 200)
        labelTitle.setScaledContents(True)
        labelTitle.setGeometry(QtCore.QRect(37, 37, 75, 75))

        labelTitle.setPixmap(pixmap)
        labelTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.layout().addWidget(labelTitle)

        # Create labels
        self.label1 = QLabel("test", self)
        self.label1.setScaledContents(True)
        self.label1.adjustSize()
        self.label1.move(250, 20)  # Adjust position as needed

        # Create "Okay" button
        self.okayButton = QPushButton("Okay", self)
        self.okayButton.setStyleSheet("background-color: rgba(0, 0, 0, 99);")
        self.okayButton.move(250, 100)  # Adjust position as needed
        self.okayButton.clicked.connect(self.close)


    def set_text(self, text1):
        self.label1.setText(text1)

        # Center justify the text
        self.label1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create a QFont object
        font1 = QFont()

        #Calculate the length of the longest part of the text when separated by \n characters
        longest = 0
        for i in text1.split("\n"):
            if len(i) > longest:
                longest = len(i)

        # Calculate the optimal font size based on the length of the text
        # and the width of the label (you may need to adjust the formula)
        font_size1 = min(14, max(8, 600 // longest))

        # Set the font size
        font1.setPointSize(font_size1)

        # Apply the font to the labels
        self.label1.setFont(font1)
        #self.label1.setScaledContents(True)
        #self.label1.setMaximumSize(350, 100)
        self.label1.adjustSize()

        # Calculate the desired center position
        center_x = 300
        center_y = 50

        # Calculate the top-left position based on the center position and the size of the QLabel
        top_left_x = int(round(center_x - self.label1.width() / 2))
        top_left_y = int(round(center_y - self.label1.height() / 2))

        # Set the position of the QLabel
        self.label1.move(top_left_x, top_left_y)

    # function that changes the icon image between 3 choices: icon_good, icon_bad, icon_info
    def set_icon(self, icon):
        labelTitle = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap(icon)
        pixmap = pixmap.scaled(200, 200)
        labelTitle.setScaledContents(True)
        labelTitle.setGeometry(QtCore.QRect(37, 37, 75, 75))

        labelTitle.setPixmap(pixmap)
        labelTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.layout().addWidget(labelTitle)

    #Function to change the window title
    def set_title(self, title):
        self.setWindowTitle(title)

    # class InformationBox(QMessageBox):
#     def __init__(self):
#         super().__init__()
#         self.setIcon(QMessageBox.Icon.Information)
#         self.setWindowIcon(QIcon('images/icons/logo.png'))
#
#         self.setStyleSheet("QMessageBox {background-image: url(images/MC2PDB bg.png);}")

    # def show_message(self, title, message):
    #     self.setWindowTitle(title)
    #     self.setText(message)
    #     self.exec()


#Quick dialog window that says "Nothing selected!"
class NothingSelected(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nothing Selected")
        self.resize(150, 75)
        self.label = QLabel(self)
        self.label.setText("Nothing selected!")
        self.label.move(25, 10)
        self.label.adjustSize()
        self.okayButton = QPushButton("Okay", self)
        self.okayButton.move(25, 30)
        self.okayButton.clicked.connect(self.close)

#A new popup menu that will show several text options in a list. It has two buttons: "Okay" and "Cancel"
class IncludedPDBPopup(QMainWindow):
    selected = pyqtSignal(str)
    def ListAvailableModels(self):
        cwd = os.getcwd()
        #available = os.listdir(os.path.join(cwd, "presets"))

        available = os.listdir(get_presets_path())
        listOutput = ['-none-']
        for file in available:
            if file.endswith(".pdb"):
                # remove the .pdb
                file = file[:-4]
                listOutput.append(file)
            else:
                print(file)
        return listOutput
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select one included PDB model")
        self.resize(350, 200)
        os.chdir(get_images_path())

        self.setWindowIcon(QIcon('images/icons/logo.png'))

        # Set background image
        self.setStyleSheet("background-image: url(images/MC2PDB bg.png);")

        #Create a selectable list where user can select one item
        self.listWidget = QListWidget(self)
        self.listWidget.setStyleSheet("QListWidget::item { background-color: rgba(255, 255, 255, 150); }")
        self.listWidget.setGeometry(QtCore.QRect(50, 10, 250, 130))
        self.listWidget.setObjectName("listWidget")

        elementsList = self.ListAvailableModels()
        #populate the listWidget with elements of elementsList
        self.listWidget.addItems(elementsList)

        #set default selection to "NA"
        self.listWidget.setCurrentRow(0)
        #change font size of list
        font = QtGui.QFont()
        font.setPointSize(11)
        self.listWidget.setFont(font)

        #Create button named "okay"
        self.okayButton = QPushButton("Okay", self)
        self.okayButton.move(60, 150)
        self.okayButton.setStyleSheet("background-color: rgba(255, 255, 255, 255);")

        #Create button named "Cancel"
        self.cancelButton = QPushButton("Cancel", self)
        self.cancelButton.move(185, 150)
        self.cancelButton.setStyleSheet("background-color: rgba(255, 255, 255, 255);")

        self.okayButton.raise_()
        self.cancelButton.raise_()

        self.okayButton.clicked.connect(self.getSelected)
        self.cancelButton.clicked.connect(self.cancelSelected)

    #save the output of the selected item
    def getSelected(self):
        selected_text = self.listWidget.currentItem().text()

        if selected_text == '-none-':
            self.nothing = NothingSelected()
            self.nothing.show()
        else:
            preset_file = os.path.join("presets", selected_text + ".pdb")
            # check if the model is small enough for minecraft
            if not pdbm.check_model_size(preset_file, world_max=320):
                self.info_box = InformationBox()  # Keep reference!
                self.info_box.set_text(f"The chosen model is too large for Minecraft.")
                self.info_box.set_title("Model too large!")
                self.info_box.set_icon("images/icons/icon_bad.png")
                self.info_box.show()
            else:
                size_factor = pdbm.check_max_size(preset_file, world_max=320)
                print("Multiplier is: ", size_factor)  # For debugging
                size_factor = str(round(size_factor, 2))
                self.info_box = InformationBox()  # Keep reference!
                self.info_box.set_text(f"The suggested maximum protein scale is: {size_factor}x\n\nSet 'Protein Scale' below this for best results.")
                self.info_box.set_title("Maximum scale")
                self.info_box.set_icon("images/icons/icon_info.png")
                self.info_box.show()
            self.selected.emit(selected_text)
            self.close()
            return selected_text
    def cancelSelected(self):
        self.close()

#A new popup that will show the system file explorer starting from a specific path
class FileExplorerPopup(QMainWindow):
    def __init__(self):
        super().__init__()
        message_box = QMessageBox()
        message_box.setWindowTitle("Please wait")
        message_box.setText("Calculating model size...")
        self.setWindowIcon(QIcon('images/icons/unknown_icon.png'))
        message_box.setStandardButtons(QMessageBox.StandardButton.NoButton)  # No buttons
        message_box.show()
        # Allow both .pdb and .cif files
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select PDB or mmCIF file",
            "",
            "Protein Databank files (*.pdb *.cif);;PDB files (*.pdb);;mmCIF files (*.cif);;All files (*)"
        )
        if file_name:
            try:
                # Try to load the file using StructureData to catch errors early
                from PDB2MC.structure_data import StructureData
                if file_name.lower().endswith('.cif'):
                    StructureData.from_mmcif(file_name)
                else:
                    StructureData.from_pdb(file_name)
            except Exception as e:
                QMessageBox.critical(self, "File Error", f"Failed to load file:\n{e}")
                file_name = None
        else:
            message_box.close()
            QMessageBox.warning(self, "No file selected", f"Please select a file.")
        self.selected_file = file_name



class MinecraftPopup(QMainWindow):
    def __init__(self):
        super().__init__()
        home_dir = os.path.expanduser("~")
        wd = os.path.join(home_dir, r"AppData\Roaming\.minecraft\saves")
        good_dir = False
        self.selected_directory = None
        while not good_dir:
            save_path = QFileDialog.getExistingDirectory(self, "Select Directory", wd)
            # check if save_path has structure .minecraft/saves/<save_name>
            if save_path:
                if os.path.basename(os.path.dirname(save_path)) == "saves":
                    good_dir = True
                else:
                    QMessageBox.warning(self, "Invalid directory", "Please select a valid Minecraft save directory.")
            else:
                return
        directory_path = os.path.join(save_path, "datapacks/mcPDB/data/protein/functions")

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        # check for pack.mcmeta in the /datapacks/mcPDB folder and if not copy it from the python directory
        if not os.path.isfile(os.path.join(save_path, "datapacks/mcPDB/pack.mcmeta")):
            pack_mcmeta_path = pkg_resources.resource_filename('PDB2MC', 'pack.mcmeta')
            copyfile(pack_mcmeta_path, os.path.join(save_path, "datapacks/mcPDB/pack.mcmeta"))

        else:
            if not os.path.isfile(os.path.join(save_path, "datapacks/mcPDB/pack.mcmeta")):
                copyfile("../PDB2MC/pack.mcmeta", os.path.join(save_path, "datapacks/mcPDB/pack.mcmeta"))

        if directory_path:
            self.selected_directory = directory_path

class SequenceSelectorPopup(QMainWindow):
    """
    Popup window for selecting and annotating sequence regions from a StructureData object.
    Allows selection of ranges per chain, and assignment of block type, hide, or add chain options.
    """
    # Add a local three_to_one conversion table
    _three_to_one_dict = {
        'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D', 'CYS': 'C',
        'GLN': 'Q', 'GLU': 'E', 'GLY': 'G', 'HIS': 'H', 'ILE': 'I',
        'LEU': 'L', 'LYS': 'K', 'MET': 'M', 'PHE': 'F', 'PRO': 'P',
        'SER': 'S', 'THR': 'T', 'TRP': 'W', 'TYR': 'Y', 'VAL': 'V',
        # DNA/RNA nucleotides
        'A': 'A', 'C': 'C', 'G': 'G', 'T': 'T', 'U': 'U',
        'DA': 'A', 'DC': 'C', 'DG': 'G', 'DT': 'T', 'DU': 'U',
        # Common alternate codes
        'ASX': 'B', 'GLX': 'Z', 'UNK': 'X'
    }

    @staticmethod
    def three_to_one(resname):
        resname = str(resname).upper()
        return SequenceSelectorPopup._three_to_one_dict.get(resname, '?')

    def __init__(self, structure_data):
        super().__init__()
        self.setWindowTitle("Sequence Selector")
        os.chdir(get_images_path())
        self.setWindowIcon(QIcon('images/icons/logo.png'))
        self.setStyleSheet("background-image: url(images/MC2PDB bg.png);")
        self.resize(700, 400)

        self.structure_data = structure_data
        self.selections = {}  # {chain: [(start, end, [options])]}
        self.chain_widgets = {}  # {chain: QListWidget}
        self.modified_items = {}  # {chain: dict(resnum: set(options))}

        # Title label
        self.title_label = QLabel("Select sequence regions for annotation", self)
        self.title_label.setFont(QFont("Arial", 14))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setGeometry(0, 10, 700, 30)

        # Dynamic area for chains
        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setGeometry(20, 50, 660, 250)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_content)

        # Use StructureData.sequences for chain display
        for chain_id, seq_info in self.structure_data.sequences.items():
            chain_label = QLabel(f"Chain {chain_id}:", self.scroll_content)
            chain_label.setFont(QFont("Arial", 12))
            self.scroll_layout.addWidget(chain_label)

            list_widget = QListWidget(self.scroll_content)
            list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
            font = QFont("Consolas", 11)
            list_widget.setFont(font)
            list_widget.setFlow(QListWidget.Flow.LeftToRight)
            list_widget.setWrapping(True)
            list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
            list_widget.setMinimumHeight(40)
            list_widget.setMaximumHeight(60)
            # Show every single-letter code, but only show index if divisible by 5
            for resid, code in seq_info:
                label = f"{code}"
                if int(resid) % 5 == 0:
                    label = f"{code}\n{resid}"
                item = QtWidgets.QListWidgetItem(label)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, str(resid))  # Store resid for lookup
                list_widget.addItem(item)
            self.scroll_layout.addWidget(list_widget)
            self.chain_widgets[chain_id] = list_widget
            self.modified_items[chain_id] = {}

        self.scroll_area.setWidget(self.scroll_content)

        # Option buttons
        self.block_btn = QPushButton("Assign Block Type", self)
        self.block_btn.setGeometry(100, 320, 140, 35)
        self.block_btn.clicked.connect(self.assign_block_type)

        self.hide_btn = QPushButton("Hide Selection", self)
        self.hide_btn.setGeometry(260, 320, 120, 35)
        self.hide_btn.clicked.connect(self.assign_hide)

        self.add_chain_btn = QPushButton("Add Chain", self)
        self.add_chain_btn.setGeometry(400, 320, 120, 35)
        self.add_chain_btn.clicked.connect(self.assign_add_chain)

        self.okay_btn = QPushButton("Okay", self)
        self.okay_btn.setGeometry(550, 320, 100, 35)
        self.okay_btn.clicked.connect(self.finish_selection)

        # Store options per selection: {chain: {resnum: [options]}}
        self.options = {}

    def assign_block_type(self):
        chain, selected = self._get_current_selection()
        if not selected:
            QMessageBox.warning(self, "No selection", "Please select a sequence region.")
            return
        block_type, ok = QtWidgets.QInputDialog.getText(self, "Block Type", "Enter block type:")
        if ok and block_type:
            for resnum in selected:
                self._add_option(chain, resnum, f"block:{block_type}")
                self._mark_modified(chain, resnum, "block")
            self._update_item_colors(chain)

    def assign_hide(self):
        chain, selected = self._get_current_selection()
        if not selected:
            QMessageBox.warning(self, "No selection", "Please select a sequence region.")
            return
        for resnum in selected:
            self._add_option(chain, resnum, "hide")
            self._mark_modified(chain, resnum, "hide")
        self._update_item_colors(chain)

    def assign_add_chain(self):
        chain, selected = self._get_current_selection()
        if not selected:
            QMessageBox.warning(self, "No selection", "Please select a sequence region.")
            return
        for resnum in selected:
            self._add_option(chain, resnum, "add_chain")
            self._mark_modified(chain, resnum, "add_chain")
        self._update_item_colors(chain)

    def _get_current_selection(self):
        for chain_id, widget in self.chain_widgets.items():
            if widget.hasFocus():
                selected_items = widget.selectedItems()
                resnums = [item.data(QtCore.Qt.ItemDataRole.UserRole) for item in selected_items]
                return chain_id, resnums
        for chain_id, widget in self.chain_widgets.items():
            selected_items = widget.selectedItems()
            if selected_items:
                resnums = [item.data(QtCore.Qt.ItemDataRole.UserRole) for item in selected_items]
                return chain_id, resnums
        return None, []

    def _add_option(self, chain, resnum, option):
        if chain not in self.options:
            self.options[chain] = {}
        if resnum not in self.options[chain]:
            self.options[chain][resnum] = []
        if option not in self.options[chain][resnum]:
            self.options[chain][resnum].append(option)

    def _mark_modified(self, chain, resnum, option_type):
        # Track all option types for each residue
        if chain not in self.modified_items:
            self.modified_items[chain] = {}
        if resnum not in self.modified_items[chain]:
            self.modified_items[chain][resnum] = set()
        self.modified_items[chain][resnum].add(option_type)

    def _update_item_colors(self, chain):
        widget = self.chain_widgets.get(chain)
        if not widget:
            return
        for i in range(widget.count()):
            item = widget.item(i)
            resnum = item.data(QtCore.Qt.ItemDataRole.UserRole)
            types = self.modified_items.get(chain, {}).get(resnum, set())
            # Color logic:
            # "hide": dark grey bg, black text (takes precedence)
            # "block": blue bg, white text
            # "add_chain": red bg, white text
            # "block"+"add_chain": purple bg, white text
            # If both "hide" and others: always dark grey/black
            if "hide" in types:
                item.setForeground(QtGui.QColor("black"))
                item.setBackground(QtGui.QColor(60, 60, 60))
            elif "block" in types and "add_chain" in types:
                item.setForeground(QtGui.QColor("white"))
                item.setBackground(QtGui.QColor(128, 0, 128))  # purple
            elif "block" in types:
                item.setForeground(QtGui.QColor("white"))
                item.setBackground(QtGui.QColor(30, 144, 255))  # blue
            elif "add_chain" in types:
                item.setForeground(QtGui.QColor("white"))
                item.setBackground(QtGui.QColor(220, 20, 60))  # red
            else:
                item.setForeground(QtGui.QColor("black"))
                item.setBackground(QtGui.QColor(255, 255, 255))

    def finish_selection(self):
        print("Sequence selection output:")
        print(self.options)
        self.close()

def get_images_path():
    if getattr(sys, 'frozen', False):
        # The program is running as a compiled executable
        images_dir = pkg_resources.resource_filename('UI', 'images')
        images_dir = os.path.join(images_dir, '..')
        return images_dir
    else:
        # The program is running as a Python script or it's installed in the Python environment
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the UI/images directory
        images_dir = os.path.join(current_dir, '..', 'UI')
        return images_dir

def get_presets_path():
    if getattr(sys, 'frozen', False):
        # The program is running as a compiled executable
        preset_dir = pkg_resources.resource_filename('UI', 'presets')
        preset_dir = os.path.join(preset_dir)
        return preset_dir
    else:
        # The program is running as a Python script or it's installed in the Python environment
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the UI/images directory
        preset_dir = os.path.join(current_dir, '..', 'UI', 'presets')
        return preset_dir
