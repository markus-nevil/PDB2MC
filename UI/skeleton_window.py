from PyQt6.QtWidgets import QApplication, QMainWindow, QCompleter, QDialog, QVBoxLayout, QLabel, QProgressBar, QMessageBox
from PyQt6.QtGui import QDesktopServices, QColor, QIcon, QPainter, QPixmap
from PyQt6 import QtCore, QtGui, QtWidgets
import os
from .utilities import InformationBox, MyComboBox,IncludedPDBPopup, MinecraftPopup, FileExplorerPopup, SequenceSelectorPopup, get_presets_path
from PDB2MC.variables import decorative_blocks, hex_dict
import pandas as pd
from PDB2MC import minecraft_functions as mcf, pdb_manipulation as pdbm, skeleton
import sys
import pkg_resources
from PyQt6.QtCore import QThread, pyqtSignal

class WorkerThread(QThread):
    finished = pyqtSignal(object)
    progress = pyqtSignal(int)

    def __init__(self, config_data, parent=None):
        super().__init__(parent)
        self.config_data = config_data

    def run(self):
        config_data = self.config_data
        pdb_file = config_data['pdb_file']

        try:
            # Use StructureData to read the structure file ONCE
            if pdb_file.lower().endswith('.cif'):
                structure = pdbm.StructureData.from_mmcif(pdb_file)
            else:
                structure = pdbm.StructureData.from_pdb(pdb_file)
            config_data['structure'] = structure  # Pass StructureData downstream

            pdb_name = structure.metadata.get('id', pdbm.get_pdb_code(pdb_file))
            self.progress.emit(10)

            # --- HETATM handling ---
            hetatom_df = None
            hetatm_bonds = None
            if config_data["show_hetatm"]:
                hetatom_df = None
                hetatm_bonds = None

            self.progress.emit(30)
            mc_dir = config_data['save_path']
            mcf.delete_old_files(mc_dir, pdb_name)

            try:
                skeleton.run_mode(
                    config_data,
                    pdb_name,
                    structure,
                    mc_dir,
                    hetatom_df,
                    hetatm_bonds
                )
                self.progress.emit(50)
            except Exception as e:
                self.finished.emit({"result": "error", "error": f"Error in skeleton.run_mode: {e}"})
                return

            mcf.finish_nbts(mc_dir, config_data, pdb_name)
            self.progress.emit(70)
            mcf.create_nbt_delete(pdb_name, mc_dir)
            self.progress.emit(85)
            mcf.finish_delete_nbts(mc_dir, pdb_name)
            self.progress.emit(100)
            lower = pdb_name.lower()
            self.finished.emit({"result": "done", "lower": lower})
        except Exception as e:
            self.finished.emit({"result": "error", "error": f"Fatal error in WorkerThread: {e}"})

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
        if value <= 10:
            self.status_label.setText("Reading and scaling PDB file...")
        elif value <= 30:
            self.status_label.setText("Processing atoms and bonds...")
        elif value <= 50:
            self.status_label.setText("Generating intermediate files...")
        elif value <= 70:
            self.status_label.setText("Generating Minecraft files...")
        elif value <= 85:
            self.status_label.setText("Finalizing output...")
        else:
            self.status_label.setText("Done!")

class SkeletonWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # current_directory = os.path.basename(os.getcwd())
        # if current_directory == "PDB2MC":
        #     mcpdb_directory = os.path.join(os.getcwd(), ".." "UI")
        #     os.chdir(mcpdb_directory)

        # Only change working directory for resource loading, not before file selection
        # os.chdir(get_images_path())  # <-- REMOVE this line from here

        self.user_pdb_file = None
        self.user_minecraft_save = None
        self.setWindowTitle("Skeleton Mode")
        # Set window icon and background after widgets are created
        os.chdir(get_images_path())
        self.setWindowIcon(QIcon('images/icons/logo.png'))
        self.resize(450, 431)
        self.centralwidget = QtWidgets.QWidget(parent=self)
        self.centralwidget.setObjectName("centralwidget")
        self.switchModeLabel = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(100)
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

        self.tools = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.tools.setFont(font)
        self.tools.setObjectName("tools")

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
        font.setPointSize(11)
        font.setBold(False)
        font.setUnderline(False)
        font.setWeight(100)
        font.setKerning(True)
        self.mc2pdbLabel.setFont(font)
        self.mc2pdbLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.mc2pdbLabel.setObjectName("mc2pdbLabel")
        self.pdbDatabaseLabel = QtWidgets.QLabel(parent=self.centralwidget)

        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(False)
        font.setUnderline(False)
        font.setWeight(100)
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

        font = QtGui.QFont()
        font.setPointSize(7)
        self.bg.setFont(font)
        self.bg.setText("")
        self.bg.setPixmap(QtGui.QPixmap("images/MC2PDB bg.png"))
        self.bg.setScaledContents(True)
        self.bg.setObjectName("bg")

        self.backboneColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.backboneColorLabel.setObjectName("backboneColorLabel")

        self.sidechainColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.sidechainColorLabel.setObjectName("sidechainColorLabel")

        self.otherColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.otherColorLabel.setObjectName("otherColorLabel")

        self.otherColorBox = MyComboBox(self.centralwidget)
        self.otherColorBox.setObjectName("otherColorBox")
        self.otherColorBox.setEditable(True)

        self.backboneColorBox = MyComboBox(self.centralwidget)
        self.backboneColorBox.setObjectName("backboneColorBox")
        self.backboneColorBox.setEditable(True)

        self.sidechainColorBox = MyComboBox(self.centralwidget)
        self.sidechainColorBox.setObjectName("sidechainColorBox")
        self.sidechainColorBox.setEditable(True)

        icon_dict = {
            "red_concrete": "icon2",
            "orange_concrete": "icon3",
            "yellow_concrete": "icon4",
            "lime_concrete": "icon5",
            "green_concrete": "icon6",
            "cyan_concrete": "icon7",
            "light_blue_concrete": "icon8",
            "blue_concrete": "icon9",
            "purple_concrete": "icon10",
            "magenta_concrete": "icon11",
            "pink_concrete": "icon12",
            "brown_concrete": "icon13",
            "black_concrete": "icon1",
            "gray_concrete": "icon14",
            "light_gray_concrete": "icon15",
            "white_concrete": "icon16",
            "red_glazed_terracotta": "icon17",
            "orange_glazed_terracotta": "icon18",
            "yellow_glazed_terracotta": "icon19",
            "lime_glazed_terracotta": "icon20",
            "green_glazed_terracotta": "icon21",
            "cyan_glazed_terracotta": "icon22",
            "light_blue_glazed_terracotta": "icon23",
            "blue_glazed_terracotta": "icon24",
            "purple_glazed_terracotta": "icon25",
            "magenta_glazed_terracotta": "icon26",
            "pink_glazed_terracotta": "icon27",
            "brown_glazed_terracotta": "icon28",
            "black_glazed_terracotta": "icon29",
            "gray_glazed_terracotta": "icon30",
            "light_gray_glazed_terracotta": "icon31",
            "white_glazed_terracotta": "icon32",
            "red_terracotta": "icon33",
            "orange_terracotta": "icon34",
            "yellow_terracotta": "icon35",
            "lime_terracotta": "icon36",
            "green_terracotta": "icon37",
            "cyan_terracotta": "icon38",
            "light_blue_terracotta": "icon39",
            "blue_terracotta": "icon40",
            "purple_terracotta": "icon41",
            "magenta_terracotta": "icon42",
            "pink_terracotta": "icon43",
            "brown_terracotta": "icon44",
            "black_terracotta": "icon45",
            "gray_terracotta": "icon46",
            "light_gray_terracotta": "icon47",
            "white_terracotta": "icon48",
            "red_wool": "icon49",
            "orange_wool": "icon50",
            "yellow_wool": "icon51",
            "lime_wool": "icon52",
            "green_wool": "icon53",
            "cyan_wool": "icon54",
            "light_blue_wool": "icon55",
            "blue_wool": "icon56",
            "purple_wool": "icon57",
            "magenta_wool": "icon58",
            "pink_wool": "icon59",
            "brown_wool": "icon60",
            "black_wool": "icon61",
            "gray_wool": "icon62",
            "light_gray_wool": "icon63",
            "white_wool": "icon64",
            "red_stained_glass": "icon2",
            "orange_stained_glass": "icon3",
            "yellow_stained_glass": "icon4",
            "lime_stained_glass": "icon5",
            "green_stained_glass": "icon6",
            "cyan_stained_glass": "icon7",
            "light_blue_stained_glass": "icon8",
            "blue_stained_glass": "icon9",
            "purple_stained_glass": "icon10",
            "magenta_stained_glass": "icon11",
            "pink_stained_glass": "icon12",
            "brown_stained_glass": "icon13",
            "black_stained_glass": "icon1",
            "gray_stained_glass": "icon14",
            "light_gray_stained_glass": "icon15",
            "white_stained_glass": "icon16"
        }

        color_boxes = [self.otherColorBox, self.sidechainColorBox, self.backboneColorBox]

        for color_box in color_boxes:
            for value, icon in icon_dict.items():
                color_box.addItem(create_icon(hex_dict[value]), value)
                #color_box.addItem(eval(icon), value)
        color_box.insertSeparator(16)
        color_box.insertSeparator(33)
        color_box.insertSeparator(50)
        color_box.insertSeparator(67)

        self.otherColorBox.setCurrentIndex(10)
        self.sidechainColorBox.setCurrentIndex(13)
        self.backboneColorBox.setCurrentIndex(13)

        otherCompleter = QCompleter(decorative_blocks)
        otherCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.otherColorBox.setCompleter(otherCompleter)
        sidechainCompleter = QCompleter(decorative_blocks)
        sidechainCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.sidechainColorBox.setCompleter(sidechainCompleter)
        backboneCompleter = QCompleter(decorative_blocks)
        backboneCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.backboneColorBox.setCompleter(backboneCompleter)

        self.aScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)

        self.aScaleLabel.setObjectName("aScaleLabel")
        self.otherMoleculeCheck = QtWidgets.QCheckBox(parent=self.centralwidget)

        self.otherMoleculeCheck.setChecked(True)
        self.otherMoleculeCheck.setObjectName("otherMoleculeCheck")
        self.otherMoleculeCheck.setToolTip("Check to show other non-protein, DNA, or RNA molecules.")
        self.aScaleSpinBox = QtWidgets.QDoubleSpinBox(parent=self.centralwidget)

        self.aScaleSpinBox.setDecimals(1)
        self.aScaleSpinBox.setMinimum(1.0)
        self.aScaleSpinBox.setMaximum(50.0)
        self.aScaleSpinBox.setSingleStep(0.5)
        self.aScaleSpinBox.setProperty("value", 1.5)
        self.aScaleSpinBox.setObjectName("aScaleSpinBox")
        self.aScaleSpinBox.setToolTip("Change the diameter (rounded up) of each atom.")
        self.showBackboneCheck = QtWidgets.QCheckBox(parent=self.centralwidget)

        self.showBackboneCheck.setChecked(True)
        self.showBackboneCheck.setObjectName("showBackboneCheck")
        self.showBackboneCheck.setToolTip("Show the N-C-C backbone of the main models.")
        self.showSidechainCheck = QtWidgets.QCheckBox(parent=self.centralwidget)

        self.showSidechainCheck.setChecked(True)
        self.showSidechainCheck.setObjectName("showSidechainCheck")
        self.showSidechainCheck.setToolTip("Show amino acid R-groups")
        self.colorByBackboneCheck = QtWidgets.QCheckBox(parent=self.centralwidget)

        self.colorByBackboneCheck.setChecked(False)
        self.colorByBackboneCheck.setObjectName("colorByBackboneCheck")
        self.colorByBackboneCheck.setToolTip("Color the backbones of the main models by the molecule number.")
        self.pScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)

        self.pScaleLabel.setObjectName("pScaleLabel")
        self.pScaleSpinBox = QtWidgets.QDoubleSpinBox(parent=self.centralwidget)

        self.pScaleSpinBox.setDecimals(1)
        self.pScaleSpinBox.setMinimum(1.0)
        self.pScaleSpinBox.setMaximum(50.0)
        self.pScaleSpinBox.setSingleStep(0.5)
        self.pScaleSpinBox.setObjectName("pScaleSpinBox")
        self.pScaleSpinBox.setToolTip("Scale the entire model by this factor.")
        self.bScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)

        self.bScaleLabel.setObjectName("bScaleLabel")
        self.backboneScaleSpinBox = QtWidgets.QDoubleSpinBox(parent=self.centralwidget)

        self.backboneScaleSpinBox.setDecimals(1)
        self.backboneScaleSpinBox.setMinimum(1.0)
        self.backboneScaleSpinBox.setMaximum(50.0)
        self.backboneScaleSpinBox.setSingleStep(0.5)
        self.backboneScaleSpinBox.setObjectName("backboneScaleSpinBox")
        self.backboneScaleSpinBox.setToolTip("Scale the width of the backbone by this factor.")
        self.selectIncludedPDBButton = QtWidgets.QPushButton(parent=self.centralwidget)

        self.selectIncludedPDBButton.setObjectName("selectIncludedPDBButton")
        self.selectMinecraftSaveButton = QtWidgets.QPushButton(parent=self.centralwidget)

        self.selectMinecraftSaveButton.setObjectName("selectMinecraftSaveButton")
        self.simpleOutputCheck = QtWidgets.QCheckBox(parent=self.centralwidget)

        self.simpleOutputCheck.setChecked(True)
        self.simpleOutputCheck.setObjectName("simpleOutputCheck")
        self.simpleOutputCheck.setToolTip("Un-select to create individual commands for each molecule")
        self.selectPDBFileButton = QtWidgets.QPushButton(parent=self.centralwidget)

        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.selectPDBFileButton.setFont(font)
        self.selectPDBFileButton.setObjectName("pushButton_10")
        self.createFunctionsButton = QtWidgets.QPushButton(parent=self.centralwidget)

        self.createFunctionsButton.setToolTip("Add the selected PDB file to the Minecraft world")
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.createFunctionsButton.setFont(font)
        self.createFunctionsButton.setObjectName("pushButton_13")
        self.orText = QtWidgets.QLabel(parent=self.centralwidget)

        font = QtGui.QFont()
        font.setPointSize(9)
        self.orText.setFont(font)
        self.orText.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.orText.setObjectName("or")
        self.andText = QtWidgets.QLabel(parent=self.centralwidget)

        font = QtGui.QFont()
        font.setPointSize(9)
        self.andText.setFont(font)
        self.andText.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.andText.setObjectName("and")

        self.bg.setGeometry(QtCore.QRect(-90, -50, 881, 500))

        self.switchModeLabel.setGeometry(QtCore.QRect(0, 0, 101, 31))
        self.CustomMode.setGeometry(QtCore.QRect(10, 30, 75, 23))
        self.SkeletonMode.setGeometry(QtCore.QRect(10, 60, 75, 23))
        self.XRayMode.setGeometry(QtCore.QRect(10, 90, 75, 23))
        self.SpaceFillingMode.setGeometry(QtCore.QRect(10, 120, 75, 23))
        self.RibbonMode.setGeometry(QtCore.QRect(10, 150, 75, 23))
        self.AminoAcidMode.setGeometry(QtCore.QRect(10, 180, 75, 23))
        self.modeInfoHLine.setGeometry(QtCore.QRect(10, 210, 71, 16))

        self.mc2pdbLabel.setGeometry(QtCore.QRect(10, 215, 71, 21))
        self.help.setGeometry(QtCore.QRect(10, 240, 75, 31))
        self.github.setGeometry(QtCore.QRect(10, 280, 75, 31))
        self.tools.setGeometry(QtCore.QRect(10, 320, 75, 31))
        self.infoDatabaseHLine.setGeometry(QtCore.QRect(10, 350, 71, 16))

        self.pdbDatabaseLabel.setGeometry(QtCore.QRect(5, 360, 91, 21))
        self.rcsbButton.setGeometry(QtCore.QRect(10, 385, 75, 31))

        self.vSepLine.setGeometry(QtCore.QRect(90, 0, 20, 431))

        self.backboneColorLabel.setGeometry(QtCore.QRect(110, 10, 120, 21))
        self.backboneColorBox.setGeometry(QtCore.QRect(240, 10, 175, 22))
        self.showBackboneCheck.setGeometry(QtCore.QRect(240, 37, 121, 17))
        self.colorByBackboneCheck.setGeometry(QtCore.QRect(240, 53, 155, 21))
        self.bScaleLabel.setGeometry(QtCore.QRect(110, 80, 111, 21))
        self.backboneScaleSpinBox.setGeometry(QtCore.QRect(240, 80, 62, 22))
        self.pScaleLabel.setGeometry(QtCore.QRect(110, 108, 71, 21))
        self.pScaleSpinBox.setGeometry(QtCore.QRect(240, 108, 62, 22))

        self.sidechainColorLabel.setGeometry(QtCore.QRect(110, 150, 120, 21))
        self.sidechainColorBox.setGeometry(QtCore.QRect(240, 150, 175, 22))
        self.showSidechainCheck.setGeometry(QtCore.QRect(240, 175, 121, 17))

        self.otherColorLabel.setGeometry(QtCore.QRect(110, 210, 121, 21))
        self.otherColorBox.setGeometry(QtCore.QRect(240, 210, 175, 22))
        self.otherMoleculeCheck.setGeometry(QtCore.QRect(240, 238, 131, 17))
        self.aScaleLabel.setGeometry(QtCore.QRect(110, 260, 61, 21))
        self.aScaleSpinBox.setGeometry(QtCore.QRect(240, 260, 62, 22))

        self.selectPDBFileButton.setGeometry(QtCore.QRect(110, 315, 91, 23))
        self.orText.setGeometry(QtCore.QRect(210, 315, 31, 21))
        self.selectIncludedPDBButton.setGeometry(QtCore.QRect(250, 315, 141, 23))

        self.andText.setGeometry(QtCore.QRect(210, 350, 31, 21))
        self.selectMinecraftSaveButton.setGeometry(QtCore.QRect(250, 350, 141, 23))

        self.simpleOutputCheck.setGeometry(QtCore.QRect(110, 385, 100, 31))
        self.createFunctionsButton.setGeometry(QtCore.QRect(230, 385, 181, 31))

        # Add labels to show selected file/folder
        self.selectedPDBLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.selectedPDBLabel.setGeometry(QtCore.QRect(110, 340, 300, 21))
        self.selectedPDBLabel.setObjectName("selectedPDBLabel")
        self.selectedPDBLabel.setText("No PDB file selected.")

        self.selectedMinecraftLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.selectedMinecraftLabel.setGeometry(QtCore.QRect(110, 370, 300, 21))
        self.selectedMinecraftLabel.setObjectName("selectedMinecraftLabel")
        self.selectedMinecraftLabel.setText("No Minecraft save selected.")

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
        self.tools.raise_()
        self.help.raise_()
        self.rcsbButton.raise_()
        self.mc2pdbLabel.raise_()
        self.pdbDatabaseLabel.raise_()
        self.modeInfoHLine.raise_()
        self.infoDatabaseHLine.raise_()
        self.backboneColorLabel.raise_()
        self.sidechainColorLabel.raise_()
        self.otherColorLabel.raise_()
        self.otherColorBox.raise_()
        self.backboneColorBox.raise_()
        self.sidechainColorBox.raise_()
        self.aScaleLabel.raise_()
        self.otherMoleculeCheck.raise_()
        self.aScaleSpinBox.raise_()
        self.showBackboneCheck.raise_()
        self.showSidechainCheck.raise_()
        self.colorByBackboneCheck.raise_()
        self.pScaleLabel.raise_()
        self.pScaleSpinBox.raise_()
        self.bScaleLabel.raise_()
        self.backboneScaleSpinBox.raise_()
        self.selectIncludedPDBButton.raise_()
        self.selectMinecraftSaveButton.raise_()
        self.simpleOutputCheck.raise_()
        self.selectPDBFileButton.raise_()
        self.createFunctionsButton.raise_()
        self.orText.raise_()
        self.andText.raise_()
        self.setCentralWidget(self.centralwidget)

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
        self.selectIncludedPDBButton.clicked.connect(self.handle_included_pdb_button)
        self.selectPDBFileButton.clicked.connect(self.handle_select_pdb_file_button)
        self.selectMinecraftSaveButton.clicked.connect(self.handle_select_minecraft_button)
        self.createFunctionsButton.clicked.connect(self.handle_make_function_button)
        self.tools.clicked.connect(self.handle_tool_mode)

        self.otherColorBox.focusOut.connect(lambda: self.check_input(self.otherColorBox, decorative_blocks))
        self.backboneColorBox.focusOut.connect(lambda: self.check_input(self.backboneColorBox, decorative_blocks))
        self.sidechainColorBox.focusOut.connect(lambda: self.check_input(self.sidechainColorBox, decorative_blocks))

        #self.showSidechainCheck.stateChanged.connect(lambda: self.check_input(self.sidechainColorBox, decorative_blocks))
        #self.showBackboneCheck.stateChanged.connect(lambda: self.check_input(self.backboneColorBox, decorative_blocks))
        self.showBackboneCheck.stateChanged.connect(self.on_showBackboneCheck_changed)
        self.showSidechainCheck.stateChanged.connect(self.on_showSidechainCheck_changed)
        self.colorByBackboneCheck.stateChanged.connect(self.on_colorByBackboneCheck_changed)
        self.otherMoleculeCheck.stateChanged.connect(self.on_otherMoleculeCheck_changed)

    def on_showBackboneCheck_changed(self, state):
        if not self.colorByBackboneCheck.isChecked():
            self.backboneColorBox.setEnabled(state != 0)
            #self.backboneColorBox.setCurrentText("gray_concrete")
        self.backboneScaleSpinBox.setEnabled(state !=0)

    def on_showSidechainCheck_changed(self, state):
        if not self.colorByBackboneCheck.isChecked():
            self.sidechainColorBox.setEnabled(state != 0)
            #self.sidechainColorBox.setCurrentText("gray_concrete")

    def on_colorByBackboneCheck_changed(self, state):
        self.backboneColorBox.setEnabled(state == 0)
        self.sidechainColorBox.setEnabled(state == 0)

    def on_otherMoleculeCheck_changed(self, state):
        self.otherColorBox.setEnabled(state != 0)
        self.aScaleSpinBox.setEnabled(state != 0)


    def check_input(self, combobox, valid_options):
        text = combobox.currentText()
        #ensure that text is lowercase
        text = text.lower()
        #replace any space characters with '_'
        text = text.replace(' ', '_')
        if text not in decorative_blocks:
            self.show_information_box(title_text=f"Invalid block input",
                                      text=f"{text} is not a valid block option.",
                                      icon_path="images/icons/icon_bad.png")
            #QMessageBox.warning(self, "Invalid Input", f"{text} is not a valid option.")
            combobox.setCurrentIndex(0)
        else:
            if combobox.findText(text) <= 0:
                icon = create_icon(hex_dict[text])
                combobox.addItem(icon, text)
            combobox.setCurrentText(text)
            combobox.setCurrentIndex(combobox.findText(text))

    # Slot methods to handle QPushButton clicks
    def handle_select_pdb_file_button(self):
        self.selectPDB = FileExplorerPopup()
        self.user_pdb_file = self.selectPDB.selected_file

        # Show recommended scale popup after file selection (for both .pdb and .cif)
        if self.user_pdb_file:
            from .utilities import InformationBox, SequenceSelectorPopup
            from PDB2MC import pdb_manipulation as pdbm
            try:
                world_max = 320
                # First check if model fits in Minecraft
                if not pdbm.check_model_size(self.user_pdb_file, world_max=world_max):
                    self.info_box = InformationBox()  # Keep reference!
                    self.info_box.set_text(f"The chosen model is too large for Minecraft.")
                    self.info_box.set_title("Model too large!")
                    self.info_box.set_icon("images/icons/icon_bad.png")
                    self.info_box.show()
                else:
                    size_factor = pdbm.check_max_size(self.user_pdb_file, world_max=world_max)
                    print("Multiplier is: ", size_factor)  # For debugging
                    size_factor = str(round(size_factor, 2))
                    self.info_box = InformationBox()  # Keep reference!
                    self.info_box.set_text(
                        f"The suggested maximum protein scale is: {size_factor}x\n\nSet 'Protein Scale' below this for best results.")
                    self.info_box.set_title("Maximum scale")
                    self.info_box.set_icon("images/icons/icon_info.png")
                    self.info_box.show()

                # # --- TESTING: Show SequenceSelectorPopup after file selection ---
                # from PDB2MC.structure_data import StructureData
                # try:
                #     if self.user_pdb_file.lower().endswith('.cif'):
                #         structure = StructureData.from_mmcif(self.user_pdb_file)
                #     else:
                #         structure = StructureData.from_pdb(self.user_pdb_file)
                #     print("okay gonna do it.")
                #     self.seq_selector = SequenceSelectorPopup(structure)
                #     self.seq_selector.show()
                # except Exception as e:
                #     QMessageBox.critical(self, "File Error", f"Failed to load structure for sequence selection:\n{e}")
                # # -------------------------------------------------------------

            except Exception as e:
                self.info_box = InformationBox()  # Keep reference!
                self.info_box.set_text(f"Could not determine recommended scale.\nError: {e}")
                self.info_box.set_title("Scale error")
                self.info_box.set_icon("images/icons/icon_bad.png")
                self.info_box.show()

    def handle_select_minecraft_button(self):
        self.selectMinecraft = MinecraftPopup()
        if self.selectMinecraft.selected_directory is None:
            self.show_information_box(title_text=f"Error",
                                      text=f"Remember to select a Minecraft save.",
                                      icon_path="images/icons/icon_bad.png")
            return
        self.user_minecraft_save = self.selectMinecraft.selected_directory

    def handle_included_pdb_button(self):
        self.includedPDB = IncludedPDBPopup()
        self.includedPDB.show()
        self.includedPDB.selected.connect(self.save_selected_text)

    def save_selected_text(self, text):
        self.user_pdb_file = f"presets/{text}.pdb"

    def handle_make_function_button(self):
        # Create a dictionary to store the user options
        config_data = {'atoms': {}}
        config_data['atoms']['O'] = 'red_wool'
        config_data['atoms']['N'] = 'blue_wool'
        config_data['atoms']['P'] = 'lime_wool'
        config_data['atoms']['S'] = 'yellow_wool'
        config_data['atoms']['C'] = 'black_wool'
        config_data['atoms']['FE'] = 'iron_block'
        config_data['atoms']['other_atom'] = self.otherColorBox.currentText()
        config_data['atoms']['backbone_atom'] = self.backboneColorBox.currentText()
        config_data['atoms']['sidechain_atom'] = self.sidechainColorBox.currentText()
        config_data['backbone_size'] = self.backboneScaleSpinBox.value()
        config_data['atom_scale'] = self.aScaleSpinBox.value()
        config_data['scale'] = self.pScaleSpinBox.value()
        config_data['show_hetatm'] = self.otherMoleculeCheck.isChecked()
        config_data['backbone'] = self.showBackboneCheck.isChecked()
        config_data['sidechain'] = self.showSidechainCheck.isChecked()
        config_data['by_chain'] = self.colorByBackboneCheck.isChecked()
        config_data['simple'] = self.simpleOutputCheck.isChecked()

        if self.user_pdb_file is None:
            self.show_information_box(title_text=f"Error: No PDB file",
                                      text=f"Please select a PDB file.",
                                      icon_path="images/icons/icon_bad.png")
        elif self.user_minecraft_save is None:
            self.show_information_box(title_text=f"Error: No Minecraft save",
                                      text=f"Please select a Minecraft save.",
                                      icon_path="images/icons/icon_bad.png")
        else:
            config_data['pdb_file'] = self.user_pdb_file
            config_data['save_path'] = self.user_minecraft_save

            # Show modal progress dialog
            self.wait_dialog = PleaseWaitDialog(self)
            self.wait_dialog.show()

            # Use WorkerThread for background processing
            self.worker = WorkerThread(config_data)
            self.worker.progress.connect(self.wait_dialog.set_progress)
            self.worker.finished.connect(self.on_worker_finished)
            self.worker.start()

    def on_worker_progress(self, value):
        # No longer needed, handled by PleaseWaitDialog
        pass

    def on_worker_finished(self, result):
        self.wait_dialog.close()
        if result.get("result") == "done":
            lower = result.get("lower", "")
            self.show_information_box(
                title_text=f"Model generated",
                text=f"Finished! \n Remember to use /reload\n Make your model with: /function protein:build_{lower}",
                icon_path="images/icons/icon_good.png"
            )
        else:
            self.show_information_box(
                title_text="Error encountered",
                text=f"Model has not generated! \nError: {result.get('error', '')}",
                icon_path="images/icons/icon_bad.png"
            )

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
        #QDesktopServices.openUrl(QtCore.QUrl("https://github.com/markus-nevil/mcpdb/blob/main/README.md"))

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
            pass
        except Exception as e:
            print(f"Error in handle_skeleton_mode: {e}")

    def handle_tool_mode(self):
        try:
            from UI.tool_window import ToolWindow
            self.tool_window = ToolWindow()
            self.tool_window.show()
            self.hide()
        except Exception as e:
            print(f"Error in handle_space_filling_mode: {e}")

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

    def retranslateUi(self, SkeletonWindow):
        _translate = QtCore.QCoreApplication.translate
        self.switchModeLabel.setText(_translate("SkeletonWindow", "Switch Mode"))
        self.CustomMode.setText(_translate("SkeletonWindow", "Custom"))
        self.SkeletonMode.setText(_translate("SkeletonWindow", "Skeleton"))
        self.XRayMode.setText(_translate("SkeletonWindow", "X-Ray"))
        self.SpaceFillingMode.setText(_translate("SkeletonWindow", "Space Filling"))
        self.AminoAcidMode.setText(_translate("SkeletonWindow", "Amino Acids"))
        self.RibbonMode.setText(_translate("SkeletonWindow", "Ribbon"))
        self.github.setText(_translate("SkeletonWindow", "Github"))
        self.tools.setText(_translate("SkeletonWindow", "Tools"))
        self.help.setText(_translate("SkeletonWindow", "Help"))
        self.rcsbButton.setText(_translate("SkeletonWindow", "RCSB.org"))
        self.mc2pdbLabel.setText(_translate("SkeletonWindow", "PDB2MC"))
        self.pdbDatabaseLabel.setText(_translate("SkeletonWindow", "PDB Database"))
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
        self.createFunctionsButton.setText(_translate("SkeletonWindow", "Create Minecraft Functions"))
        self.orText.setText(_translate("SkeletonWindow", "or"))
        self.andText.setText(_translate("SkeletonWindow", "and"))


def set_combobox_by_text(combobox, text):
    index = combobox.findText(text)
    if index >= 0:  # If the text is found
        combobox.setCurrentIndex(index)

def create_icon(hex_color: str, size: int = 100) -> QIcon:
    #print(hex_color)

    # Create a QPixmap object
    pixmap = QPixmap(size, size)
    # Create a QPainter object and begin painting on the QPixmap
    painter = QPainter(pixmap)
    # Set the brush color to the desired color
    color = QColor(hex_color)
    painter.setBrush(color)
    # Draw a rectangle on the QPixmap
    painter.drawRect(0, 0, size, size)
    # End the painting process
    painter.end()
    # Create a QIcon object from the QPixmap
    icon = QIcon(pixmap)
    return icon

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

if __name__ == "__main__":
    app = QApplication([])
    main_window = SkeletonWindow()
    main_window.show()
    app.exec()