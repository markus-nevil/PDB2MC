from PyQt6.QtWidgets import QApplication, QMainWindow, QCompleter, QDialog, QVBoxLayout, QLabel, QProgressBar, QMessageBox
from PyQt6.QtGui import QDesktopServices, QColor, QIcon, QPainter, QPixmap
from PyQt6 import QtCore, QtGui, QtWidgets
import os
import sys
import importlib
import pkg_resources
from .utilities import InformationBox, MyComboBox, IncludedPDBPopup, MinecraftPopup, FileExplorerPopup, SequenceSelectorPopup, get_presets_path
from PDB2MC.variables import decorative_blocks, hex_dict
import pandas as pd
from PDB2MC import minecraft_functions as mcf, pdb_manipulation as pdbm, skeleton
from PyQt6.QtCore import QThread, pyqtSignal
from .sidebar import Sidebar, SIDEBAR_WIDTH


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

def get_images_path():
    """
    Return a deterministic images directory path.
    For development: UI/images inside the package folder.
    For frozen executables you may adapt this to your bundler needs.
    """
    try:
        # Normal script location: folder/UI/images
        current_dir = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(current_dir, 'images')
        if os.path.isdir(images_dir):
            return images_dir
        # fallback: parent/UI/images
        images_dir = os.path.normpath(os.path.join(current_dir, '..', 'UI', 'images'))
        return images_dir
    except Exception:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')

class SkeletonWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Keep working directory unchanged (do not os.chdir)

        self.user_pdb_file = None
        self.user_minecraft_save = None
        self.setWindowTitle("Skeleton Mode")
        # Set window icon using deterministic images path
        try:
            icon_path = os.path.join(get_images_path(), 'icons', 'logo.png')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                # fallback relative path
                fallback = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', 'icons', 'logo.png')
                if os.path.exists(fallback):
                    self.setWindowIcon(QIcon(fallback))
        except Exception:
            pass

        self.resize(450, 450)
        self.centralwidget = QtWidgets.QWidget(parent=self)
        self.centralwidget.setObjectName("centralwidget")

        # --- UI layout configuration (one place to modify positions/sizes) ---
        # geometry tuple format: (X, Y, WIDTH, HEIGHT)
        # indices: X = 0, Y = 1, WIDTH = 2, HEIGHT = 3
        UI_GEOMETRY = {
            "bg": (-90, -50, 881, 500),
            "backboneColorLabel": (110, 10, 120, 21),
            "backboneColorBox": (240, 10, 175, 22),
            "showBackboneCheck": (240, 37, 121, 17),
            "colorByBackboneCheck": (240, 53, 155, 21),
            "bScaleLabel": (110, 80, 111, 21),
            "backboneScaleSpinBox": (240, 80, 62, 22),
            "pScaleLabel": (110, 108, 71, 21),
            "pScaleSpinBox": (240, 108, 62, 22),
            "sidechainColorLabel": (110, 150, 120, 21),
            "sidechainColorBox": (240, 150, 175, 22),
            "showSidechainCheck": (240, 175, 121, 17),
            "otherColorLabel": (110, 210, 121, 21),
            "otherColorBox": (240, 210, 175, 22),
            "otherMoleculeCheck": (240, 238, 131, 17),
            "aScaleLabel": (110, 260, 61, 21),
            "aScaleSpinBox": (240, 260, 62, 22),
            "selectPDBFileButton": (110, 315, 91, 23),
            "orText": (210, 315, 31, 21),
            "selectIncludedPDBButton": (250, 315, 141, 23),
            "andText": (210, 350, 31, 21),
            "selectMinecraftSaveButton": (250, 350, 141, 23),
            "simpleOutputCheck": (110, 410, 100, 31),
            "createFunctionsButton": (230, 385, 181, 31),
            "modifyResiduesButton": (100, 370, 150, 31),
            "selectedPDBLabel": (110, 340, 300, 21),
            "selectedMinecraftLabel": (110, 370, 300, 21),
        }

        # small per-widget font sizes (point sizes); use None to keep default
        UI_FONTS = {
            "selectPDBFileButton": None,
            "createFunctionsButton": 11,
            "orText": 9,
            "andText": 9,
            "modifyResiduesButton": 10,
            "selectedPDBLabel": None,
            "selectedMinecraftLabel": None,
        }

        # --- Sidebar: instantiate the new Sidebar widget and place at left ---
        try:
            # Use sidebar master width constant so changing SIDEBAR_WIDTH updates placement
            self.sidebar = Sidebar(self.centralwidget, width=SIDEBAR_WIDTH)
        except Exception:
            self.sidebar = QtWidgets.QWidget(self.centralwidget)
            self.sidebar.setFixedWidth(SIDEBAR_WIDTH)

        # initial placement: set geometry using centralwidget height if available
        try:
            initial_h = self.centralwidget.height() if self.centralwidget.height() > 0 else 400
            self.sidebar.setGeometry(0, 0, SIDEBAR_WIDTH, initial_h)
            if hasattr(self.sidebar, "setFixedHeight"):
                self.sidebar.setFixedHeight(initial_h)
        except Exception:
            pass

        # --- Restore the remainder of the UI (from skeleton_old) ---
        # Create widgets that belong in the content area / centralwidget.
        # DO NOT recreate the left-side controls that Sidebar already owns.

        self.bg = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(7)
        self.bg.setFont(font)
        self.bg.setText("")
        # try to load background safely via images path
        try:
            bg_pix = os.path.join(get_images_path(), "MC2PDB bg.png")
            if not os.path.exists(bg_pix):
                # fallback path used in old code
                bg_pix = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "MC2PDB bg.png")
            if os.path.exists(bg_pix):
                self.bg.setPixmap(QtGui.QPixmap(bg_pix))
        except Exception:
            pass
        self.bg.setScaledContents(True)
        self.bg.setObjectName("bg")

        # Color/option labels and comboboxes
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

        # populate color comboboxes using helper create_icon
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
                try:
                    color_box.addItem(create_icon(hex_dict[value]), value)
                except Exception:
                    # fallback: add without icon if anything fails
                    color_box.addItem(value)
        # separators as in old UI
        try:
            color_box.insertSeparator(16)
            color_box.insertSeparator(33)
            color_box.insertSeparator(50)
            color_box.insertSeparator(67)
        except Exception:
            pass

        # Set default indices
        try:
            self.otherColorBox.setCurrentIndex(10)
            self.sidechainColorBox.setCurrentIndex(13)
            self.backboneColorBox.setCurrentIndex(13)
        except Exception:
            pass

        # Completers
        try:
            otherCompleter = QCompleter(decorative_blocks)
            otherCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
            self.otherColorBox.setCompleter(otherCompleter)
            sidechainCompleter = QCompleter(decorative_blocks)
            sidechainCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
            self.sidechainColorBox.setCompleter(sidechainCompleter)
            backboneCompleter = QCompleter(decorative_blocks)
            backboneCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
            self.backboneColorBox.setCompleter(backboneCompleter)
        except Exception:
            pass

        # Additional controls
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

        # Apply the centralized geometry and fonts to the created widgets
        try:
            for name, geom in UI_GEOMETRY.items():
                try:
                    w = getattr(self, name, None)
                    if w is not None:
                        w.setGeometry(QtCore.QRect(*geom))
                except Exception:
                    pass
        except Exception:
            pass

        # Apply fonts where configured
        try:
            for name, pts in UI_FONTS.items():
                try:
                    if pts is None:
                        continue
                    w = getattr(self, name, None)
                    if w is None:
                        continue
                    f = w.font() if hasattr(w, "font") else QtGui.QFont()
                    f.setPointSize(int(pts))
                    w.setFont(f)
                except Exception:
                    pass
        except Exception:
            pass

        # Add "Modify Residues" button (minimal placement; adjust graphics as needed)
        self.modifyResiduesButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.modifyResiduesButton.setGeometry(QtCore.QRect(100, 345, 150, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.modifyResiduesButton.setFont(font)
        self.modifyResiduesButton.setObjectName("modifyResiduesButton")

        # Add labels to show selected file/folder
        self.selectedPDBLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.selectedPDBLabel.setGeometry(QtCore.QRect(110, 340, 300, 21))
        self.selectedPDBLabel.setObjectName("selectedPDBLabel")
        self.selectedPDBLabel.setText("No PDB file selected.")

        self.selectedMinecraftLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.selectedMinecraftLabel.setGeometry(QtCore.QRect(110, 370, 300, 21))
        self.selectedMinecraftLabel.setObjectName("selectedMinecraftLabel")
        self.selectedMinecraftLabel.setText("No Minecraft save selected.")

        # Finish setup
        self.bg.raise_()
        #self.vSepLine.raise_()
        self.mc2pdbLabel = getattr(self.sidebar, "mc2pdbLabel", QtWidgets.QLabel(parent=self.centralwidget))
        # ensure central widget set
        self.setCentralWidget(self.centralwidget)

        # Make sure the right-hand controls are above the background.
        # Use guarded raises so missing attributes won't crash startup.
        try:
            widgets_to_raise = (
                getattr(self, "switchModeLabel", None),
                getattr(self, "CustomMode", None),
                getattr(self, "SkeletonMode", None),
                getattr(self, "XRayMode", None),
                getattr(self, "SpaceFillingMode", None),
                getattr(self, "RibbonMode", None),
                getattr(self, "AminoAcidMode", None),
                getattr(self, "github", None),
                getattr(self, "tools", None),
                getattr(self, "help", None),
                getattr(self, "rcsbButton", None),
                getattr(self, "mc2pdbLabel", None),
                getattr(self, "pdbDatabaseLabel", None),
                getattr(self, "modeInfoHLine", None),
                getattr(self, "infoDatabaseHLine", None),
                getattr(self, "backboneColorLabel", None),
                getattr(self, "backboneColorBox", None),
                getattr(self, "showBackboneCheck", None),
                getattr(self, "colorByBackboneCheck", None),
                getattr(self, "backboneScaleSpinBox", None),
                getattr(self, "pScaleLabel", None),
                getattr(self, "pScaleSpinBox", None),
                getattr(self, "sidechainColorLabel", None),
                getattr(self, "sidechainColorBox", None),
                getattr(self, "showSidechainCheck", None),
                getattr(self, "otherColorLabel", None),
                getattr(self, "otherColorBox", None),
                getattr(self, "otherMoleculeCheck", None),
                getattr(self, "aScaleLabel", None),
                getattr(self, "aScaleSpinBox", None),
                getattr(self, "selectPDBFileButton", None),
                getattr(self, "selectIncludedPDBButton", None),
                getattr(self, "selectMinecraftSaveButton", None),
                getattr(self, "createFunctionsButton", None),
                getattr(self, "simpleOutputCheck", None),
                getattr(self, "modifyResiduesButton", None),
                getattr(self, "selectPDBFileButton", None),
                getattr(self, "orText", None),
                getattr(self, "andText", None),
                getattr(self, "selectedPDBLabel", None),
                getattr(self, "selectedMinecraftLabel", None),
            )
            for w in widgets_to_raise:
                try:
                    if w is not None:
                        w.raise_()
                except Exception:
                    pass
        except Exception:
            pass

        # Make sure the sidebar itself is on top of the content area
        try:
            if hasattr(self, "sidebar") and self.sidebar is not None:
                self.sidebar.raise_()
        except Exception:
            pass

        # call retranslateUi and connections
        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

        # Make the main window non-resizable by the user (locks current size)
        try:
            self.setFixedSize(self.size())
        except Exception:
            pass

        # Connect sidebar buttons if present
        try:
            if hasattr(self.sidebar, "help"):
                self.sidebar.help.clicked.connect(self.handle_help_button)
            if hasattr(self.sidebar, "rcsbButton"):
                self.sidebar.rcsbButton.clicked.connect(self.handle_rscb_button)
            if hasattr(self.sidebar, "github"):
                self.sidebar.github.clicked.connect(self.handle_github_button)
            if hasattr(self.sidebar, "CustomMode"):
                self.sidebar.CustomMode.clicked.connect(self.handle_custom_mode)
            if hasattr(self.sidebar, "SkeletonMode"):
                self.sidebar.SkeletonMode.clicked.connect(self.handle_skeleton_mode)
            if hasattr(self.sidebar, "XRayMode"):
                self.sidebar.XRayMode.clicked.connect(self.handle_xray_mode)
            if hasattr(self.sidebar, "SpaceFillingMode"):
                self.sidebar.SpaceFillingMode.clicked.connect(self.handle_space_filling_mode)
            if hasattr(self.sidebar, "AminoAcidMode"):
                self.sidebar.AminoAcidMode.clicked.connect(self.handle_amino_acid_mode)
            if hasattr(self.sidebar, "RibbonMode"):
                self.sidebar.RibbonMode.clicked.connect(self.handle_ribbon_mode)
        except Exception:
            pass

        # Connect remaining UI signals
        try:
            self.selectIncludedPDBButton.clicked.connect(self.handle_included_pdb_button)
            self.selectPDBFileButton.clicked.connect(self.handle_select_pdb_file_button)
            self.selectMinecraftSaveButton.clicked.connect(self.handle_select_minecraft_button)
            self.createFunctionsButton.clicked.connect(self.handle_make_function_button)
            self.tools = getattr(self.sidebar, "tools", getattr(self, "tools", None))
            if self.tools is not None:
                self.tools.clicked.connect(self.handle_tool_mode)
            self.modifyResiduesButton.clicked.connect(self.handle_modify_residues_button)
        except Exception:
            pass

        # focusOut handlers and state changes
        try:
            if hasattr(self.otherColorBox, "focusOut"):
                self.otherColorBox.focusOut.connect(lambda: self.check_input(self.otherColorBox, decorative_blocks))
            if hasattr(self.backboneColorBox, "focusOut"):
                self.backboneColorBox.focusOut.connect(lambda: self.check_input(self.backboneColorBox, decorative_blocks))
            if hasattr(self.sidechainColorBox, "focusOut"):
                self.sidechainColorBox.focusOut.connect(lambda: self.check_input(self.sidechainColorBox, decorative_blocks))
        except Exception:
            pass

        try:
            self.showBackboneCheck.stateChanged.connect(self.on_showBackboneCheck_changed)
            self.showSidechainCheck.stateChanged.connect(self.on_showSidechainCheck_changed)
            self.colorByBackboneCheck.stateChanged.connect(self.on_colorByBackboneCheck_changed)
            self.otherMoleculeCheck.stateChanged.connect(self.on_otherMoleculeCheck_changed)
        except Exception:
            pass

    # event handlers and helpers (copied/restored from skeleton_old.py, adapted)
    def on_showBackboneCheck_changed(self, state):
        if not self.colorByBackboneCheck.isChecked():
            self.backboneColorBox.setEnabled(state != 0)
        self.backboneScaleSpinBox.setEnabled(state != 0)

    def on_showSidechainCheck_changed(self, state):
        if not self.colorByBackboneCheck.isChecked():
            self.sidechainColorBox.setEnabled(state != 0)

    def on_colorByBackboneCheck_changed(self, state):
        self.backboneColorBox.setEnabled(state == 0)
        self.sidechainColorBox.setEnabled(state == 0)

    def on_otherMoleculeCheck_changed(self, state):
        self.otherColorBox.setEnabled(state != 0)
        self.aScaleSpinBox.setEnabled(state != 0)

    def check_input(self, combobox, valid_options):
        text = combobox.currentText()
        text = text.lower()
        text = text.replace(' ', '_')
        if text not in decorative_blocks:
            self.show_information_box(title_text=f"Invalid block input",
                                      text=f"{text} is not a valid block option.",
                                      icon_path="images/icons/icon_bad.png")
            combobox.setCurrentIndex(0)
        else:
            if combobox.findText(text) <= 0:
                icon = create_icon(hex_dict[text])
                combobox.addItem(icon, text)
            combobox.setCurrentText(text)
            combobox.setCurrentIndex(combobox.findText(text))

    def handle_select_pdb_file_button(self):
        try:
            self.selectPDB = FileExplorerPopup()
            self.user_pdb_file = self.selectPDB.selected_file
            if self.user_pdb_file:
                try:
                    world_max = 320
                    if not pdbm.check_model_size(self.user_pdb_file, world_max=world_max):
                        self.info_box = InformationBox()
                        self.info_box.set_text(f"The chosen model is too large for Minecraft.")
                        self.info_box.set_title("Model too large!")
                        self.info_box.set_icon("images/icons/icon_bad.png")
                        self.info_box.show()
                    else:
                        size_factor = pdbm.check_max_size(self.user_pdb_file, world_max=world_max)
                        size_factor = str(round(size_factor, 2))
                        self.info_box = InformationBox()
                        self.info_box.set_text(
                            f"The suggested maximum protein scale is: {size_factor}x\n\nSet 'Protein Scale' below this for best results.")
                        self.info_box.set_title("Maximum scale")
                        self.info_box.set_icon("images/icons/icon_info.png")
                        self.info_box.show()
                except Exception as e:
                    self.info_box = InformationBox()
                    self.info_box.set_text(f"Could not determine recommended scale.\nError: {e}")
                    self.info_box.set_title("Scale error")
                    self.info_box.set_icon("images/icons/icon_bad.png")
                    self.info_box.show()
        except Exception as e:
            print(f"Error selecting PDB file: {e}")

    def handle_select_minecraft_button(self):
        try:
            self.selectMinecraft = MinecraftPopup()
            if self.selectMinecraft.selected_directory is None:
                self.show_information_box(title_text=f"Error",
                                          text=f"Remember to select a Minecraft save.",
                                          icon_path="images/icons/icon_bad.png")
                return
            self.user_minecraft_save = self.selectMinecraft.selected_directory
        except Exception as e:
            print(f"Error selecting Minecraft save: {e}")

    def handle_modify_residues_button(self):
        if not getattr(self, "user_pdb_file", None):
            self.show_information_box(title_text="No structure selected",
                                      text="Please select a PDB or mmCIF file first.",
                                      icon_path="images/icons/icon_bad.png")
            return
        try:
            from PDB2MC.structure_data import StructureData
            if self.user_pdb_file.lower().endswith('.cif'):
                structure = StructureData.from_mmcif(self.user_pdb_file)
            else:
                structure = StructureData.from_pdb(self.user_pdb_file)
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Failed to load structure for sequence selection:\n{e}")
            return

        try:
            popup = SequenceSelectorPopup(structure)
            self.seq_selector = popup
            popup.destroyed.connect(lambda obj=None, p=popup: setattr(self, "last_sequence_selection", getattr(p, "selection_output", None)))
            popup.show()
        except Exception as e:
            print(f"Error opening SequenceSelectorPopup: {e}")

    def handle_included_pdb_button(self):
        try:
            self.includedPDB = IncludedPDBPopup()
            self.includedPDB.show()
            self.includedPDB.selected.connect(self.save_selected_text)
        except Exception as e:
            print(f"Error opening IncludedPDBPopup: {e}")

    def save_selected_text(self, text):
        self.user_pdb_file = f"presets/{text}.pdb"

    def handle_make_function_button(self):
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

            self.wait_dialog = PleaseWaitDialog(self)
            self.wait_dialog.show()

            self.worker = WorkerThread(config_data)
            self.worker.progress.connect(self.wait_dialog.set_progress)
            self.worker.finished.connect(self.on_worker_finished)
            self.worker.start()

    def on_worker_finished(self, result):
        try:
            self.wait_dialog.close()
        except Exception:
            pass
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
        try:
            self.info_box = InformationBox()
            self.info_box.set_text(text)
            self.info_box.set_title(title_text)
            self.info_box.set_icon(icon_path)
            self.info_box.show()
        except Exception:
            QMessageBox.information(self, title_text, text)

    def handle_github_button(self):
        QDesktopServices.openUrl(QtCore.QUrl("https://github.com/markus-nevil/mcpdb"))

    def handle_help_button(self):
        try:
            from UI.help_window import HelpWindow
            help_window = HelpWindow.instance()
            if help_window.isVisible():
                help_window.raise_()
                help_window.activateWindow()
            else:
                help_window.show()
            frame_geometry = help_window.frameGeometry()
            screen_center = self.screen().availableGeometry().center()
            frame_geometry.moveCenter(screen_center)
            help_window.move(frame_geometry.topLeft())
        except Exception:
            pass

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
        # already in skeleton mode; no-op or refresh if needed
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
            print(f"Error in handle_tool_mode: {e}")

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

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        # Sidebar text handled by Sidebar; set texts for right-side widgets
        try:
            self.setWindowTitle(_translate("SkeletonWindow", "Skeleton Mode"))
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
            self.modifyResiduesButton.setText(_translate("SkeletonWindow", "Modify Residues"))
            self.createFunctionsButton.setText(_translate("SkeletonWindow", "Create Minecraft Functions"))
            self.orText.setText(_translate("SkeletonWindow", "or"))
            self.andText.setText(_translate("SkeletonWindow", "and"))
        except Exception:
            pass

# Helper utilities restored from old file
def set_combobox_by_text(combobox, text):
    index = combobox.findText(text)
    if index >= 0:  # If the text is found
        combobox.setCurrentIndex(index)

def create_icon(hex_color: str, size: int = 100) -> QIcon:
    pixmap = QPixmap(size, size)
    painter = QPainter(pixmap)
    color = QColor(hex_color)
    painter.setBrush(color)
    painter.drawRect(0, 0, size, size)
    painter.end()
    icon = QIcon(pixmap)
    return icon
