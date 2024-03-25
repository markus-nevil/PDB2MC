import os
from PyQt6.QtWidgets import QFileDialog, QApplication, QMainWindow
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6 import QtCore, QtGui, QtWidgets

from UI.utilities import InformationBox, IncludedPDBPopup, MinecraftPopup, FileExplorerPopup
from PDB2MC import minecraft_functions as mcf


class ToolWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_pdb_file = None
        self.user_minecraft_save = None
        current_directory = os.path.basename(os.getcwd())
        if current_directory == "PDB2MC":
            mcpdb_directory = os.path.join(os.getcwd(), ".." "UI")
            os.chdir(mcpdb_directory)

        self.setWindowTitle("Utilities")
        self.setWindowIcon(QIcon('images/icons/logo.png'))

        self.resize(450, 411)
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

        self.movePreset = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.movePreset.setFont(font)
        self.movePreset.setText("Copy Blank World to Minecraft")
        self.movePreset.setObjectName("movePreset")

        font = QtGui.QFont()
        font.setPointSize(7)
        self.bg.setFont(font)
        self.bg.setText("")
        self.bg.setPixmap(QtGui.QPixmap("images/MC2PDB bg.png"))
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
        self.movePreset.setGeometry(QtCore.QRect(150, 200, 240, 50))

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
        self.movePreset.raise_()

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
        self.movePreset.clicked.connect(self.handle_move_preset_button)


    def handle_remove_function_files(self):
        self.selectMinecraft = MinecraftPopup()
        if self.selectMinecraft.selected_directory is None:
            return
        self.user_minecraft_save = self.selectMinecraft.selected_directory

        #make an empty list to store paths to files that will be deleted
        files_to_delete = []

        # Take the directory and remove any files that end in .mcfunction
        for filename in os.listdir(self.user_minecraft_save):
            if filename.endswith(".mcfunction"):
                # Open the file to see if it has the word 'setblock'. if so delete it
                with open(os.path.join(self.user_minecraft_save, filename), 'r') as f:
                    if "setblock" in f.read():
                        files_to_delete.append(os.path.join(self.user_minecraft_save, filename))
            else:
                continue

        for file in files_to_delete:
            os.remove(file)

    def handle_move_preset_button(self):
        home_dir = os.path.expanduser("~")
        wd = os.path.join(home_dir, "AppData\Roaming\.minecraft\saves")
        mcf.copy_blank_world(wd)
        self.show_information_box(title_text=f"Blank World Copied!",
                                  text=f"The blank world will now be found in your saves.\nRun again to overwrite with this world.",
                                  icon_path="images/icons/icon_good.png")

        #self.user_minecraft_save = self.selectMinecraft.selected_directory


    def handle_open_function_dir(self):
        self.selectMinecraft = MinecraftPopup()
        if self.selectMinecraft.selected_directory is None:
            return
        self.user_minecraft_save = self.selectMinecraft.selected_directory

        self.explore = FileExplorerPopup(self.user_minecraft_save)

    def handle_open_included_dir(self):
        # Get the directory of the current Python file
        start_dir = os.path.dirname(os.path.abspath(__file__))
        start_dir = os.path.join(start_dir, "presets")

        self.explore = FileExplorerPopup(start_dir)

    # Slot methods to handle QPushButton clicks
    def handle_select_pdb_file_button(self):
        self.selectPDB = FileExplorerPopup()
        self.user_pdb_file = self.selectPDB.selected_file

    def handle_included_pdb_button(self):
        self.includedPDB = IncludedPDBPopup()
        self.includedPDB.show()
        self.includedPDB.selected.connect(self.save_selected_text)

    def show_information_box(self, title_text, text, icon_path):
        self.info_box = InformationBox()
        self.info_box.set_text(text)
        self.info_box.set_title(title_text)
        self.info_box.set_icon(icon_path)
        self.info_box.show()

    def handle_github_button(self):
        QDesktopServices.openUrl(QtCore.QUrl("https://github.com/markus-nevil/mcpdb"))

    def handle_help_button(self):
        from UI.help_window import HelpWindow
        help_window = HelpWindow.instance()
        if help_window.isVisible():
            # If a HelpWindow already exists, bring it to the front
            help_window.raise_()
            help_window.activateWindow()
        else:
            # If no HelpWindow exists, create a new one
            help_window.show()

        # Move the HelpWindow to the center of the current screen
        frame_geometry = help_window.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        help_window.move(frame_geometry.topLeft())

    def handle_rscb_button(self):
        QDesktopServices.openUrl(QtCore.QUrl("https://www.rcsb.org/"))

    def handle_custom_mode(self):
        try:
            from UI.custom_window import CustomWindow
            self.Custom = CustomWindow()
            self.Custom.show()
            self.hide()
        except Exception as e:
            print(f"Error in handle_custom_mode: {e}")

    def handle_skeleton_mode(self):
        try:
            from UI.skeleton_window import SkeletonWindow
            self.Skeleton = SkeletonWindow()
            self.Skeleton.show()
            self.hide()
        except Exception as e:
            print(f"Error in handle_skeleton_mode: {e}")

    def handle_xray_mode(self):
        try:
            from UI.xray_window import XrayWindow
            self.Xray = XrayWindow()
            self.Xray.show()
            self.hide()
        except Exception as e:
            print(f"Error in handle_xray_mode: {e}")

    def handle_space_filling_mode(self):
        try:
            from UI.space_filling_window import spWindow
            self.SpaceFilling = spWindow()
            self.SpaceFilling.show()
            self.hide()
        except Exception as e:
            print(f"Error in handle_space_filling_mode: {e}")

    def handle_amino_acid_mode(self):
        try:
            from UI.amino_acids_window import AAWindow
            self.AminoAcid = AAWindow()
            self.AminoAcid.show()
            self.hide()
        except Exception as e:
            print(f"Error in handle_amino_acid_mode: {e}")

    def handle_ribbon_mode(self):
        try:
            from UI.ribbon_window import RibbonWindow
            self.Ribbon = RibbonWindow()
            self.Ribbon.show()
            self.hide()
        except Exception as e:
            print(f"Error in handle_ribbon_mode: {e}")

    def retranslateUi(self, ToolWindow):
        _translate = QtCore.QCoreApplication.translate
        self.switchModeLabel.setText(_translate("ToolWindow", "Switch Mode"))
        self.CustomMode.setText(_translate("ToolWindow", "Custom"))
        self.SkeletonMode.setText(_translate("ToolWindow", "Skeleton"))
        self.XRayMode.setText(_translate("ToolWindow", "X-Ray"))
        self.SpaceFillingMode.setText(_translate("ToolWindow", "Space Filling"))
        self.AminoAcidMode.setText(_translate("ToolWindow", "Amino Acids"))
        self.RibbonMode.setText(_translate("ToolWindow", "Ribbon"))
        self.github.setText(_translate("ToolWindow", "Github"))
        self.help.setText(_translate("ToolWindow", "Help"))
        self.rcsbButton.setText(_translate("ToolWindow", "RCSB.org"))
        self.mc2pdbLabel.setText(_translate("ToolWindow", "PDB2MC"))
        self.pdbDatabaseLabel.setText(_translate("ToolWindow", "PDB Database"))
        self.removeFunctionFiles.setText(_translate("ToolWindow", "Remove Function Files"))


class FileExplorerPopup(QMainWindow):
    def __init__(self, start_dir):
        super().__init__()
        # Open a QFileDialog starting at the directory passed to this function
        file_name, _ = QFileDialog.getOpenFileName(self, "File Explorer", start_dir, "")
        if file_name:
            pass


if __name__ == "__main__":
    app = QApplication([])
    main_window = ToolWindow()
    main_window.show()
    app.exec()
