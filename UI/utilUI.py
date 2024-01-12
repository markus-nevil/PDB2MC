import os
from shutil import copyfile
from PyQt6.QtWidgets import QFileDialog, QApplication, QListWidget, QPushButton, QMainWindow, QMessageBox, QLabel
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6 import QtCore, QtGui, QtWidgets

from PDB2MC import pdb_manipulation as pdbm


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
        self.setWindowIcon(QIcon('../images/icons/logo.png'))

        # Set background image
        self.setStyleSheet("background-image: url(images/MC2PDB bg.png);")
        self.resize(500, 150)

        labelTitle = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap("../images/icons/icon_info.png")
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
        self.setWindowIcon(QIcon('../images/icons/logo.png'))

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
            preset_file = os.path.join("../presets", selected_text + ".pdb")
            # check if the model is small enough for minecraft
            if not pdbm.check_model_size(preset_file, world_max=320):
                self.info_box = InformationBox()
                self.info_box.set_text(f"The chosen model is too large for Minecraft.")
                self.info_box.set_title("Model too large!")
                self.info_box.set_icon("images/icons/icon_bad.png")
                self.info_box.show()
                #QMessageBox.warning(self, "Too large", f"Model may be too large for Minecraft.")
            else:
                # Calculate the maximum protein scale factor
                size_factor = pdbm.check_max_size(preset_file, world_max=320)
                size_factor = str(round(size_factor, 2))
                self.info_box = InformationBox()
                self.info_box.set_text(f"The suggested maximum protein scale is: {size_factor}x\n\nSet 'Protein Scale' below this for best results.")
                self.info_box.set_title("Maximum scale")
                self.info_box.set_icon("images/icons/icon_info.png")
                self.info_box.show()

                #QMessageBox.information(self, "Maximum scale", f"The maximum protein scale is: {size_factor}x")
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
            copyfile("../PDB2MC/pack.mcmeta", os.path.join(save_path, "datapacks/mcPDB/pack.mcmeta"))

        if directory_path:
            self.selected_directory = directory_path



if __name__ == "__main__":
    app = QApplication([])
    main_window = InformationBox()
    main_window.set_text("Finished! \n Remember to take your stuff out of the\n minecraft yes okay good")
    main_window.set_icon("images/icons/icon_good.png")
    main_window.show()
    #app.exec()