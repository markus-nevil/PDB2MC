import os
from shutil import copyfile
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QApplication, QListWidget, QPushButton, QMainWindow, QMessageBox, QLabel, QVBoxLayout, QWidget, QStylePainter
from PyQt6.QtGui import QMovie, QPalette, QBrush, QPixmap, QDesktopServices,QIcon
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6 import QtCore, QtGui, QtWidgets
from variables import decorative_blocks
import pandas as pd

import pdb_manipulation as pdbm
import minecraft_functions as mcf

class MyComboBox(QtWidgets.QComboBox):
    focusOut = pyqtSignal()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focusOut.emit()


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
        available = os.listdir(os.path.join(cwd, "presets"))
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

        #Create a selectable list where user can select one item
        self.listWidget = QListWidget(self)
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

        #Create button named "Cancel"
        self.cancelButton = QPushButton("Cancel", self)
        self.cancelButton.move(185, 150)

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
                QMessageBox.warning(self, "Too large", f"Model may be too large for Minecraft.")
            else:
                # Calculate the maximum protein scale factor
                size_factor = pdbm.check_max_size(preset_file, world_max=320)
                size_factor = str(round(size_factor, 2))
                QMessageBox.information(self, "Maximum scale", f"The maximum protein scale is: {size_factor}x")
            self.selected.emit(selected_text)
            self.close()
            return selected_text
    def cancelSelected(self):
        print('close window')
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
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "Protein Databank files (*.pdb)")
        if file_name:
            # check if the model is small enough for minecraft
            if not pdbm.check_model_size(file_name, world_max=320):
                message_box.close()
                QMessageBox.warning(self, "Too large", f"Model may be too large for Minecraft.")
            else:
                # Calculate the maximum protein scale factor
                size_factor = pdbm.check_max_size(file_name, world_max=320)
                size_factor = str(round(size_factor, 2))
                message_box.close()
                QMessageBox.information(self, "Maximum scale", f"The maximum protein scale is: {size_factor}x")
        else:
            message_box.close()
            QMessageBox.warning(self, "No file selected", f"Please select a file.")
        self.selected_file = file_name



class MinecraftPopup(QMainWindow):
    def __init__(self):
        super().__init__()
        home_dir = os.path.expanduser("~")
        wd = os.path.join(home_dir, "AppData\Roaming\.minecraft\saves")
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
            copyfile("pack.mcmeta", os.path.join(save_path, "datapacks/mcPDB/pack.mcmeta"))

        if directory_path:
            self.selected_directory = directory_path

