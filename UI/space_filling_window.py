from PyQt6.QtWidgets import QApplication, QMainWindow, QCompleter
from PyQt6.QtGui import QDesktopServices, QColor, QIcon, QPainter, QPixmap
from PyQt6 import QtCore, QtGui, QtWidgets
import os
from PDB2MC.variables import decorative_blocks, hex_dict
import pandas as pd
from PDB2MC import minecraft_functions as mcf, pdb_manipulation as pdbm, space_filling

from .utilities import InformationBox, MyComboBox, IncludedPDBPopup, MinecraftPopup, FileExplorerPopup
import sys
import pkg_resources
class spWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_pdb_file = None
        self.user_minecraft_save = None
        self.setWindowTitle("Space Filling mode")
        # current_directory = os.path.basename(os.getcwd())
        # if current_directory == "PDB2MC":
        #     mcpdb_directory = os.path.join(os.getcwd(), ".." "UI")
        #     os.chdir(mcpdb_directory)

        os.chdir(get_images_path())

        self.resize(435, 411)
        self.setWindowIcon(QIcon('images/icons/logo.png'))

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
        self.bg.setGeometry(QtCore.QRect(-90, -50, 781, 461))
        font = QtGui.QFont()
        font.setPointSize(7)
        self.bg.setFont(font)
        self.bg.setText("")
        self.bg.setPixmap(QtGui.QPixmap("images/MC2PDB bg.png"))
        self.bg.setScaledContents(True)
        self.bg.setObjectName("bg")
        # icon1 = QtGui.QIcon()
        # icon1.addPixmap(QtGui.QPixmap("images/icons/black_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon2 = QtGui.QIcon()
        # icon2.addPixmap(QtGui.QPixmap("images/icons/red_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon3 = QtGui.QIcon()
        # icon3.addPixmap(QtGui.QPixmap("images/icons/orange_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon4 = QtGui.QIcon()
        # icon4.addPixmap(QtGui.QPixmap("images/icons/yellow_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon5 = QtGui.QIcon()
        # icon5.addPixmap(QtGui.QPixmap("images/icons/lime_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon6 = QtGui.QIcon()
        # icon6.addPixmap(QtGui.QPixmap("images/icons/green_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon7 = QtGui.QIcon()
        # icon7.addPixmap(QtGui.QPixmap("images/icons/cyan_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon8 = QtGui.QIcon()
        # icon8.addPixmap(QtGui.QPixmap("images/icons/light_blue_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon9 = QtGui.QIcon()
        # icon9.addPixmap(QtGui.QPixmap("images/icons/blue_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon10 = QtGui.QIcon()
        # icon10.addPixmap(QtGui.QPixmap("images/icons/purple_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon11 = QtGui.QIcon()
        # icon11.addPixmap(QtGui.QPixmap("images/icons/magenta_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon12 = QtGui.QIcon()
        # icon12.addPixmap(QtGui.QPixmap("images/icons/magenta_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon13 = QtGui.QIcon()
        # icon13.addPixmap(QtGui.QPixmap("images/icons/brown_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon14 = QtGui.QIcon()
        # icon14.addPixmap(QtGui.QPixmap("images/icons/gray_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon15 = QtGui.QIcon()
        # icon15.addPixmap(QtGui.QPixmap("images/icons/light_gray_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon16 = QtGui.QIcon()
        # icon16.addPixmap(QtGui.QPixmap("images/icons/white_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon17 = QtGui.QIcon()
        # icon17.addPixmap(QtGui.QPixmap("images/icons/red_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon18 = QtGui.QIcon()
        # icon18.addPixmap(QtGui.QPixmap("images/icons/orange_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon19 = QtGui.QIcon()
        # icon19.addPixmap(QtGui.QPixmap("images/icons/yellow_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon20 = QtGui.QIcon()
        # icon20.addPixmap(QtGui.QPixmap("images/icons/lime_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon21 = QtGui.QIcon()
        # icon21.addPixmap(QtGui.QPixmap("images/icons/green_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon22 = QtGui.QIcon()
        # icon22.addPixmap(QtGui.QPixmap("images/icons/cyan_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon23 = QtGui.QIcon()
        # icon23.addPixmap(QtGui.QPixmap("images/icons/light_blue_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon24 = QtGui.QIcon()
        # icon24.addPixmap(QtGui.QPixmap("images/icons/blue_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon25 = QtGui.QIcon()
        # icon25.addPixmap(QtGui.QPixmap("images/icons/purple_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon26 = QtGui.QIcon()
        # icon26.addPixmap(QtGui.QPixmap("images/icons/magenta_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon27 = QtGui.QIcon()
        # icon27.addPixmap(QtGui.QPixmap("images/icons/pink_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon28 = QtGui.QIcon()
        # icon28.addPixmap(QtGui.QPixmap("images/icons/brown_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon29 = QtGui.QIcon()
        # icon29.addPixmap(QtGui.QPixmap("images/icons/black_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon30 = QtGui.QIcon()
        # icon30.addPixmap(QtGui.QPixmap("images/icons/gray_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon31 = QtGui.QIcon()
        # icon31.addPixmap(QtGui.QPixmap("images/icons/light_gray_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon32 = QtGui.QIcon()
        # icon32.addPixmap(QtGui.QPixmap("images/icons/white_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon33 = QtGui.QIcon()
        # icon33.addPixmap(QtGui.QPixmap("images/icons/red_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon34 = QtGui.QIcon()
        # icon34.addPixmap(QtGui.QPixmap("images/icons/orange_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon35 = QtGui.QIcon()
        # icon35.addPixmap(QtGui.QPixmap("images/icons/yellow_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon36 = QtGui.QIcon()
        # icon36.addPixmap(QtGui.QPixmap("images/icons/lime_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon37 = QtGui.QIcon()
        # icon37.addPixmap(QtGui.QPixmap("images/icons/green_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon38 = QtGui.QIcon()
        # icon38.addPixmap(QtGui.QPixmap("images/icons/cyan_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon39 = QtGui.QIcon()
        # icon39.addPixmap(QtGui.QPixmap("images/icons/light_blue_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon40 = QtGui.QIcon()
        # icon40.addPixmap(QtGui.QPixmap("images/icons/blue_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon41 = QtGui.QIcon()
        # icon41.addPixmap(QtGui.QPixmap("images/icons/purple_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon42 = QtGui.QIcon()
        # icon42.addPixmap(QtGui.QPixmap("images/icons/magenta_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon43 = QtGui.QIcon()
        # icon43.addPixmap(QtGui.QPixmap("images/icons/pink_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon44 = QtGui.QIcon()
        # icon44.addPixmap(QtGui.QPixmap("images/icons/brown_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon45 = QtGui.QIcon()
        # icon45.addPixmap(QtGui.QPixmap("images/icons/black_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon46 = QtGui.QIcon()
        # icon46.addPixmap(QtGui.QPixmap("images/icons/gray_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon47 = QtGui.QIcon()
        # icon47.addPixmap(QtGui.QPixmap("images/icons/light_gray_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon48 = QtGui.QIcon()
        # icon48.addPixmap(QtGui.QPixmap("images/icons/white_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon49 = QtGui.QIcon()
        # icon49.addPixmap(QtGui.QPixmap("images/icons/red_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon50 = QtGui.QIcon()
        # icon50.addPixmap(QtGui.QPixmap("images/icons/orange_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon51 = QtGui.QIcon()
        # icon51.addPixmap(QtGui.QPixmap("images/icons/yellow_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon52 = QtGui.QIcon()
        # icon52.addPixmap(QtGui.QPixmap("images/icons/lime_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon53 = QtGui.QIcon()
        # icon53.addPixmap(QtGui.QPixmap("images/icons/green_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon54 = QtGui.QIcon()
        # icon54.addPixmap(QtGui.QPixmap("images/icons/cyan_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon55 = QtGui.QIcon()
        # icon55.addPixmap(QtGui.QPixmap("images/icons/light_blue_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon56 = QtGui.QIcon()
        # icon56.addPixmap(QtGui.QPixmap("images/icons/blue_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon57 = QtGui.QIcon()
        # icon57.addPixmap(QtGui.QPixmap("images/icons/purple_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon58 = QtGui.QIcon()
        # icon58.addPixmap(QtGui.QPixmap("images/icons/magenta_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon59 = QtGui.QIcon()
        # icon59.addPixmap(QtGui.QPixmap("images/icons/pink_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon60 = QtGui.QIcon()
        # icon60.addPixmap(QtGui.QPixmap("images/icons/brown_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon61 = QtGui.QIcon()
        # icon61.addPixmap(QtGui.QPixmap("images/icons/black_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon62 = QtGui.QIcon()
        # icon62.addPixmap(QtGui.QPixmap("images/icons/gray_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon63 = QtGui.QIcon()
        # icon63.addPixmap(QtGui.QPixmap("images/icons/light_gray_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        #
        # icon64 = QtGui.QIcon()
        # icon64.addPixmap(QtGui.QPixmap("images/icons/white_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        self.cColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.cColorLabel.setGeometry(QtCore.QRect(110, 10, 106, 21))
        self.cColorLabel.setObjectName("cColorLabel")
        self.oColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.oColorLabel.setGeometry(QtCore.QRect(110, 40, 106, 21))
        self.oColorLabel.setObjectName("oColorLabel")
        self.nColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.nColorLabel.setGeometry(QtCore.QRect(110, 70, 106, 21))
        self.nColorLabel.setObjectName("nColorLabel")
        self.sColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.sColorLabel.setGeometry(QtCore.QRect(110, 100, 106, 21))
        self.sColorLabel.setObjectName("sColorLabel")
        self.pColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.pColorLabel.setGeometry(QtCore.QRect(110, 130, 110, 21))
        self.pColorLabel.setObjectName("pColorLabel")
        self.otherColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.otherColorLabel.setGeometry(QtCore.QRect(110, 160, 121, 21))
        self.otherColorLabel.setObjectName("otherColorLabel")
        self.oColorBox = MyComboBox(self.centralwidget)
        self.oColorBox.setGeometry(QtCore.QRect(240, 40, 175, 22))
        self.oColorBox.setObjectName("oColorBox")
        self.oColorBox.setEditable(True)

        self.nColorBox = MyComboBox(self.centralwidget)
        self.nColorBox.setGeometry(QtCore.QRect(240, 70, 175, 22))
        self.nColorBox.setObjectName("nColorBox")
        self.nColorBox.setEditable(True)

        self.pColorBox = MyComboBox(self.centralwidget)
        self.pColorBox.setGeometry(QtCore.QRect(240, 130, 175, 22))
        self.pColorBox.setObjectName("pColorBox")
        self.pColorBox.setEditable(True)

        self.otherColorBox = MyComboBox(self.centralwidget)
        self.otherColorBox.setGeometry(QtCore.QRect(240, 160, 175, 22))
        self.otherColorBox.setObjectName("otherColorBox")
        self.otherColorBox.setEditable(True)

        self.sColorBox = MyComboBox(self.centralwidget)
        self.sColorBox.setGeometry(QtCore.QRect(240, 100, 175, 22))
        self.sColorBox.setObjectName("sColorBox")
        self.sColorBox.setEditable(True)

        self.cColorBox = MyComboBox(self.centralwidget)
        self.cColorBox.setGeometry(QtCore.QRect(240, 10, 175, 22))
        self.cColorBox.setObjectName("cColorBox")
        self.cColorBox.setEditable(True)

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

        color_boxes = [self.oColorBox, self.otherColorBox,
                       self.cColorBox, self.nColorBox, self.sColorBox,
                       self.pColorBox]

        for color_box in color_boxes:
            for value, icon in icon_dict.items():
                #color_box.addItem(eval(icon), value)
                color_box.addItem(create_icon(hex_dict[value]), value)
        color_box.insertSeparator(16)
        color_box.insertSeparator(33)
        color_box.insertSeparator(50)
        color_box.insertSeparator(67)

        self.oColorBox.setCurrentIndex(0)
        self.cColorBox.setCurrentIndex(12)
        self.nColorBox.setCurrentIndex(7)
        self.sColorBox.setCurrentIndex(2)
        self.pColorBox.setCurrentIndex(3)
        self.otherColorBox.setCurrentIndex(10)

        oCompleter = QCompleter(decorative_blocks)
        oCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.otherColorBox.setCompleter(oCompleter)
        cCompleter = QCompleter(decorative_blocks)
        cCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.cColorBox.setCompleter(cCompleter)
        nCompleter = QCompleter(decorative_blocks)
        nCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.nColorBox.setCompleter(nCompleter)
        sCompleter = QCompleter(decorative_blocks)
        sCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.sColorBox.setCompleter(sCompleter)
        pCompleter = QCompleter(decorative_blocks)
        pCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.pColorBox.setCompleter(pCompleter)
        otherCompleter = QCompleter(decorative_blocks)
        otherCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.otherColorBox.setCompleter(otherCompleter)

        self.tools = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.tools.setFont(font)
        self.tools.setObjectName("tools")

        self.vSepLine.setGeometry(QtCore.QRect(90, 0, 20, 431))

        self.switchModeLabel.setGeometry(QtCore.QRect(0, 0, 101, 31))
        self.CustomMode.setGeometry(QtCore.QRect(10, 30, 75, 23))
        self.SkeletonMode.setGeometry(QtCore.QRect(10, 60, 75, 23))
        self.XRayMode.setGeometry(QtCore.QRect(10, 90, 75, 23))
        self.SpaceFillingMode.setGeometry(QtCore.QRect(10, 120, 75, 23))
        self.RibbonMode.setGeometry(QtCore.QRect(10, 150, 75, 23))
        self.AminoAcidMode.setGeometry(QtCore.QRect(10, 180, 75, 23))

        self.modeInfoHLine.setGeometry(QtCore.QRect(10, 200, 71, 16))
        self.mc2pdbLabel.setGeometry(QtCore.QRect(10, 210, 71, 21))
        self.help.setGeometry(QtCore.QRect(10, 240, 75, 31))
        self.tools.setGeometry(QtCore.QRect(10, 270, 75, 31))
        self.github.setGeometry(QtCore.QRect(10, 300, 75, 31))

        self.infoDatabaseHLine.setGeometry(QtCore.QRect(10, 325, 71, 16))
        self.pdbDatabaseLabel.setGeometry(QtCore.QRect(0, 335, 91, 21))
        self.rcsbButton.setGeometry(QtCore.QRect(10, 365, 75, 31))

        self.otherMoleculeCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.otherMoleculeCheck.setGeometry(QtCore.QRect(240, 220, 131, 17))
        self.otherMoleculeCheck.setChecked(True)
        self.otherMoleculeCheck.setObjectName("otherMoleculeCheck")
        self.otherMoleculeCheck.setToolTip("Check to show other non-protein, DNA, or RNA molecules.")
        self.meshCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.meshCheck.setGeometry(QtCore.QRect(240, 245, 151, 17))
        self.meshCheck.setObjectName("meshCheck")
        self.meshCheck.setToolTip("Check to show mesh-style atoms: many fewer blocks")

        self.colorByBackboneCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.colorByBackboneCheck.setGeometry(QtCore.QRect(240, 270, 155, 21))
        self.colorByBackboneCheck.setChecked(False)
        self.colorByBackboneCheck.setObjectName("colorByBackboneCheck")
        self.colorByBackboneCheck.setToolTip("Color the backbones of the main models by the molecule number.")
        self.pScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.pScaleLabel.setGeometry(QtCore.QRect(150, 190, 71, 21))
        self.pScaleLabel.setObjectName("pScaleLabel")
        self.pScaleSpinBox = QtWidgets.QDoubleSpinBox(parent=self.centralwidget)
        self.pScaleSpinBox.setGeometry(QtCore.QRect(240, 190, 62, 22))
        self.pScaleSpinBox.setDecimals(1)
        self.pScaleSpinBox.setMinimum(1.0)
        self.pScaleSpinBox.setMaximum(50.0)
        self.pScaleSpinBox.setSingleStep(0.5)
        self.pScaleSpinBox.setObjectName("pScaleSpinBox")
        self.pScaleSpinBox.setToolTip("Scale the entire model by this factor.")
        self.selectIncludedPDBButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.selectIncludedPDBButton.setGeometry(QtCore.QRect(250, 300, 141, 23))
        self.selectIncludedPDBButton.setObjectName("selectIncludedPDBButton")
        self.selectMinecraftSaveButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.selectMinecraftSaveButton.setGeometry(QtCore.QRect(250, 335, 131, 23))
        self.selectMinecraftSaveButton.setObjectName("selectMinecraftSaveButton")
        self.simpleOutputCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.simpleOutputCheck.setGeometry(QtCore.QRect(110, 370, 100, 31))
        self.simpleOutputCheck.setChecked(True)
        self.simpleOutputCheck.setObjectName("simpleOutputCheck")
        self.simpleOutputCheck.setToolTip("Un-select to create individual commands for each molecule")
        self.selectPDBFileButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.selectPDBFileButton.setGeometry(QtCore.QRect(110, 300, 91, 23))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.selectPDBFileButton.setFont(font)
        self.selectPDBFileButton.setObjectName("pushButton_10")
        self.createFunctionsButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.createFunctionsButton.setGeometry(QtCore.QRect(230, 370, 181, 31))
        self.createFunctionsButton.setToolTip("Add the selected PDB file to the Minecraft world")
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.createFunctionsButton.setFont(font)
        self.createFunctionsButton.setObjectName("pushButton_13")
        self.orText = QtWidgets.QLabel(parent=self.centralwidget)
        self.orText.setGeometry(QtCore.QRect(210, 300, 31, 21))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.orText.setFont(font)
        self.orText.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.orText.setObjectName("or")
        self.andText = QtWidgets.QLabel(parent=self.centralwidget)
        self.andText.setGeometry(QtCore.QRect(210, 335, 31, 21))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.andText.setFont(font)
        self.andText.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.andText.setObjectName("and")
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
        self.tools.raise_()
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
        self.otherColorLabel.raise_()
        self.oColorBox.raise_()
        self.nColorBox.raise_()
        self.pColorBox.raise_()
        self.otherColorBox.raise_()
        self.sColorBox.raise_()
        self.cColorBox.raise_()
        self.otherMoleculeCheck.raise_()
        self.meshCheck.raise_()
        self.colorByBackboneCheck.raise_()
        self.pScaleLabel.raise_()
        self.pScaleSpinBox.raise_()
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

        #self.oColorBox.focusOut.connect(self.check_input)
        self.oColorBox.focusOut.connect(lambda: self.check_input(self.oColorBox, decorative_blocks))
        self.cColorBox.focusOut.connect(lambda: self.check_input(self.cColorBox, decorative_blocks))
        self.sColorBox.focusOut.connect(lambda: self.check_input(self.sColorBox, decorative_blocks))
        self.pColorBox.focusOut.connect(lambda: self.check_input(self.pColorBox, decorative_blocks))
        self.nColorBox.focusOut.connect(lambda: self.check_input(self.nColorBox, decorative_blocks))
        self.otherColorBox.focusOut.connect(lambda: self.check_input(self.otherColorBox, decorative_blocks))

        self.colorByBackboneCheck.stateChanged.connect(self.on_colorByBackboneCheck_changed)

    def on_colorByBackboneCheck_changed(self, state):

        self.cColorBox.setEnabled(state == 0)
        self.nColorBox.setEnabled(state == 0)
        self.oColorBox.setEnabled(state == 0)
        self.pColorBox.setEnabled(state == 0)
        self.sColorBox.setEnabled(state == 0)
        self.otherColorBox.setEnabled(state == 0)

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
        config_data['atoms']['backbone_atom'] = 'backbone_atom'
        config_data['atoms']['sidechain_atom'] = 'sidechain_atom'

        config_data['backbone_size'] = 1.0
        config_data['atom_scale'] = 1.0
        config_data['scale'] = self.pScaleSpinBox.value()

        # Add the checked state of each checkbox to the dictionary
        config_data['show_atoms'] = True
        config_data['show_hetatm'] = self.otherMoleculeCheck.isChecked()
        config_data['mesh'] = self.meshCheck.isChecked()
        config_data['backbone'] = True
        config_data['sidechain'] = True
        config_data['by_chain'] = self.colorByBackboneCheck.isChecked()
        config_data['simple'] = self.simpleOutputCheck.isChecked()

        # Add the current paths of the files and directories to the dictionary
        # Replace 'file_path' and 'save_path' with the actual paths
        if self.user_pdb_file is None:
            self.show_information_box(title_text=f"Error: No PDB file",
                                      text=f"Please select a PDB file.",
                                      icon_path="images/icons/icon_bad.png")
            #QMessageBox.critical(None, "Error", "Please select a PDB file.")
        elif self.user_minecraft_save is None:
            self.show_information_box(title_text=f"Error: No Minecraft save",
                                      text=f"Please select a Minecraft save.",
                                      icon_path="images/icons/icon_bad.png")
            #QMessageBox.critical(None, "Error", "Please select a Minecraft save.")
        else:
            config_data['pdb_file'] = self.user_pdb_file
            config_data['save_path'] = self.user_minecraft_save

            #QMessageBox.information(None, "Please wait", "This process will take a long time, please wait.")

            # Read in the PDB file and process it
            pdb_file = config_data['pdb_file']
            #print(pdb_file)
            pdb_df = pdbm.read_pdb(pdb_file)
            pdb_name = pdbm.get_pdb_code(pdb_file)
            scalar = config_data['scale']
            scaled = pdbm.scale_coordinates(pdb_df, scalar)
            moved = pdbm.move_coordinates(scaled)
            moved = pdbm.rotate_to_y(moved)
            rounded = pdbm.round_df(moved)

            print("Here!")
            hetatom_df = pd.DataFrame()
            hetatm_bonds = pd.DataFrame()

            # Check if the user wants het-atoms, if so, process them
            if config_data["show_hetatm"] == True:
                print("Hetatm TRUE")
                # check if the first column of rounded contains any "HETATM" values

                if "HETATM" in rounded.iloc[:, 0].values:
                    hetatm_bonds = pdbm.process_hetatom(rounded, pdb_file)
                    hetatom_df = pdbm.filter_type_atom(rounded, remove_type="ATOM", remove_atom="H")
                    # hetatom_df = pdbm.filter_type_atom(rounded, remove_type="ATOM")
                else:
                    hetatm_bonds = None
                    hetatom_df = None
                    config_data["show_hetatm"] = False

            atom_df = pdbm.filter_type_atom(rounded, remove_type="HETATM", remove_atom="H")

            # Delete the old mcfunctions if they match the current one
            mc_dir = config_data['save_path']
            mcf.delete_mcfunctions(mc_dir, "z" + pdb_name.lower())

            try:
                space_filling.run_mode(config_data, pdb_name, rounded, mc_dir, atom_df, hetatom_df, hetatm_bonds)
            except Exception as e:
                self.show_information_box(title_text=f"Error encountered",
                                          text=f"Model has not generated! \nError: {e}",
                                          icon_path="images/icons/icon_bad.png")

            mcfiles = mcf.find_mcfunctions(mc_dir, pdb_name.lower())

            if config_data["simple"]:
                mcf.create_simple_function(pdb_name, mc_dir)
                mcf.create_clear_function(mc_dir, pdb_name)
                mcf.delete_mcfunctions(mc_dir, "z" + pdb_name.lower())
            else:
                mcf.create_master_function(mcfiles, pdb_name, mc_dir)
                mcf.create_clear_function(mc_dir, pdb_name)

            lower = pdb_name.lower()
            mcf.adjust_y_coords(mc_dir, lower)
            self.show_information_box(title_text = f"Model generated", text = f"Finished! \n Remember to use /reload\n Make your model with: /function protein:build_" + lower, icon_path ="images/icons/icon_good.png")

            #QMessageBox.information(None, "Model generated", f"Finished!\nRemember to /reload in your world and /function protein:build_{lower}")


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
            pass
        except Exception as e:
            print(f"Error in handle_space_filling_mode: {e}")


    def handle_tool_mode(self):
        try:
            from UI.tool_window import ToolWindow
            self.tool_window = ToolWindow()
            self.tool_window.show()
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


    def retranslateUi(self, sfWindow):
        _translate = QtCore.QCoreApplication.translate
        #sfWindow.setWindowTitle(_translate("sfWindow", "MainWindow"))
        self.switchModeLabel.setText(_translate("sfWindow", "Switch Mode"))
        self.CustomMode.setText(_translate("sfWindow", "Custom"))
        self.SkeletonMode.setText(_translate("sfWindow", "Skeleton"))
        self.XRayMode.setText(_translate("sfWindow", "X-Ray"))
        self.SpaceFillingMode.setText(_translate("sfWindow", "Space Filling"))
        self.AminoAcidMode.setText(_translate("sfWindow", "Amino Acids"))
        self.RibbonMode.setText(_translate("sfWindow", "Ribbon"))
        self.github.setText(_translate("sfWindow", "Github"))
        self.help.setText(_translate("sfWindow", "Help"))
        self.tools.setText(_translate("sfWindow", "Tools"))
        self.rcsbButton.setText(_translate("sfWindow", "RCSB.org"))
        self.mc2pdbLabel.setText(_translate("sfWindow", "PDB2MC"))
        self.pdbDatabaseLabel.setText(_translate("sfWindow", "PDB Database"))
        self.cColorLabel.setText(_translate("sfWindow", "Select C atom color:"))
        self.oColorLabel.setText(_translate("sfWindow", "Select O atom color:"))
        self.nColorLabel.setText(_translate("sfWindow", "Select N atom color:"))
        self.sColorLabel.setText(_translate("sfWindow", "Select S atom color:"))
        self.pColorLabel.setText(_translate("sfWindow", "Select P atom color:"))
        self.otherColorLabel.setText(_translate("sfWindow", "Select other color:"))
        #self.aScaleLabel.setText(_translate("sfWindow", "Atom scale:"))
        #self.showAtomsCheck.setText(_translate("sfWindow", "Show model atoms"))
        self.otherMoleculeCheck.setText(_translate("sfWindow", "Show other molecules"))
        self.meshCheck.setText(_translate("sfWindow", "Use \"mesh-style\" atoms"))
        self.colorByBackboneCheck.setText(_translate("sfWindow", "Color model by chain"))
        self.pScaleLabel.setText(_translate("sfWindow", "Protein scale:"))
        self.selectIncludedPDBButton.setText(_translate("sfWindow", "Select Included PDB File"))
        self.selectMinecraftSaveButton.setText(_translate("sfWindow", "Select Minecraft Save"))
        self.simpleOutputCheck.setText(_translate("sfWindow", "Simple output"))
        self.selectPDBFileButton.setText(_translate("sfWindow", "Select PDB File"))
        self.createFunctionsButton.setText(_translate("sfWindow", "Create Minecraft Functions"))
        self.orText.setText(_translate("sfWindow", "or"))
        self.andText.setText(_translate("sfWindow", "and"))

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
    main_window = spWindow()
    main_window.show()
    app.exec()