from PyQt6.QtWidgets import QApplication, QMainWindow, QCompleter, QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtGui import QDesktopServices, QColor, QIcon, QPainter, QPixmap
from PyQt6 import QtCore, QtGui, QtWidgets
from PDB2MC.variables import decorative_blocks, hex_dict
import os
from PDB2MC import minecraft_functions as mcf, pdb_manipulation as pdbm, amino_acids
from .utilities import InformationBox, MyComboBox, IncludedPDBPopup, MinecraftPopup, FileExplorerPopup
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
            config_data['structure'] = structure

            pdb_name = structure.metadata.get('id', pdbm.get_pdb_code(pdb_file))
            self.progress.emit(10)

            mc_dir = config_data['save_path']
            mcf.delete_old_files(mc_dir, pdb_name)

            try:
                amino_acids.run_mode(structure, config_data, pdb_name, mc_dir)
                self.progress.emit(50)
            except Exception as e:
                self.finished.emit({"result": "error", "error": f"Error in amino_acids.run_mode: {e}"})
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

class AAWindow(QMainWindow):


    def __init__(self):
        super().__init__()

        self.user_pdb_file = None
        self.user_minecraft_save = None
        self.setWindowTitle("Amino Acid Mode")

        # current_directory = os.path.basename(os.getcwd())
        # if current_directory == "PDB2MC":
        #     mcpdb_directory = os.path.join(os.getcwd(), ".." "UI")
        #     os.chdir(mcpdb_directory)
        os.chdir(get_images_path())

        self.setWindowIcon(QIcon('images/icons/logo.png'))

        self.resize(695, 430)
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
        font = QtGui.QFont()
        font.setPointSize(7)
        self.bg.setFont(font)
        self.bg.setText("")
        self.bg.setPixmap(QtGui.QPixmap("images/MC2PDB bg.png"))
        self.bg.setScaledContents(True)
        self.bg.setObjectName("bg")

        self.backboneColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.backboneColorLabel.setObjectName("backboneColorLabel")

        self.AlaColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.AlaColorLabel.setObjectName("AlaColorLabel")
        self.AlaColorBox = MyComboBox(self.centralwidget)
        self.AlaColorBox.setObjectName("AlaColorBox")
        self.AlaColorBox.setEditable(True)

        self.ArgColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.ArgColorLabel.setObjectName("ArgColorLabel")
        self.ArgColorBox = MyComboBox(self.centralwidget)
        self.ArgColorBox.setObjectName("ArgColorBox")
        self.ArgColorBox.setEditable(True)

        self.AsnColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.AsnColorLabel.setObjectName("AsnColorLabel")
        self.AsnColorBox = MyComboBox(self.centralwidget)
        self.AsnColorBox.setObjectName("AsnColorBox")
        self.AsnColorBox.setEditable(True)

        self.AspColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.AspColorLabel.setObjectName("AspColorLabel")
        self.AspColorBox = MyComboBox(self.centralwidget)
        self.AspColorBox.setObjectName("AspColorBox")
        self.AspColorBox.setEditable(True)

        self.CysColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.CysColorLabel.setObjectName("CysColorLabel")
        self.CysColorBox = MyComboBox(self.centralwidget)
        self.CysColorBox.setObjectName("CysColorBox")
        self.CysColorBox.setEditable(True)

        self.GlnColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.GlnColorLabel.setObjectName("GlnColorLabel")
        self.GlnColorBox = MyComboBox(self.centralwidget)
        self.GlnColorBox.setObjectName("GlnColorBox")
        self.GlnColorBox.setEditable(True)

        self.GluColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.GluColorLabel.setObjectName("GluColorLabel")
        self.GluColorBox = MyComboBox(self.centralwidget)
        self.GluColorBox.setObjectName("GluColorBox")
        self.GluColorBox.setEditable(True)

        self.GlyColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.GlyColorLabel.setObjectName("GlyColorLabel")
        self.GlyColorBox = MyComboBox(self.centralwidget)
        self.GlyColorBox.setObjectName("GlyColorBox")
        self.GlyColorBox.setEditable(True)

        self.HisColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.HisColorLabel.setObjectName("HisColorLabel")
        self.HisColorBox = MyComboBox(self.centralwidget)
        self.HisColorBox.setObjectName("HisColorBox")
        self.HisColorBox.setEditable(True)

        self.IleColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.IleColorLabel.setObjectName("IleColorLabel")
        self.IleColorBox = MyComboBox(self.centralwidget)
        self.IleColorBox.setObjectName("IleColorBox")
        self.IleColorBox.setEditable(True)

        self.LeuColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.LeuColorLabel.setObjectName("LeuColorLabel")
        self.LeuColorBox = MyComboBox(self.centralwidget)
        self.LeuColorBox.setObjectName("LeuColorBox")
        self.LeuColorBox.setEditable(True)

        self.LysColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.LysColorLabel.setObjectName("LysColorLabel")
        self.LysColorBox = MyComboBox(self.centralwidget)
        self.LysColorBox.setObjectName("LysColorBox")
        self.LysColorBox.setEditable(True)

        self.MetColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.MetColorLabel.setObjectName("MetColorLabel")
        self.MetColorBox = MyComboBox(self.centralwidget)
        self.MetColorBox.setObjectName("MetColorBox")
        self.MetColorBox.setEditable(True)

        self.PheColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.PheColorLabel.setObjectName("PheColorLabel")
        self.PheColorBox = MyComboBox(self.centralwidget)
        self.PheColorBox.setObjectName("PheColorBox")
        self.PheColorBox.setEditable(True)

        self.ProColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.ProColorLabel.setObjectName("ProColorLabel")
        self.ProColorBox = MyComboBox(self.centralwidget)
        self.ProColorBox.setObjectName("ProColorBox")
        self.ProColorBox.setEditable(True)

        self.SerColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.SerColorLabel.setObjectName("SerColorLabel")
        self.SerColorBox = MyComboBox(self.centralwidget)
        self.SerColorBox.setObjectName("SerColorBox")
        self.SerColorBox.setEditable(True)

        self.ThrColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.ThrColorLabel.setObjectName("ThrColorLabel")
        self.ThrColorBox = MyComboBox(self.centralwidget)
        self.ThrColorBox.setObjectName("ThrColorBox")
        self.ThrColorBox.setEditable(True)

        self.TrpColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.TrpColorLabel.setObjectName("TrpColorLabel")
        self.TrpColorBox = MyComboBox(self.centralwidget)
        self.TrpColorBox.setObjectName("TrpColorBox")
        self.TrpColorBox.setEditable(True)

        self.TyrColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.TyrColorLabel.setObjectName("TyrColorLabel")
        self.TyrColorBox = MyComboBox(self.centralwidget)
        self.TyrColorBox.setObjectName("TyrColorBox")
        self.TyrColorBox.setEditable(True)

        self.ValColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.ValColorLabel.setObjectName("ValColorLabel")
        self.ValColorBox = MyComboBox(self.centralwidget)
        self.ValColorBox.setObjectName("ValColorBox")
        self.ValColorBox.setEditable(True)

        self.backboneColorBox = MyComboBox(self.centralwidget)
        self.backboneColorBox.setObjectName("backboneColorBox")
        self.backboneColorBox.setEditable(True)

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

        color_boxes = [self.AlaColorBox, self.ArgColorBox, self.AsnColorBox, self.AspColorBox,
                       self.CysColorBox, self.GlnColorBox, self.GluColorBox, self.GlyColorBox, self.HisColorBox,
                       self.IleColorBox, self.LeuColorBox, self.LysColorBox, self.MetColorBox, self.PheColorBox,
                       self.ProColorBox, self.SerColorBox, self.ThrColorBox, self.TrpColorBox, self.TyrColorBox,
                       self.ValColorBox, self.backboneColorBox]

        for color_box in color_boxes:
            for value, icon in icon_dict.items():
                color_box.addItem(create_icon(hex_dict[value]), value)

        color_box.insertSeparator(16)
        color_box.insertSeparator(33)
        color_box.insertSeparator(50)
        color_box.insertSeparator(67)


        self.AlaColorBox.setCurrentIndex(0)
        self.ArgColorBox.setCurrentIndex(2)
        self.AsnColorBox.setCurrentIndex(5)
        self.AspColorBox.setCurrentIndex(8)
        self.CysColorBox.setCurrentIndex(11)
        self.GlnColorBox.setCurrentIndex(14)
        self.GluColorBox.setCurrentIndex(17)
        self.GlyColorBox.setCurrentIndex(20)
        self.HisColorBox.setCurrentIndex(23)
        self.IleColorBox.setCurrentIndex(26)
        self.LeuColorBox.setCurrentIndex(29)
        self.LysColorBox.setCurrentIndex(32)
        self.MetColorBox.setCurrentIndex(35)
        self.PheColorBox.setCurrentIndex(38)
        self.ProColorBox.setCurrentIndex(41)
        self.SerColorBox.setCurrentIndex(57)
        self.ThrColorBox.setCurrentIndex(60)
        self.TrpColorBox.setCurrentIndex(65)
        self.TyrColorBox.setCurrentIndex(68)
        self.ValColorBox.setCurrentIndex(72)
        self.backboneColorBox.setCurrentIndex(13)
        alaCompleter = QCompleter(decorative_blocks)
        alaCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        argCompleter = QCompleter(decorative_blocks)
        argCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        asnCompleter = QCompleter(decorative_blocks)
        asnCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        aspCompleter = QCompleter(decorative_blocks)
        aspCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        cysCompleter = QCompleter(decorative_blocks)
        cysCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        glnCompleter = QCompleter(decorative_blocks)
        glnCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        gluCompleter = QCompleter(decorative_blocks)
        gluCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        glyCompleter = QCompleter(decorative_blocks)
        glyCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        hisCompleter = QCompleter(decorative_blocks)
        hisCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        ileCompleter = QCompleter(decorative_blocks)
        ileCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        leuCompleter = QCompleter(decorative_blocks)
        leuCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        lysCompleter = QCompleter(decorative_blocks)
        lysCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        metCompleter = QCompleter(decorative_blocks)
        metCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        pheCompleter = QCompleter(decorative_blocks)
        pheCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        proCompleter = QCompleter(decorative_blocks)
        proCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        serCompleter = QCompleter(decorative_blocks)
        serCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        thrCompleter = QCompleter(decorative_blocks)
        thrCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        trpCompleter = QCompleter(decorative_blocks)
        trpCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        tyrCompleter = QCompleter(decorative_blocks)
        tyrCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        valCompleter = QCompleter(decorative_blocks)
        valCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        backboneCompleter = QCompleter(decorative_blocks)
        backboneCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.AlaColorBox.setCompleter(alaCompleter)
        self.ArgColorBox.setCompleter(argCompleter)
        self.AsnColorBox.setCompleter(asnCompleter)
        self.AspColorBox.setCompleter(aspCompleter)
        self.CysColorBox.setCompleter(cysCompleter)
        self.GlnColorBox.setCompleter(glnCompleter)
        self.GluColorBox.setCompleter(gluCompleter)
        self.GlyColorBox.setCompleter(glyCompleter)
        self.HisColorBox.setCompleter(hisCompleter)
        self.IleColorBox.setCompleter(ileCompleter)
        self.LeuColorBox.setCompleter(leuCompleter)
        self.LysColorBox.setCompleter(lysCompleter)
        self.MetColorBox.setCompleter(metCompleter)
        self.PheColorBox.setCompleter(pheCompleter)
        self.ProColorBox.setCompleter(proCompleter)
        self.SerColorBox.setCompleter(serCompleter)
        self.ThrColorBox.setCompleter(thrCompleter)
        self.TrpColorBox.setCompleter(trpCompleter)
        self.TyrColorBox.setCompleter(tyrCompleter)
        self.ValColorBox.setCompleter(valCompleter)
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
        # self.colorByBackboneCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        # self.colorByBackboneCheck.setChecked(False)
        # self.colorByBackboneCheck.setObjectName("colorByBackboneCheck")
        # self.colorByBackboneCheck.setToolTip("Color the backbones of the main models by the molecule number.")

        self.tools = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.tools.setFont(font)
        self.tools.setObjectName("tools")
        self.pScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.pScaleLabel.setObjectName("pScaleLabel")
        self.pScaleSpinBox = QtWidgets.QDoubleSpinBox(parent=self.centralwidget)

        self.pScaleSpinBox.setDecimals(1)
        self.pScaleSpinBox.setMinimum(1.0)
        self.pScaleSpinBox.setMaximum(50.0)
        self.pScaleSpinBox.setSingleStep(0.5)
        self.pScaleSpinBox.setObjectName("pScaleSpinBox")
        self.pScaleSpinBox.setToolTip("Scale the entire model by this factor.")
        # self.bScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)
        # self.bScaleLabel.setObjectName("bScaleLabel")
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

        # Define a new QPushButton
        self.colorStyleBox = MyComboBox(self.centralwidget)
        self.colorStyleBox.setObjectName("colorStyleBox")
        self.colorStyleBox.setGeometry(QtCore.QRect(210, 325, 87, 22))
        self.colorStyleBox.addItem("Residue")
        self.colorStyleBox.addItem("Type")
        self.colorStyleBox.addItem("Charge")
        self.colorStyleBox.addItem("Hydrophobicity")

        self.colorStyleLabel = QtWidgets.QLabel('<a href="style_link">Color Style</a>', parent=self.centralwidget)
        self.colorStyleLabel.setOpenExternalLinks(False)
        self.colorStyleLabel.setObjectName("colorStyleLabel")
        self.colorStyleLabel.setGeometry(QtCore.QRect(110, 325, 87, 22))

        self.bg.setGeometry(QtCore.QRect(-90, -50, 881, 500))

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
        self.tools.setGeometry(QtCore.QRect(10, 285, 75, 31))
        self.github.setGeometry(QtCore.QRect(10, 320, 75, 31))
        self.infoDatabaseHLine.setGeometry(QtCore.QRect(10, 350, 71, 16))

        self.pdbDatabaseLabel.setGeometry(QtCore.QRect(0, 360, 91, 21))
        self.rcsbButton.setGeometry(QtCore.QRect(10, 385, 75, 31))

        self.vSepLine.setGeometry(QtCore.QRect(90, 0, 20, 431))

        self.AlaColorLabel.setGeometry(QtCore.QRect(110, 5, 120, 21))
        self.AlaColorBox.setGeometry(QtCore.QRect(210, 5, 175, 22))

        self.ArgColorLabel.setGeometry(QtCore.QRect(395, 5, 120, 21))
        self.ArgColorBox.setGeometry(QtCore.QRect(510, 5, 175, 22))

        self.AsnColorLabel.setGeometry(QtCore.QRect(110, 30, 120, 21))
        self.AsnColorBox.setGeometry(QtCore.QRect(210, 30, 175, 22))

        self.AspColorLabel.setGeometry(QtCore.QRect(395, 30, 120, 21))
        self.AspColorBox.setGeometry(QtCore.QRect(510, 30, 175, 22))

        self.CysColorLabel.setGeometry(QtCore.QRect(110, 55, 120, 21))
        self.CysColorBox.setGeometry(QtCore.QRect(210, 55, 175, 22))

        self.GlnColorLabel.setGeometry(QtCore.QRect(395, 55, 120, 21))
        self.GlnColorBox.setGeometry(QtCore.QRect(510, 55, 175, 22))

        self.GluColorLabel.setGeometry(QtCore.QRect(110, 80, 120, 21))
        self.GluColorBox.setGeometry(QtCore.QRect(210, 80, 175, 22))

        self.GlyColorLabel.setGeometry(QtCore.QRect(395, 80, 120, 21))
        self.GlyColorBox.setGeometry(QtCore.QRect(510, 80, 175, 22))

        self.HisColorLabel.setGeometry(QtCore.QRect(110, 105, 120, 21))
        self.HisColorBox.setGeometry(QtCore.QRect(210, 105, 175, 22))

        self.IleColorLabel.setGeometry(QtCore.QRect(395, 105, 120, 21))
        self.IleColorBox.setGeometry(QtCore.QRect(510, 105, 175, 22))

        self.LeuColorLabel.setGeometry(QtCore.QRect(110, 130, 120, 21))
        self.LeuColorBox.setGeometry(QtCore.QRect(210, 130, 175, 22))

        self.LysColorLabel.setGeometry(QtCore.QRect(395, 130, 120, 21))
        self.LysColorBox.setGeometry(QtCore.QRect(510, 130, 175, 22))

        self.MetColorLabel.setGeometry(QtCore.QRect(110, 155, 120, 21))
        self.MetColorBox.setGeometry(QtCore.QRect(210, 155, 175, 22))

        self.PheColorLabel.setGeometry(QtCore.QRect(395, 155, 120, 21))
        self.PheColorBox.setGeometry(QtCore.QRect(510, 155, 175, 22))

        self.ProColorLabel.setGeometry(QtCore.QRect(110, 180, 120, 21))
        self.ProColorBox.setGeometry(QtCore.QRect(210, 180, 175, 22))

        self.SerColorLabel.setGeometry(QtCore.QRect(395, 180, 120, 21))
        self.SerColorBox.setGeometry(QtCore.QRect(510, 180, 175, 22))

        self.ThrColorLabel.setGeometry(QtCore.QRect(110, 205, 120, 21))
        self.ThrColorBox.setGeometry(QtCore.QRect(210, 205, 175, 22))

        self.TrpColorLabel.setGeometry(QtCore.QRect(395, 205, 120, 21))
        self.TrpColorBox.setGeometry(QtCore.QRect(510, 205, 175, 22))

        self.TyrColorLabel.setGeometry(QtCore.QRect(110, 230, 120, 21))
        self.TyrColorBox.setGeometry(QtCore.QRect(210, 230, 175, 22))

        self.ValColorLabel.setGeometry(QtCore.QRect(395, 230, 120, 21))
        self.ValColorBox.setGeometry(QtCore.QRect(510, 230, 175, 22))

        self.backboneColorLabel.setGeometry(QtCore.QRect(110, 265, 120, 21))
        self.backboneColorBox.setGeometry(QtCore.QRect(210, 265, 175, 22))
        self.showBackboneCheck.setGeometry(QtCore.QRect(395, 265, 121, 17))
        self.backboneScaleSpinBox.setGeometry(QtCore.QRect(510, 265, 62, 22))

        #self.colorByBackboneCheck.setGeometry(QtCore.QRect(240, 530, 155, 21))
        #self.bScaleLabel.setGeometry(QtCore.QRect(110, 270, 111, 21))

        self.pScaleLabel.setGeometry(QtCore.QRect(110, 295, 71, 21))
        self.pScaleSpinBox.setGeometry(QtCore.QRect(210, 295, 62, 22))

        self.otherMoleculeCheck.setGeometry(QtCore.QRect(395, 325, 131, 17))
        self.aScaleLabel.setGeometry(QtCore.QRect(395, 295, 61, 21))
        self.aScaleSpinBox.setGeometry(QtCore.QRect(510, 295, 62, 22))

        self.selectPDBFileButton.setGeometry(QtCore.QRect(110, 350, 91, 23))
        self.orText.setGeometry(QtCore.QRect(210, 350, 31, 21))
        self.selectIncludedPDBButton.setGeometry(QtCore.QRect(250, 350, 141, 23))
        self.andText.setGeometry(QtCore.QRect(400, 350, 31, 21))
        self.selectMinecraftSaveButton.setGeometry(QtCore.QRect(450, 350, 141, 23))

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
        self.help.raise_()
        self.rcsbButton.raise_()
        self.mc2pdbLabel.raise_()
        self.pdbDatabaseLabel.raise_()
        self.modeInfoHLine.raise_()
        self.infoDatabaseHLine.raise_()
        self.tools.raise_()
        self.backboneColorLabel.raise_()
        #self.sidechainColorLabel.raise_()
        #self.otherColorLabel.raise_()
        # self.oColorBox.raise_()
        # self.nColorBox.raise_()
        # self.pColorBox.raise_()
        #self.otherColorBox.raise_()
        self.AlaColorLabel.raise_()
        self.AlaColorBox.raise_()
        self.ArgColorLabel.raise_()
        self.ArgColorBox.raise_()
        self.AsnColorLabel.raise_()
        self.AsnColorBox.raise_()
        self.AspColorLabel.raise_()
        self.AspColorBox.raise_()
        self.CysColorLabel.raise_()
        self.CysColorBox.raise_()
        self.GlnColorLabel.raise_()
        self.GlnColorBox.raise_()
        self.GluColorLabel.raise_()
        self.GluColorBox.raise_()
        self.GlyColorLabel.raise_()
        self.GlyColorBox.raise_()
        self.HisColorLabel.raise_()
        self.HisColorBox.raise_()
        self.IleColorLabel.raise_()
        self.IleColorBox.raise_()
        self.LeuColorLabel.raise_()
        self.LeuColorBox.raise_()
        self.LysColorLabel.raise_()
        self.LysColorBox.raise_()
        self.MetColorLabel.raise_()
        self.MetColorBox.raise_()
        self.PheColorLabel.raise_()
        self.PheColorBox.raise_()
        self.ProColorLabel.raise_()
        self.ProColorBox.raise_()
        self.SerColorLabel.raise_()
        self.SerColorBox.raise_()
        self.ThrColorLabel.raise_()
        self.ThrColorBox.raise_()
        self.TrpColorLabel.raise_()
        self.TrpColorBox.raise_()
        self.TyrColorLabel.raise_()
        self.TyrColorBox.raise_()
        self.ValColorLabel.raise_()
        self.ValColorBox.raise_()
        self.backboneColorBox.raise_()
        #self.sidechainColorBox.raise_()
        self.aScaleLabel.raise_()
        # self.showAtomsCheck.raise_()
        self.otherMoleculeCheck.raise_()
        #self.meshCheck.raise_()
        self.aScaleSpinBox.raise_()
        self.showBackboneCheck.raise_()
        #self.showSidechainCheck.raise_()
        #self.colorByBackboneCheck.raise_()
        self.pScaleLabel.raise_()
        self.pScaleSpinBox.raise_()
        #self.bScaleLabel.raise_()
        self.backboneScaleSpinBox.raise_()
        self.selectIncludedPDBButton.raise_()
        self.selectMinecraftSaveButton.raise_()
        self.simpleOutputCheck.raise_()
        self.selectPDBFileButton.raise_()
        self.createFunctionsButton.raise_()
        self.orText.raise_()
        self.andText.raise_()
        self.colorStyleBox.raise_()
        self.setCentralWidget(self.centralwidget)
        self.colorStyleLabel.raise_()

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
        self.colorStyleBox.currentTextChanged.connect(lambda: self.handle_colorStyle_button(self.colorStyleBox))
        self.tools.clicked.connect(self.handle_tool_mode)

        #self.otherColorBox.focusOut.connect(lambda: self.check_input(self.otherColorBox, decorative_blocks))
        self.backboneColorBox.focusOut.connect(lambda: self.check_input(self.backboneColorBox, decorative_blocks))
        self.AlaColorBox.focusOut.connect(lambda: (self.check_input(self.AlaColorBox, decorative_blocks), self.backboneColorBox.update()))
        self.ArgColorBox.focusOut.connect(lambda: (self.check_input(self.ArgColorBox, decorative_blocks), self.backboneColorBox.update()))
        self.AsnColorBox.focusOut.connect(lambda: (self.check_input(self.AsnColorBox, decorative_blocks), self.backboneColorBox.update()))
        self.AspColorBox.focusOut.connect(lambda: (self.check_input(self.AspColorBox, decorative_blocks), self.backboneColorBox.update()))
        self.CysColorBox.focusOut.connect(lambda: (self.check_input(self.CysColorBox, decorative_blocks), self.backboneColorBox.update()))
        self.GlnColorBox.focusOut.connect(lambda: (self.check_input(self.GlnColorBox, decorative_blocks), self.backboneColorBox.update()))
        self.GluColorBox.focusOut.connect(lambda: self.check_input(self.GluColorBox, decorative_blocks))
        self.GlyColorBox.focusOut.connect(lambda: self.check_input(self.GlyColorBox, decorative_blocks))
        self.HisColorBox.focusOut.connect(lambda: self.check_input(self.HisColorBox, decorative_blocks))
        self.IleColorBox.focusOut.connect(lambda: self.check_input(self.IleColorBox, decorative_blocks))
        self.LeuColorBox.focusOut.connect(lambda: self.check_input(self.LeuColorBox, decorative_blocks))
        self.LysColorBox.focusOut.connect(lambda: self.check_input(self.LysColorBox, decorative_blocks))
        self.MetColorBox.focusOut.connect(lambda: self.check_input(self.MetColorBox, decorative_blocks))
        self.PheColorBox.focusOut.connect(lambda: self.check_input(self.PheColorBox, decorative_blocks))
        self.ProColorBox.focusOut.connect(lambda: self.check_input(self.ProColorBox, decorative_blocks))
        self.SerColorBox.focusOut.connect(lambda: self.check_input(self.SerColorBox, decorative_blocks))
        self.ThrColorBox.focusOut.connect(lambda: self.check_input(self.ThrColorBox, decorative_blocks))
        self.TrpColorBox.focusOut.connect(lambda: self.check_input(self.TrpColorBox, decorative_blocks))
        self.TyrColorBox.focusOut.connect(lambda: self.check_input(self.TyrColorBox, decorative_blocks))
        self.ValColorBox.focusOut.connect(lambda: self.check_input(self.ValColorBox, decorative_blocks))
        self.showBackboneCheck.stateChanged.connect(self.on_showBackboneCheck_changed)

    def handle_colorStyle_button(self, combobox):
        text = combobox.currentText()
        if text == "Residue":
            self.AlaColorBox.setCurrentIndex(0)
            self.ArgColorBox.setCurrentIndex(2)
            self.AsnColorBox.setCurrentIndex(5)
            self.AspColorBox.setCurrentIndex(8)
            self.CysColorBox.setCurrentIndex(11)
            self.GlnColorBox.setCurrentIndex(14)
            self.GluColorBox.setCurrentIndex(17)
            self.GlyColorBox.setCurrentIndex(20)
            self.HisColorBox.setCurrentIndex(23)
            self.IleColorBox.setCurrentIndex(26)
            self.LeuColorBox.setCurrentIndex(29)
            self.LysColorBox.setCurrentIndex(32)
            self.MetColorBox.setCurrentIndex(35)
            self.PheColorBox.setCurrentIndex(38)
            self.ProColorBox.setCurrentIndex(41)
            self.SerColorBox.setCurrentIndex(57)
            self.ThrColorBox.setCurrentIndex(60)
            self.TrpColorBox.setCurrentIndex(65)
            self.TyrColorBox.setCurrentIndex(68)
            self.ValColorBox.setCurrentIndex(72)
        if text == "Type":
            # Update the colorBox with text that is not currently indexed
            self.AlaColorBox.setCurrentIndex(self.AlaColorBox.findText("green_wool"))
            self.ArgColorBox.setCurrentIndex(self.ArgColorBox.findText("red_wool"))
            self.AsnColorBox.setCurrentIndex(self.AsnColorBox.findText("blue_wool"))
            self.AspColorBox.setCurrentIndex(self.AspColorBox.findText("blue_wool"))
            self.CysColorBox.setCurrentIndex(self.CysColorBox.findText("orange_wool"))
            self.GlnColorBox.setCurrentIndex(self.GlnColorBox.findText("yellow_wool"))
            self.GluColorBox.setCurrentIndex(self.GluColorBox.findText("blue_wool"))
            self.GlyColorBox.setCurrentIndex(self.GlyColorBox.findText("orange_wool"))
            self.HisColorBox.setCurrentIndex(self.HisColorBox.findText("red_wool"))
            self.IleColorBox.setCurrentIndex(self.IleColorBox.findText("green_wool"))
            self.LeuColorBox.setCurrentIndex(self.LeuColorBox.findText("green_wool"))
            self.LysColorBox.setCurrentIndex(self.LysColorBox.findText("red_wool"))
            self.MetColorBox.setCurrentIndex(self.MetColorBox.findText("green_wool"))
            self.PheColorBox.setCurrentIndex(self.PheColorBox.findText("green_wool"))
            self.ProColorBox.setCurrentIndex(self.ProColorBox.findText("orange_wool"))
            self.SerColorBox.setCurrentIndex(self.SerColorBox.findText("yellow_wool"))
            self.ThrColorBox.setCurrentIndex(self.ThrColorBox.findText("yellow_wool"))
            self.TrpColorBox.setCurrentIndex(self.TrpColorBox.findText("green_wool"))
            self.TyrColorBox.setCurrentIndex(self.TyrColorBox.findText("green_wool"))
            self.ValColorBox.setCurrentIndex(self.ValColorBox.findText("green_wool"))

        if text == "Hydrophobicity":
            # Update the colorBox with text that is not currently indexed
            if self.AlaColorBox.findText("snow_block") <= 0:
                self.AlaColorBox.addItem(create_icon(hex_dict["snow_block"]), "snow_block")
            self.AlaColorBox.setCurrentIndex(self.AlaColorBox.findText("snow_block"))

            if self.ArgColorBox.findText("copper_block") <= 0:
                self.ArgColorBox.addItem(create_icon(hex_dict["copper_block"]), "copper_block")
            self.ArgColorBox.setCurrentIndex(self.ArgColorBox.findText("copper_block"))

            if self.AsnColorBox.findText("quartz_block") <= 0:
                self.AsnColorBox.addItem(create_icon(hex_dict["quartz_block"]), "quartz_block")
            self.AsnColorBox.setCurrentIndex(self.AsnColorBox.findText("quartz_block"))

            if self.AspColorBox.findText("nether_wart_block") <= 0:
                self.AspColorBox.addItem(create_icon(hex_dict["nether_wart_block"]), "nether_wart_block")
            self.AspColorBox.setCurrentIndex(self.AspColorBox.findText("nether_wart_block"))

            if self.CysColorBox.findText("diorite") <= 0:
                self.CysColorBox.addItem(create_icon(hex_dict["diorite"]), "diorite")
            self.CysColorBox.setCurrentIndex(self.CysColorBox.findText("diorite"))

            if self.GlnColorBox.findText("stripped_cherry_log") <= 0:
                self.GlnColorBox.addItem(create_icon(hex_dict["stripped_cherry_log"]), "stripped_cherry_log")
            self.GlnColorBox.setCurrentIndex(self.GlnColorBox.findText("stripped_cherry_log"))

            if self.GluColorBox.findText("red_wool") <= 0:
                self.GluColorBox.addItem(create_icon(hex_dict["red_wool"]), "red_wool")
            self.GluColorBox.setCurrentIndex(self.GluColorBox.findText("red_wool"))

            if self.GlyColorBox.findText("snow_block") <= 0:
                self.GlyColorBox.addItem(create_icon(hex_dict["snow_block"]), "snow_block")
            self.GlyColorBox.setCurrentIndex(self.GlyColorBox.findText("snow_block"))

            if self.HisColorBox.findText("pink_concrete") <= 0:
                self.HisColorBox.addItem(create_icon(hex_dict["pink_concrete"]), "pink_concrete")
            self.HisColorBox.setCurrentIndex(self.HisColorBox.findText("pink_concrete"))

            if self.IleColorBox.findText("light_gray_glazed_terracotta") <= 0:
                self.IleColorBox.addItem(create_icon(hex_dict["light_gray_glazed_terracotta"]), "light_gray_glazed_terracotta")
            self.IleColorBox.setCurrentIndex(self.IleColorBox.findText("light_gray_glazed_terracotta"))

            if self.LeuColorBox.findText("packed_ice") <= 0:
                self.LeuColorBox.addItem(create_icon(hex_dict["packed_ice"]), "packed_ice")
            self.LeuColorBox.setCurrentIndex(self.LeuColorBox.findText("packed_ice"))

            if self.LysColorBox.findText("red_mushroom_block") <= 0:
                self.LysColorBox.addItem(create_icon(hex_dict["red_mushroom_block"]), "red_mushroom_block")
            self.LysColorBox.setCurrentIndex(self.LysColorBox.findText("red_mushroom_block"))

            if self.MetColorBox.findText("white_shulker_box") <= 0:
                self.MetColorBox.addItem(create_icon(hex_dict["white_shulker_box"]), "white_shulker_box")
            self.MetColorBox.setCurrentIndex(self.MetColorBox.findText("white_shulker_box"))

            if self.PheColorBox.findText("tube_coral_block") <= 0:
                self.PheColorBox.addItem(create_icon(hex_dict["tube_coral_block"]), "tube_coral_block")
            self.PheColorBox.setCurrentIndex(self.PheColorBox.findText("tube_coral_block"))

            if self.ProColorBox.findText("cherry_planks") <= 0:
                self.ProColorBox.addItem(create_icon(hex_dict["cherry_planks"]), "cherry_planks")
            self.ProColorBox.setCurrentIndex(self.ProColorBox.findText("cherry_planks"))

            if self.SerColorBox.findText("snow_block") <= 0:
                self.SerColorBox.addItem(create_icon(hex_dict["snow_block"]), "snow_block")
            self.SerColorBox.setCurrentIndex(self.SerColorBox.findText("snow_block"))

            if self.ThrColorBox.findText("snow_block") <= 0:
                self.ThrColorBox.addItem(create_icon(hex_dict["snow_block"]), "snow_block")
            self.ThrColorBox.setCurrentIndex(self.ThrColorBox.findText("snow_block"))

            if self.TrpColorBox.findText("blue_concrete") <= 0:
                self.TrpColorBox.addItem(create_icon(hex_dict["blue_concrete"]), "blue_concrete")
            self.TrpColorBox.setCurrentIndex(self.TrpColorBox.findText("blue_concrete"))

            if self.TyrColorBox.findText("blue_ice") <= 0:
                self.TyrColorBox.addItem(create_icon(hex_dict["blue_ice"]), "blue_ice")
            self.TyrColorBox.setCurrentIndex(self.TyrColorBox.findText("blue_ice"))

            if self.ValColorBox.findText("snow_block") <= 0:
                self.ValColorBox.addItem(create_icon(hex_dict["snow_block"]), "snow_block")
            self.ValColorBox.setCurrentIndex(self.ValColorBox.findText("snow_block"))

        if text == "Charge":
            # Update the colorBox with text that is not currently indexed
            if self.AlaColorBox.findText("pearlescent_froglight") <= 0:
                self.AlaColorBox.addItem(create_icon(hex_dict["pearlescent_froglight"]), "pearlescent_froglight")
            self.AlaColorBox.setCurrentIndex(self.AlaColorBox.findText("pearlescent_froglight"))

            if self.ArgColorBox.findText("emerald_block") <= 0:
                self.ArgColorBox.addItem(create_icon(hex_dict["emerald_block"]), "emerald_block")
            self.ArgColorBox.setCurrentIndex(self.ArgColorBox.findText("emerald_block"))

            if self.AsnColorBox.findText("end_stone") <= 0:
                self.AsnColorBox.addItem(create_icon(hex_dict["end_stone"]), "end_stone")
            self.AsnColorBox.setCurrentIndex(self.AsnColorBox.findText("end_stone"))

            if self.AspColorBox.findText("cobblestone") <= 0:
                self.AspColorBox.addItem(create_icon(hex_dict["cobblestone"]), "cobblestone")
            self.AspColorBox.setCurrentIndex(self.AspColorBox.findText("cobblestone"))

            if self.CysColorBox.findText("cherry_leaves") <= 0:
                self.CysColorBox.addItem(create_icon(hex_dict["cherry_leaves"]), "cherry_leaves")
            self.CysColorBox.setCurrentIndex(self.CysColorBox.findText("cherry_leaves"))

            if self.GlnColorBox.findText("end_stone_bricks") <= 0:
                self.GlnColorBox.addItem(create_icon(hex_dict["end_stone_bricks"]), "end_stone_bricks")
            self.GlnColorBox.setCurrentIndex(self.GlnColorBox.findText("end_stone_bricks"))

            if self.GluColorBox.findText("light_gray_wool") <= 0:
                self.GluColorBox.addItem(create_icon(hex_dict["light_gray_wool"]), "light_gray_wool")
            self.GluColorBox.setCurrentIndex(self.GluColorBox.findText("light_gray_wool"))

            if self.GlyColorBox.findText("snow_block") <= 0:
                self.GlyColorBox.addItem(create_icon(hex_dict["snow_block"]), "snow_block")
            self.GlyColorBox.setCurrentIndex(self.GlyColorBox.findText("snow_block"))

            if self.HisColorBox.findText("white_glazed_terracotta") <= 0:
                self.HisColorBox.addItem(create_icon(hex_dict["white_glazed_terracotta"]), "white_glazed_terracotta")
            self.HisColorBox.setCurrentIndex(self.HisColorBox.findText("white_glazed_terracotta"))

            if self.IleColorBox.findText("red_mushroom_block") <= 0:
                self.IleColorBox.addItem(create_icon(hex_dict["red_mushroom_block"]), "red_mushroom_block")
            self.IleColorBox.setCurrentIndex(self.IleColorBox.findText("red_mushroom_block"))

            if self.LeuColorBox.findText("pink_wool") <= 0:
                self.LeuColorBox.addItem(create_icon(hex_dict["pink_wool"]), "pink_wool")
            self.LeuColorBox.setCurrentIndex(self.LeuColorBox.findText("pink_wool"))

            if self.LysColorBox.findText("weathered_copper") <= 0:
                self.LysColorBox.addItem(create_icon(hex_dict["weathered_copper"]), "weathered_copper")
            self.LysColorBox.setCurrentIndex(self.LysColorBox.findText("weathered_copper"))

            if self.MetColorBox.findText("ochre_froglight") <= 0:
                self.MetColorBox.addItem(create_icon(hex_dict["ochre_froglight"]), "ochre_froglight")
            self.MetColorBox.setCurrentIndex(self.MetColorBox.findText("ochre_froglight"))

            if self.PheColorBox.findText("cherry_planks") <= 0:
                self.PheColorBox.addItem(create_icon(hex_dict["cherry_planks"]), "cherry_planks")
            self.PheColorBox.setCurrentIndex(self.PheColorBox.findText("cherry_planks"))

            if self.ProColorBox.findText("verdant_froglight") <= 0:
                self.ProColorBox.addItem(create_icon(hex_dict["verdant_froglight"]), "verdant_froglight")
            self.ProColorBox.setCurrentIndex(self.ProColorBox.findText("verdant_froglight"))

            if self.SerColorBox.findText("snow_block") <= 0:
                self.SerColorBox.addItem(create_icon(hex_dict["snow_block"]), "snow_block")
            self.SerColorBox.setCurrentIndex(self.SerColorBox.findText("snow_block"))

            if self.ThrColorBox.findText("snow_block") <= 0:
                self.ThrColorBox.addItem(create_icon(hex_dict["snow_block"]), "snow_block")
            self.ThrColorBox.setCurrentIndex(self.ThrColorBox.findText("snow_block"))

            if self.TrpColorBox.findText("snow_block") <= 0:
                self.TrpColorBox.addItem(create_icon(hex_dict["snow_block"]), "snow_block")
            self.TrpColorBox.setCurrentIndex(self.TrpColorBox.findText("snow_block"))

            if self.TyrColorBox.findText("white_wool") <= 0:
                self.TyrColorBox.addItem(create_icon(hex_dict["white_wool"]), "white_wool")
            self.TyrColorBox.setCurrentIndex(self.TyrColorBox.findText("white_wool"))

            if self.ValColorBox.findText("pink_concrete") <= 0:
                self.ValColorBox.addItem(create_icon(hex_dict["pink_concrete"]), "pink_concrete")
            self.ValColorBox.setCurrentIndex(self.ValColorBox.findText("pink_concrete"))


    def on_showBackboneCheck_changed(self, state):
        self.backboneColorBox.setEnabled(state != 0)
        self.backboneScaleSpinBox.setEnabled(state !=0)

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
            #QMessageBox.critical(None, "Error", "Remember to select a Minecraft save.")
            return
        self.user_minecraft_save = self.selectMinecraft.selected_directory

    def handle_included_pdb_button(self):
        self.includedPDB = IncludedPDBPopup()
        self.includedPDB.show()
        self.includedPDB.selected.connect(self.save_selected_text)

    def save_selected_text(self, text):
        self.selected_text = text
        #make global variable for pdb file
        self.user_pdb_file = f"presets/{text}.pdb"

    def handle_make_function_button(self):
        # Create a dictionary to store the user options
        config_data = {'atoms': {},
                       'amino_acids': {}}

        # Add the current text of each combobox to the dictionary
        config_data['atoms']['O'] = 'red_wool'
        config_data['atoms']['N'] = 'blue_wool'
        config_data['atoms']['P'] = 'lime_wool'
        config_data['atoms']['S'] = 'yellow_wool'
        config_data['atoms']['C'] = 'black_wool'
        config_data['atoms']['FE'] = 'iron_block'
        config_data['atoms']['other_atom'] = 'pink_concrete'
        config_data['atoms']['backbone_atom'] = self.backboneColorBox.currentText()
        config_data['atoms']['sidechain_atom'] = 'sidechain_atom'

        config_data['amino_acids']['ALA'] = self.AlaColorBox.currentText()
        config_data['amino_acids']['ARG'] = self.ArgColorBox.currentText()
        config_data['amino_acids']['ASN'] = self.AsnColorBox.currentText()
        config_data['amino_acids']['ASP'] = self.AspColorBox.currentText()
        config_data['amino_acids']['CYS'] = self.CysColorBox.currentText()
        config_data['amino_acids']['GLN'] = self.GlnColorBox.currentText()
        config_data['amino_acids']['GLU'] = self.GluColorBox.currentText()
        config_data['amino_acids']['GLY'] = self.GlyColorBox.currentText()
        config_data['amino_acids']['HIS'] = self.HisColorBox.currentText()
        config_data['amino_acids']['ILE'] = self.IleColorBox.currentText()
        config_data['amino_acids']['LEU'] = self.LeuColorBox.currentText()
        config_data['amino_acids']['LYS'] = self.LysColorBox.currentText()
        config_data['amino_acids']['MET'] = self.MetColorBox.currentText()
        config_data['amino_acids']['PHE'] = self.PheColorBox.currentText()
        config_data['amino_acids']['PRO'] = self.ProColorBox.currentText()
        config_data['amino_acids']['SER'] = self.SerColorBox.currentText()
        config_data['amino_acids']['THR'] = self.ThrColorBox.currentText()
        config_data['amino_acids']['TRP'] = self.TrpColorBox.currentText()
        config_data['amino_acids']['TYR'] = self.TyrColorBox.currentText()
        config_data['amino_acids']['VAL'] = self.ValColorBox.currentText()

        config_data['color_style'] = self.colorStyleBox.currentText()

        config_data['backbone_size'] = self.backboneScaleSpinBox.value()
        config_data['atom_scale'] = self.aScaleSpinBox.value()
        config_data['scale'] = self.pScaleSpinBox.value()

        # Add the checked state of each checkbox to the dictionary
        config_data['show_hetatm'] = self.otherMoleculeCheck.isChecked()
        config_data['backbone'] = self.showBackboneCheck.isChecked()
        config_data['sidechain'] = True
        config_data['by_chain'] = False
        config_data['simple'] = self.simpleOutputCheck.isChecked()

        # Add the current paths of the files and directories to the dictionary
        # Replace 'file_path' and 'save_path' with the actual paths
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
            pass
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

    def handle_tool_mode(self):
        try:
            from UI.tool_window import ToolWindow
            self.tool_window = ToolWindow()
            self.tool_window.show()
            self.hide()
        except Exception as e:
            print(f"Error in handle_space_filling_mode: {e}")

    def show_information_box(self, title_text, text, icon_path):
        self.info_box = InformationBox()
        self.info_box.set_text(text)
        self.info_box.set_title(title_text)
        self.info_box.set_icon(icon_path)
        self.info_box.show()

    def retranslateUi(self, AAWindow):
        _translate = QtCore.QCoreApplication.translate
        self.switchModeLabel.setText(_translate("AAWindow", "Switch Mode"))
        self.CustomMode.setText(_translate("AAWindow", "Custom"))
        self.SkeletonMode.setText(_translate("AAWindow", "Skeleton"))
        self.XRayMode.setText(_translate("AAWindow", "X-Ray"))
        self.SpaceFillingMode.setText(_translate("AAWindow", "Space Filling"))
        self.AminoAcidMode.setText(_translate("AAWindow", "Amino Acids"))
        self.RibbonMode.setText(_translate("AAWindow", "Ribbon"))
        self.github.setText(_translate("AAWindow", "Github"))
        self.help.setText(_translate("AAWindow", "Help"))
        self.rcsbButton.setText(_translate("AAWindow", "RCSB.org"))
        self.mc2pdbLabel.setText(_translate("AAWindow", "PDB2MC"))
        self.pdbDatabaseLabel.setText(_translate("AAWindow", "PDB Database"))
        self.backboneColorLabel.setText(_translate("AAWindow", "Select backbone:"))
        self.AlaColorLabel.setText(_translate("AAWindow", "Select Alanine:"))
        self.ArgColorLabel.setText(_translate("AAWindow", "Select Arginine:"))
        self.AsnColorLabel.setText(_translate("AAWindow", "Select Asparagine:"))
        self.AspColorLabel.setText(_translate("AAWindow", "Select Aspartate:"))
        self.CysColorLabel.setText(_translate("AAWindow", "Select Cysteine:"))
        self.GlnColorLabel.setText(_translate("AAWindow", "Select Glutamine:"))
        self.GluColorLabel.setText(_translate("AAWindow", "Select Glutamate:"))
        self.GlyColorLabel.setText(_translate("AAWindow", "Select Glycine:"))
        self.HisColorLabel.setText(_translate("AAWindow", "Select Histidine:"))
        self.IleColorLabel.setText(_translate("AAWindow", "Select Isoleucine:"))
        self.LeuColorLabel.setText(_translate("AAWindow", "Select Leucine:"))
        self.LysColorLabel.setText(_translate("AAWindow", "Select Lysine:"))
        self.MetColorLabel.setText(_translate("AAWindow", "Select Methionine:"))
        self.PheColorLabel.setText(_translate("AAWindow", "Select Phenylalanine:"))
        self.ProColorLabel.setText(_translate("AAWindow", "Select Proline:"))
        self.SerColorLabel.setText(_translate("AAWindow", "Select Serine:"))
        self.ThrColorLabel.setText(_translate("AAWindow", "Select Threonine:"))
        self.TrpColorLabel.setText(_translate("AAWindow", "Select Tryptophan:"))
        self.TyrColorLabel.setText(_translate("AAWindow", "Select Tyrosine:"))
        self.ValColorLabel.setText(_translate("AAWindow", "Select Valine:"))
        self.tools.setText(_translate("AAWindow", "Tools"))
        self.aScaleLabel.setText(_translate("AAWindow", "Atom scale:"))
        self.otherMoleculeCheck.setText(_translate("AAWindow", "Show other molecules"))
        self.showBackboneCheck.setText(_translate("AAWindow", "Show backbone"))
        self.pScaleLabel.setText(_translate("AAWindow", "Protein scale:"))
        self.selectIncludedPDBButton.setText(_translate("AAWindow", "Select Included PDB File"))
        self.selectMinecraftSaveButton.setText(_translate("AAWindow", "Select Minecraft Save"))
        self.simpleOutputCheck.setText(_translate("AAWindow", "Simple output"))
        self.selectPDBFileButton.setText(_translate("AAWindow", "Select PDB File"))
        self.createFunctionsButton.setText(_translate("AAWindow", "Create Minecraft Functions"))
        self.orText.setText(_translate("AAWindow", "or"))
        self.andText.setText(_translate("AAWindow", "and"))


def set_combobox_by_text(combobox, text):
    index = combobox.findText(text)
    if index >= 0:  # If the text is found
        combobox.setCurrentIndex(index)

def create_icon(hex_color: str, size: int = 100) -> QIcon:

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
    main_window = AAWindow()
    main_window.show()
    try:
        app.exec()
    except KeyboardInterrupt:
        pass

