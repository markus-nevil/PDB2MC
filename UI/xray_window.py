from PyQt6.QtWidgets import QApplication, QMainWindow, QCompleter, QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtGui import QDesktopServices, QColor, QIcon, QPainter, QPixmap
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QThread, pyqtSignal
import os
from PDB2MC.variables import decorative_blocks, hex_dict
import pandas as pd
from PDB2MC import minecraft_functions as mcf, pdb_manipulation as pdbm, xray
from UI.utilities import InformationBox, MyComboBox, IncludedPDBPopup, MinecraftPopup, FileExplorerPopup
import sys
import pkg_resources

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
            config_data['structure'] = structure

            pdb_name = structure.metadata.get('id', pdbm.get_pdb_code(pdb_file))
            self.progress.emit(10)

            hetatom_df = None
            hetatm_bonds = None
            if config_data["show_hetatm"]:
                hetatom_df = None
                hetatm_bonds = None

            self.progress.emit(30)
            mc_dir = config_data['save_path']
            mcf.delete_old_files(mc_dir, pdb_name)

            try:
                xray.run_mode(
                    config_data,
                    pdb_name,
                    structure,
                    mc_dir,
                    hetatom_df,
                    hetatm_bonds
                )
                self.progress.emit(50)
            except Exception as e:
                self.finished.emit({"result": "error", "error": f"Error in xray.run_mode: {e}"})
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

class XrayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_pdb_file = None
        self.user_minecraft_save = None
        # current_directory = os.path.basename(os.getcwd())
        # if current_directory == "PDB2MC":
        #     mcpdb_directory = os.path.join(os.getcwd(), ".." "UI")
        #     os.chdir(mcpdb_directory)
        #
        # print(os.getcwd())

        os.chdir(get_images_path())
        
        self.setWindowTitle("X-ray mode")
        self.resize(607, 430)
        self.setWindowIcon(QIcon('images/icons/logo.png'))

        # Set style to Fusion
        #self.setStyle("Fusion")
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

        self.tools = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.tools.setFont(font)
        self.tools.setObjectName("tools")

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
        self.cColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.cColorLabel.setObjectName("cColorLabel")
        self.oColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.oColorLabel.setObjectName("oColorLabel")
        self.nColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.nColorLabel.setObjectName("nColorLabel")
        self.sColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.sColorLabel.setObjectName("sColorLabel")
        self.pColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.pColorLabel.setObjectName("pColorLabel")
        self.backboneColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.backboneColorLabel.setObjectName("backboneColorLabel")
        self.sidechainColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.sidechainColorLabel.setObjectName("sidechainColorLabel")
        self.otherColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.otherColorLabel.setObjectName("otherColorLabel")
        self.oColorBox = MyComboBox(self.centralwidget)
        self.oColorBox.setObjectName("oColorBox")
        self.oColorBox.setEditable(True)

        self.nColorBox = MyComboBox(self.centralwidget)
        self.nColorBox.setObjectName("nColorBox")
        self.nColorBox.setEditable(True)

        self.pColorBox = MyComboBox(self.centralwidget)
        self.pColorBox.setObjectName("pColorBox")
        self.pColorBox.setEditable(True)

        self.otherColorBox = MyComboBox(self.centralwidget)
        self.otherColorBox.setObjectName("otherColorBox")
        self.otherColorBox.setEditable(True)

        self.sColorBox = MyComboBox(self.centralwidget)
        self.sColorBox.setObjectName("sColorBox")
        self.sColorBox.setEditable(True)

        self.cColorBox = MyComboBox(self.centralwidget)
        self.cColorBox.setObjectName("cColorBox")
        self.cColorBox.setEditable(True)

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

        color_boxes = [self.sidechainColorBox, self.backboneColorBox]

        for color_box in color_boxes:
            for value, icon in icon_dict.items():
                color_box.addItem(create_icon(hex_dict[value]), value)
                #color_box.addItem(eval(icon), value)
            color_box.insertSeparator(16)
            color_box.insertSeparator(33)
            color_box.insertSeparator(50)
            color_box.insertSeparator(67)

        self.sidechainColorBox.setCurrentIndex(13)
        self.backboneColorBox.setCurrentIndex(13)

        sidechainCompleter = QCompleter(decorative_blocks)
        sidechainCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.sidechainColorBox.setCompleter(sidechainCompleter)

        backboneCompleter = QCompleter(decorative_blocks)
        backboneCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.backboneColorBox.setCompleter(backboneCompleter)


        glass_dict = {
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

        color_boxes = [self.oColorBox, self.otherColorBox, self.cColorBox,
                       self.nColorBox, self.sColorBox, self.pColorBox]

        for color_box in color_boxes:
            for value, icon in glass_dict.items():
                color_box.addItem(create_icon(hex_dict[value]), value)
                #color_box.addItem(eval(icon), value)

        self.oColorBox.setCurrentIndex(0)
        self.cColorBox.setCurrentIndex(12)
        self.nColorBox.setCurrentIndex(7)
        self.sColorBox.setCurrentIndex(2)
        self.pColorBox.setCurrentIndex(3)
        self.otherColorBox.setCurrentIndex(10)

        oCompleter = QCompleter(decorative_blocks)
        oCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        cCompleter = QCompleter(decorative_blocks)
        cCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        nCompleter = QCompleter(decorative_blocks)
        nCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        sCompleter = QCompleter(decorative_blocks)
        sCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        pCompleter = QCompleter(decorative_blocks)
        pCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        otherCompleter = QCompleter(decorative_blocks)
        otherCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.oColorBox.setCompleter(oCompleter)
        self.cColorBox.setCompleter(cCompleter)
        self.nColorBox.setCompleter(nCompleter)
        self.sColorBox.setCompleter(sCompleter)
        self.pColorBox.setCompleter(pCompleter)
        self.otherColorBox.setCompleter(otherCompleter)

        self.aScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.aScaleLabel.setObjectName("aScaleLabel")
        self.showAtomsCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.showAtomsCheck.setChecked(True)
        self.showAtomsCheck.setObjectName("showAtomsCheck")
        self.showAtomsCheck.setToolTip("Show the atoms of the main models.")
        self.otherMoleculeCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.otherMoleculeCheck.setChecked(True)
        self.otherMoleculeCheck.setObjectName("otherMoleculeCheck")
        self.otherMoleculeCheck.setToolTip("Check to show other non-protein, DNA, or RNA molecules.")
        self.meshCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.meshCheck.setObjectName("meshCheck")
        self.meshCheck.setToolTip("Check to show mesh-style atoms: many fewer blocks")
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
        self.modeInfoHLine.setGeometry(QtCore.QRect(10, 205, 71, 16))

        self.mc2pdbLabel.setGeometry(QtCore.QRect(10, 220, 71, 21))
        self.help.setGeometry(QtCore.QRect(10, 240, 75, 31))
        self.tools.setGeometry(QtCore.QRect(10, 280, 75, 31))
        self.github.setGeometry(QtCore.QRect(10, 320, 75, 31))
        self.infoDatabaseHLine.setGeometry(QtCore.QRect(10, 350, 71, 16))

        self.pdbDatabaseLabel.setGeometry(QtCore.QRect(0, 360, 91, 21))
        self.rcsbButton.setGeometry(QtCore.QRect(10, 385, 75, 31))

        self.vSepLine.setGeometry(QtCore.QRect(90, 0, 20, 431))

        self.cColorLabel.setGeometry(QtCore.QRect(110, 10, 106, 21))
        self.cColorBox.setGeometry(QtCore.QRect(240, 10, 175, 22))
        self.showAtomsCheck.setGeometry(QtCore.QRect(440, 10, 121, 17))

        self.oColorLabel.setGeometry(QtCore.QRect(110, 40, 106, 21))
        self.oColorBox.setGeometry(QtCore.QRect(240, 40, 175, 22))
        self.otherMoleculeCheck.setGeometry(QtCore.QRect(440, 40, 131, 17))

        self.nColorLabel.setGeometry(QtCore.QRect(110, 70, 106, 21))
        self.nColorBox.setGeometry(QtCore.QRect(240, 70, 175, 22))
        self.meshCheck.setGeometry(QtCore.QRect(440, 70, 151, 17))

        self.sColorLabel.setGeometry(QtCore.QRect(110, 100, 106, 21))
        self.sColorBox.setGeometry(QtCore.QRect(240, 100, 175, 22))
        self.aScaleLabel.setGeometry(QtCore.QRect(440, 100, 61, 21))
        self.aScaleSpinBox.setGeometry(QtCore.QRect(530, 100, 62, 22))

        self.pColorLabel.setGeometry(QtCore.QRect(110, 130, 110, 21))
        self.pColorBox.setGeometry(QtCore.QRect(240, 130, 175, 22))
        self.pScaleLabel.setGeometry(QtCore.QRect(440, 130, 71, 21))
        self.pScaleSpinBox.setGeometry(QtCore.QRect(530, 130, 62, 22))

        self.otherColorLabel.setGeometry(QtCore.QRect(110, 160, 121, 21))
        self.otherColorBox.setGeometry(QtCore.QRect(240, 160, 175, 22))

        self.sidechainColorLabel.setGeometry(QtCore.QRect(110, 225, 120, 21))
        self.sidechainColorBox.setGeometry(QtCore.QRect(240, 225, 175, 22))
        self.showSidechainCheck.setGeometry(QtCore.QRect(440, 225, 121, 17))

        self.backboneColorLabel.setGeometry(QtCore.QRect(110, 255, 120, 21))
        self.backboneColorBox.setGeometry(QtCore.QRect(240, 255, 175, 22))
        self.showBackboneCheck.setGeometry(QtCore.QRect(440, 255, 121, 17))

        self.colorByBackboneCheck.setGeometry(QtCore.QRect(240, 285, 155, 21))
        self.bScaleLabel.setGeometry(QtCore.QRect(440, 285, 111, 21))
        self.backboneScaleSpinBox.setGeometry(QtCore.QRect(530, 285, 62, 22))

        self.selectPDBFileButton.setGeometry(QtCore.QRect(110, 350, 91, 23))
        self.orText.setGeometry(QtCore.QRect(210, 350, 21, 21))
        self.selectIncludedPDBButton.setGeometry(QtCore.QRect(250, 350, 141, 23))

        self.andText.setGeometry(QtCore.QRect(400, 350, 31, 21))
        self.selectMinecraftSaveButton.setGeometry(QtCore.QRect(440, 350, 131, 23))

        self.simpleOutputCheck.setGeometry(QtCore.QRect(110, 385, 100, 31))
        self.createFunctionsButton.setGeometry(QtCore.QRect(230, 385, 181, 31))


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
        self.colorByBackboneCheck.raise_()
        self.help.raise_()
        self.rcsbButton.raise_()
        self.mc2pdbLabel.raise_()
        self.pdbDatabaseLabel.raise_()
        self.modeInfoHLine.raise_()
        self.infoDatabaseHLine.raise_()
        self.cColorLabel.raise_()
        self.oColorLabel.raise_()
        self.nColorLabel.raise_()
        self.sColorLabel.raise_()
        self.pColorLabel.raise_()
        self.backboneColorLabel.raise_()
        self.tools.raise_()
        self.sidechainColorLabel.raise_()
        self.otherColorLabel.raise_()
        self.oColorBox.raise_()
        self.nColorBox.raise_()
        self.pColorBox.raise_()
        self.otherColorBox.raise_()
        self.sColorBox.raise_()
        self.cColorBox.raise_()
        self.backboneColorBox.raise_()
        self.sidechainColorBox.raise_()
        self.aScaleLabel.raise_()
        self.showAtomsCheck.raise_()
        self.otherMoleculeCheck.raise_()
        self.meshCheck.raise_()
        self.aScaleSpinBox.raise_()
        self.showBackboneCheck.raise_()
        self.showSidechainCheck.raise_()
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
        self.colorByBackboneCheck.stateChanged.connect(self.on_colorByBackboneCheck_changed)
        self.tools.clicked.connect(self.handle_tool_mode)

        #self.oColorBox.focusOut.connect(self.check_input)
        self.oColorBox.focusOut.connect(lambda: self.check_input(self.oColorBox, decorative_blocks))
        self.cColorBox.focusOut.connect(lambda: self.check_input(self.cColorBox, decorative_blocks))
        self.sColorBox.focusOut.connect(lambda: self.check_input(self.sColorBox, decorative_blocks))
        self.pColorBox.focusOut.connect(lambda: self.check_input(self.pColorBox, decorative_blocks))
        self.nColorBox.focusOut.connect(lambda: self.check_input(self.nColorBox, decorative_blocks))
        self.otherColorBox.focusOut.connect(lambda: self.check_input(self.otherColorBox, decorative_blocks))
        self.backboneColorBox.focusOut.connect(lambda: self.check_input(self.backboneColorBox, decorative_blocks))
        self.sidechainColorBox.focusOut.connect(lambda: self.check_input(self.sidechainColorBox, decorative_blocks))

        self.showAtomsCheck.stateChanged.connect(self.on_showAtomsAndMoleculesCheck_changed)
        self.otherMoleculeCheck.stateChanged.connect(self.on_showAtomsAndMoleculesCheck_changed)

        self.showBackboneCheck.stateChanged.connect(self.on_showBackboneCheck_changed)
        self.showSidechainCheck.stateChanged.connect(self.on_showSidechainCheck_changed)

    def on_colorByBackboneCheck_changed(self, state):
        self.backboneColorBox.setEnabled(state == 0)
        self.sidechainColorBox.setEnabled(state == 0)

    def on_showAtomsAndMoleculesCheck_changed(self, state):
        if self.showAtomsCheck.isChecked() or self.otherMoleculeCheck.isChecked():
            self.cColorBox.setEnabled(True)
            self.oColorBox.setEnabled(True)
            self.nColorBox.setEnabled(True)
            self.sColorBox.setEnabled(True)
            self.pColorBox.setEnabled(True)
            self.otherColorBox.setEnabled(True)
        else:
            self.cColorBox.setEnabled(False)
            self.oColorBox.setEnabled(False)
            self.nColorBox.setEnabled(False)
            self.sColorBox.setEnabled(False)
            self.pColorBox.setEnabled(False)
            self.otherColorBox.setEnabled(False)

    def on_showBackboneCheck_changed(self, state):

        self.backboneColorBox.setEnabled(state != 0)

        self.backboneScaleSpinBox.setEnabled(state !=0)

    def on_showSidechainCheck_changed(self, state):

        self.sidechainColorBox.setEnabled(state != 0)


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
        print("Selecting PDB file")
        self.selectPDB = FileExplorerPopup()
        self.user_pdb_file = self.selectPDB.selected_file
        print(f"The user has this file: {self.user_pdb_file}")

        # Show recommended scale popup after file selection (for both .pdb and .cif)
        if self.user_pdb_file:
            from .utilities import InformationBox
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
                    size_factor = str(round(size_factor, 2))
                    self.info_box = InformationBox()  # Keep reference!
                    self.info_box.set_text(
                        f"The suggested maximum protein scale is: {size_factor}x\n\nSet 'Protein Scale' below this for best results.")
                    self.info_box.set_title("Maximum scale")
                    self.info_box.set_icon("images/icons/icon_info.png")
                    self.info_box.show()
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
        print("Included PDB button clicked")
        self.includedPDB = IncludedPDBPopup()
        self.includedPDB.show()
        self.includedPDB.selected.connect(self.save_selected_text)

    def save_selected_text(self, text):
        self.selected_text = text
        print(f"This is what was selectd: {text}")
        #make global variable for pdb file
        self.user_pdb_file = f"presets/{text}.pdb"
        print(f"The user has this file: {self.user_pdb_file}")

    def handle_make_function_button(self):
        # Create a dictionary to store the user options
        config_data = {}
        config_data['atoms'] = {}

        # Add the current text of each combobox to the dictionary
        config_data['atoms']['O'] = self.oColorBox.currentText()
        config_data['atoms']['N'] = self.nColorBox.currentText()
        config_data['atoms']['P'] = self.pColorBox.currentText()
        config_data['atoms']['S'] = self.sColorBox.currentText()
        config_data['atoms']['C'] = self.cColorBox.currentText()
        config_data['atoms']['FE'] = 'iron_block'
        config_data['atoms']['other_atom'] = self.otherColorBox.currentText()
        config_data['atoms']['backbone_atom'] = self.backboneColorBox.currentText()
        config_data['atoms']['sidechain_atom'] = self.sidechainColorBox.currentText()

        config_data['backbone_size'] = self.backboneScaleSpinBox.value()
        config_data['atom_scale'] = self.aScaleSpinBox.value()
        config_data['scale'] = self.pScaleSpinBox.value()

        # Add the checked state of each checkbox to the dictionary
        config_data['show_atoms'] = self.showAtomsCheck.isChecked()
        config_data['show_hetatm'] = self.otherMoleculeCheck.isChecked()
        config_data['mesh'] = self.meshCheck.isChecked()
        config_data['backbone'] = self.showBackboneCheck.isChecked()
        config_data['sidechain'] = self.showSidechainCheck.isChecked()
        config_data['by_chain'] = self.colorByBackboneCheck.isChecked()
        config_data['simple'] = self.simpleOutputCheck.isChecked()

        # Add the current paths of the files and directories to the dictionary
        # Replace 'file_path' and 'save_path' with the actual paths
        if self.user_pdb_file is None:
            self.show_information_box(title_text=f"Error: No PDB file",
                                      text=f"Please select a PDB file.",
                                      icon_path="images/icons/icon_bad.png")
            return
        if self.user_minecraft_save is None or not os.path.isdir(self.user_minecraft_save):
            self.show_information_box(title_text=f"Error: No Minecraft save",
                                      text=f"Please select a valid Minecraft save.",
                                      icon_path="images/icons/icon_bad.png")
            return

        config_data['pdb_file'] = self.user_pdb_file
        config_data['save_path'] = self.user_minecraft_save

        # Show modal progress dialog
        self.wait_dialog = PleaseWaitDialog(self)
        self.wait_dialog.show()

        # Defensive: ensure only one worker thread is running
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        self.worker = WorkerThread(config_data)
        self.worker.progress.connect(self.wait_dialog.set_progress)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_finished(self, result):
        # Defensive: close the dialog only if it exists
        if hasattr(self, 'wait_dialog') and self.wait_dialog:
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

    def handle_github_button(self):
        print("Github button clicked")
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
        print("RSCB button clicked")
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
            pass
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

    def show_information_box(self, title_text, text, icon_path):
        self.info_box = InformationBox()
        self.info_box.set_text(text)
        self.info_box.set_title(title_text)
        self.info_box.set_icon(icon_path)
        self.info_box.show()


    def retranslateUi(self, XrayWindow):
        _translate = QtCore.QCoreApplication.translate

        self.switchModeLabel.setText(_translate("XrayWindow", "Switch Mode"))
        self.CustomMode.setText(_translate("XrayWindow", "Custom"))
        self.SkeletonMode.setText(_translate("XrayWindow", "Skeleton"))
        self.XRayMode.setText(_translate("XrayWindow", "X-Ray"))
        self.SpaceFillingMode.setText(_translate("XrayWindow", "Space Filling"))
        self.AminoAcidMode.setText(_translate("XrayWindow", "Amino Acids"))
        self.RibbonMode.setText(_translate("XrayWindow", "Ribbon"))
        self.github.setText(_translate("XrayWindow", "Github"))
        self.help.setText(_translate("XrayWindow", "Help"))
        self.rcsbButton.setText(_translate("XrayWindow", "RCSB.org"))
        self.mc2pdbLabel.setText(_translate("XrayWindow", "PDB2MC"))
        self.pdbDatabaseLabel.setText(_translate("XrayWindow", "PDB Database"))
        self.cColorLabel.setText(_translate("XrayWindow", "Select C atom color:"))
        self.oColorLabel.setText(_translate("XrayWindow", "Select O atom color:"))
        self.nColorLabel.setText(_translate("XrayWindow", "Select N atom color:"))
        self.sColorLabel.setText(_translate("XrayWindow", "Select S atom color:"))
        self.pColorLabel.setText(_translate("XrayWindow", "Select P atom color:"))
        self.backboneColorLabel.setText(_translate("XrayWindow", "Select backbone color:"))
        self.sidechainColorLabel.setText(_translate("XrayWindow", "Select sidechain color:"))
        self.tools.setText(_translate("XrayWindow", "Tools"))
        self.otherColorLabel.setText(_translate("XrayWindow", "Select other color:"))
        self.aScaleLabel.setText(_translate("XrayWindow", "Atom scale:"))
        self.showAtomsCheck.setText(_translate("XrayWindow", "Show model atoms"))
        self.otherMoleculeCheck.setText(_translate("XrayWindow", "Show other molecules"))
        self.meshCheck.setText(_translate("XrayWindow", "Use \"mesh-style\" atoms"))
        self.showBackboneCheck.setText(_translate("XrayWindow", "Show backbone"))
        self.showSidechainCheck.setText(_translate("XrayWindow", "Show sidechain"))
        self.colorByBackboneCheck.setText(_translate("XrayWindow", "Color backbone by chain"))
        self.pScaleLabel.setText(_translate("XrayWindow", "Protein scale:"))
        self.bScaleLabel.setText(_translate("XrayWindow", "Backbone scale:"))
        self.selectIncludedPDBButton.setText(_translate("XrayWindow", "Select Included PDB File"))
        self.selectMinecraftSaveButton.setText(_translate("XrayWindow", "Select Minecraft Save"))
        self.simpleOutputCheck.setText(_translate("XrayWindow", "Simple output"))
        self.selectPDBFileButton.setText(_translate("XrayWindow", "Select PDB File"))
        self.createFunctionsButton.setText(_translate("XrayWindow", "Create Minecraft Functions"))
        self.orText.setText(_translate("XrayWindow", "or"))
        self.andText.setText(_translate("XrayWindow", "and"))

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
    main_window = XrayWindow()
    main_window.show()
    app.exec()