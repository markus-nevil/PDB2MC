import os
from PyQt6.QtWidgets import QFileDialog, QApplication, QMainWindow
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6 import QtCore, QtGui, QtWidgets

import utilUI
import xrayWindow
import space_fillingWindow
import ribbonWindow
import skeletonWindow
import amino_acidsWindow
import customWindow

from utilUI import IncludedPDBPopup, MinecraftPopup, FileExplorerPopup

class UtilityWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_pdb_file = None
        self.user_minecraft_save = None
        self.setWindowTitle("Utilities")
        self.setWindowIcon(QIcon('../images/icons/logo.png'))

        self.resize(450, 411)
        # Set style to Fusion
        #self.setStyle("Fusion")
        self.centralwidget = QtWidgets.QWidget(parent=self)
        self.centralwidget.setObjectName("centralwidget")
        self.switchModeLabel = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        font.setKerning(True)
        self.switchModeLabel.setFont(font)
        self.switchModeLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.switchModeLabel.setObjectName("switchModeLabel")
        self.vSepLine = QtWidgets.QFrame(parent=self.centralwidget)

        self.vSepLine.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.vSepLine.setLineWidth(2)
        self.vSepLine.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.vSepLine.setObjectName("vSepLine")
        self.CustomMode = QtWidgets.QPushButton(parent=self.centralwidget)

        font = QtGui.QFont()
        font.setPointSize(11)
        self.CustomMode.setFont(font)
        self.CustomMode.setObjectName("CustomMode")

        self.SkeletonMode = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.SkeletonMode.setFont(font)
        self.SkeletonMode.setObjectName("SkeletonMode")

        self.XRayMode = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.XRayMode.setFont(font)
        self.XRayMode.setObjectName("XRayMode")
        self.SpaceFillingMode = QtWidgets.QPushButton(parent=self.centralwidget)

        font = QtGui.QFont()
        font.setPointSize(8)
        self.SpaceFillingMode.setFont(font)
        self.SpaceFillingMode.setObjectName("SpaceFillingMode")
        self.AminoAcidMode = QtWidgets.QPushButton(parent=self.centralwidget)

        font = QtGui.QFont()
        font.setPointSize(8)
        self.AminoAcidMode.setFont(font)
        self.AminoAcidMode.setObjectName("AminoAcidMode")
        self.RibbonMode = QtWidgets.QPushButton(parent=self.centralwidget)

        font = QtGui.QFont()
        font.setPointSize(11)
        self.RibbonMode.setFont(font)
        self.RibbonMode.setObjectName("RibbonMode")
        self.github = QtWidgets.QPushButton(parent=self.centralwidget)

        font = QtGui.QFont()
        font.setPointSize(10)
        self.github.setFont(font)
        self.github.setObjectName("github")
        self.help = QtWidgets.QPushButton(parent=self.centralwidget)

        font = QtGui.QFont()
        font.setPointSize(10)
        self.help.setFont(font)
        self.help.setObjectName("help")
        self.rcsbButton = QtWidgets.QPushButton(parent=self.centralwidget)

        font = QtGui.QFont()
        font.setPointSize(9)
        self.rcsbButton.setFont(font)
        self.rcsbButton.setObjectName("rcsbButton")

        self.mc2pdbLabel = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setUnderline(False)
        font.setWeight(50)
        font.setKerning(True)
        self.mc2pdbLabel.setFont(font)
        self.mc2pdbLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.mc2pdbLabel.setObjectName("mc2pdbLabel")

        self.pdbDatabaseLabel = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setUnderline(False)
        font.setWeight(50)
        font.setKerning(True)
        self.pdbDatabaseLabel.setFont(font)
        self.pdbDatabaseLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.pdbDatabaseLabel.setObjectName("pdbDatabaseLabel")
        self.modeInfoHLine = QtWidgets.QFrame(parent=self.centralwidget)

        self.modeInfoHLine.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.modeInfoHLine.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.modeInfoHLine.setObjectName("modeInfoHLine")
        self.infoDatabaseHLine = QtWidgets.QFrame(parent=self.centralwidget)

        self.infoDatabaseHLine.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.infoDatabaseHLine.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.infoDatabaseHLine.setObjectName("infoDatabaseHLine")
        self.bg = QtWidgets.QLabel(parent=self.centralwidget)

        self.removeFunctionFiles = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.removeFunctionFiles.setFont(font)
        self.removeFunctionFiles.setObjectName("removeFunctionFiles")

        self.openFunctionDir = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.openFunctionDir.setFont(font)
        self.openFunctionDir.setText("Open Minecraft Function Directory")
        self.openFunctionDir.setObjectName("removeFunctionFiles")

        self.openIncludedDir = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.openIncludedDir.setFont(font)
        self.openIncludedDir.setText("Open 'Presets' Directory")
        self.openIncludedDir.setObjectName("removeFunctionFiles")

        font = QtGui.QFont()
        font.setPointSize(7)
        self.bg.setFont(font)
        self.bg.setText("")
        self.bg.setPixmap(QtGui.QPixmap("../images/MC2PDB bg.png"))
        self.bg.setScaledContents(True)
        self.bg.setObjectName("bg")

        self.bg.setGeometry(QtCore.QRect(-90, -50, 781, 461))

        self.switchModeLabel.setGeometry(QtCore.QRect(0, 0, 101, 31))
        self.CustomMode.setGeometry(QtCore.QRect(10, 30, 75, 23))
        self.SkeletonMode.setGeometry(QtCore.QRect(10, 60, 75, 23))
        self.XRayMode.setGeometry(QtCore.QRect(10, 90, 75, 23))
        self.SpaceFillingMode.setGeometry(QtCore.QRect(10, 120, 75, 23))
        self.RibbonMode.setGeometry(QtCore.QRect(10, 150, 75, 23))
        self.AminoAcidMode.setGeometry(QtCore.QRect(10, 180, 75, 23))
        self.modeInfoHLine.setGeometry(QtCore.QRect(10, 210, 71, 16))

        self.mc2pdbLabel.setGeometry(QtCore.QRect(10, 220, 71, 21))
        self.help.setGeometry(QtCore.QRect(10, 250, 75, 31))
        self.github.setGeometry(QtCore.QRect(10, 290, 75, 31))
        self.infoDatabaseHLine.setGeometry(QtCore.QRect(10, 320, 71, 16))
        self.pdbDatabaseLabel.setGeometry(QtCore.QRect(0, 330, 91, 21))
        self.rcsbButton.setGeometry(QtCore.QRect(10, 360, 75, 31))

        self.vSepLine.setGeometry(QtCore.QRect(90, 0, 20, 431))

        self.removeFunctionFiles.setGeometry(QtCore.QRect(150, 20, 240, 50))
        self.openFunctionDir.setGeometry(QtCore.QRect(150, 80, 240, 50))
        self.openIncludedDir.setGeometry(QtCore.QRect(150, 140, 240, 50))

        self.bg.raise_()
        self.switchModeLabel.raise_()
        self.vSepLine.raise_()
        self.CustomMode.raise_()
        self.SkeletonMode.raise_()
        self.XRayMode.raise_()
        self.SpaceFillingMode.raise_()
        self.AminoAcidMode.raise_()
        self.RibbonMode.raise_()
        self.github.raise_()
        self.help.raise_()
        self.rcsbButton.raise_()
        self.mc2pdbLabel.raise_()
        self.pdbDatabaseLabel.raise_()
        self.modeInfoHLine.raise_()
        self.infoDatabaseHLine.raise_()
        self.setCentralWidget(self.centralwidget)
        self.removeFunctionFiles.raise_()
        self.openIncludedDir.raise_()
        self.openFunctionDir.raise_()

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

        # Connect the QPushButton's clicked signal to a slot method
        self.help.clicked.connect(self.handle_help_button)
        self.rcsbButton.clicked.connect(self.handle_rscb_button)
        self.github.clicked.connect(self.handle_github_button)
        self.CustomMode.clicked.connect(self.handle_custom_mode)
        self.SkeletonMode.clicked.connect(self.handle_skeleton_mode)
        self.XRayMode.clicked.connect(self.handle_xray_mode)
        self.SpaceFillingMode.clicked.connect(self.handle_space_filling_mode)
        self.AminoAcidMode.clicked.connect(self.handle_amino_acid_mode)
        self.RibbonMode.clicked.connect(self.handle_ribbon_mode)
        self.removeFunctionFiles.clicked.connect(self.handle_remove_function_files)
        self.openFunctionDir.clicked.connect(self.handle_open_function_dir)
        self.openIncludedDir.clicked.connect(self.handle_open_included_dir)

    def handle_remove_function_files(self):
        self.selectMinecraft = MinecraftPopup()
        if self.selectMinecraft.selected_directory is None:
            return
        self.user_minecraft_save = self.selectMinecraft.selected_directory

        #Take the directory and remove any files that end in .mcfunction
        for filename in os.listdir(self.user_minecraft_save):
            if filename.endswith(".mcfunction"):
                #Open the file to see if it has the word 'setblock'. if so delete it
                with open(os.path.join(self.user_minecraft_save, filename), 'r') as f:
                    if "setblock" in f.read():
                        os.remove(os.path.join(self.user_minecraft_save, filename))
                        print(f"Removed {filename}")
            else:
                continue

    def handle_open_function_dir(self):
        self.selectMinecraft = MinecraftPopup()
        if self.selectMinecraft.selected_directory is None:
            return
        self.user_minecraft_save = self.selectMinecraft.selected_directory

        self.explore = FileExplorerPopup(self.user_minecraft_save)

    def handle_open_included_dir(self):
        print("Open included directory button clicked")
        # Get the directory of the current Python file
        start_dir = os.path.dirname(os.path.abspath(__file__))
        start_dir = os.path.join(start_dir, "presets")

        self.explore = FileExplorerPopup(start_dir)

    # Slot methods to handle QPushButton clicks
    def handle_select_pdb_file_button(self):
        print("Selecting PDB file")
        self.selectPDB = FileExplorerPopup()
        self.user_pdb_file = self.selectPDB.selected_file
        print(f"The user has this file: {self.user_pdb_file}")

    def handle_included_pdb_button(self):
        print("Included PDB button clicked")
        self.includedPDB = IncludedPDBPopup()
        self.includedPDB.show()
        self.includedPDB.selected.connect(self.save_selected_text)

    def show_information_box(self, title_text, text, icon_path):
        self.info_box = utilUI.InformationBox()
        self.info_box.set_text(text)
        self.info_box.set_title(title_text)
        self.info_box.set_icon(icon_path)
        self.info_box.show()

    def handle_github_button(self):
        print("Github button clicked")
        QDesktopServices.openUrl(QtCore.QUrl("https://github.com/markus-nevil/mcpdb"))

    def handle_help_button(self):
        print("Help button clicked")
        QDesktopServices.openUrl(QtCore.QUrl("https://github.com/markus-nevil/mcpdb/blob/main/README.md"))

    def handle_rscb_button(self):
        print("RSCB button clicked")
        QDesktopServices.openUrl(QtCore.QUrl("https://www.rcsb.org/"))

    def handle_custom_mode(self):
        print("Custom mode button clicked")
        self.Custom = customWindow.CustomWindow()
        self.Custom.show()
        self.hide()

    def handle_skeleton_mode(self):
        print("Skeleton mode button clicked")
        self.Skeleton = skeletonWindow.SkeletonWindow()
        self.Skeleton.show()
        self.hide()

    def handle_xray_mode(self):
        print("X-Ray mode button clicked")
        self.Xray = xrayWindow.XrayWindow()
        self.Xray.show()
        self.hide()

    def handle_space_filling_mode(self):
        print("Space Filling mode button clicked")
        self.SpaceFilling = space_fillingWindow.spWindow()
        self.SpaceFilling.show()
        self.hide()

    def handle_amino_acid_mode(self):
        print("Amino Acid mode button clicked")
        self.AminoAcid = amino_acidsWindow.AAWindow()
        self.AminoAcid.show()
        self.hide()

    def handle_ribbon_mode(self):
        print("Ribbon mode button clicked")
        self.Ribbon = ribbonWindow.RibbonWindow()
        self.Ribbon.show()
        self.hide()

    def retranslateUi(self, UtilityWindow):
        _translate = QtCore.QCoreApplication.translate
        #UtilityWindow.setWindowTitle(_translate("UtilityWindow", "MainWindow"))
        self.switchModeLabel.setText(_translate("UtilityWindow", "Switch Mode"))
        self.CustomMode.setText(_translate("UtilityWindow", "Custom"))
        self.SkeletonMode.setText(_translate("UtilityWindow", "Skeleton"))
        self.XRayMode.setText(_translate("UtilityWindow", "X-Ray"))
        self.SpaceFillingMode.setText(_translate("UtilityWindow", "Space Filling"))
        self.AminoAcidMode.setText(_translate("UtilityWindow", "Amino Acids"))
        self.RibbonMode.setText(_translate("UtilityWindow", "Ribbon"))
        self.github.setText(_translate("UtilityWindow", "Github"))
        self.help.setText(_translate("UtilityWindow", "Help"))
        self.rcsbButton.setText(_translate("UtilityWindow", "RCSB.org"))
        self.mc2pdbLabel.setText(_translate("UtilityWindow", "PDB2MC"))
        self.pdbDatabaseLabel.setText(_translate("UtilityWindow", "PDB Database"))
        self.removeFunctionFiles.setText(_translate("UtilityWindow", "Remove Function Files"))

class FileExplorerPopup(QMainWindow):
    def __init__(self, start_dir):
        super().__init__()
        #Open a QFileDialog starting at the directory passed to this function
        file_name, _ = QFileDialog.getOpenFileName(self, "File Explorer", start_dir, "")
        if file_name:
            pass

if __name__ == "__main__":
    app = QApplication([])
    main_window = UtilityWindow()
    main_window.show()
    app.exec()