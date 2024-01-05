import os
from shutil import copyfile
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QApplication, QListWidget, QPushButton, QMainWindow, QMessageBox, QLabel, QVBoxLayout, QWidget, QStylePainter
from PyQt6.QtGui import QMovie, QPalette, QBrush, QPixmap, QDesktopServices, QIcon
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6 import QtCore, QtGui, QtWidgets

import UI
import xrayWindow
import space_fillingWindow
from variables import decorative_blocks
import pandas as pd

import pdb_manipulation as pdbm
import minecraft_functions as mcf
import skeleton
from utilUI import MyComboBox, NothingSelected, IncludedPDBPopup, MinecraftPopup, FileExplorerPopup

class SkeletonWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_pdb_file = None
        self.user_minecraft_save = None
        self.setWindowTitle("Skeleton Mode")
        self.setWindowIcon(QIcon('images/icons/logo.png'))

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

        font = QtGui.QFont()
        font.setPointSize(7)
        self.bg.setFont(font)
        self.bg.setText("")
        self.bg.setPixmap(QtGui.QPixmap("images/MC2PDB bg.png"))
        self.bg.setScaledContents(True)
        self.bg.setObjectName("bg")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("images/icons/black_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("images/icons/red_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("images/icons/orange_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("images/icons/yellow_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("images/icons/lime_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap("images/icons/green_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap("images/icons/cyan_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap("images/icons/light_blue_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap("images/icons/blue_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap("images/icons/purple_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap("images/icons/magenta_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap("images/icons/magenta_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon13 = QtGui.QIcon()
        icon13.addPixmap(QtGui.QPixmap("images/icons/brown_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon14 = QtGui.QIcon()
        icon14.addPixmap(QtGui.QPixmap("images/icons/gray_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon15 = QtGui.QIcon()
        icon15.addPixmap(QtGui.QPixmap("images/icons/light_gray_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon16 = QtGui.QIcon()
        icon16.addPixmap(QtGui.QPixmap("images/icons/white_concrete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon17 = QtGui.QIcon()
        icon17.addPixmap(QtGui.QPixmap("images/icons/red_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon18 = QtGui.QIcon()
        icon18.addPixmap(QtGui.QPixmap("images/icons/orange_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon19 = QtGui.QIcon()
        icon19.addPixmap(QtGui.QPixmap("images/icons/yellow_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon20 = QtGui.QIcon()
        icon20.addPixmap(QtGui.QPixmap("images/icons/lime_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon21 = QtGui.QIcon()
        icon21.addPixmap(QtGui.QPixmap("images/icons/green_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon22 = QtGui.QIcon()
        icon22.addPixmap(QtGui.QPixmap("images/icons/cyan_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon23 = QtGui.QIcon()
        icon23.addPixmap(QtGui.QPixmap("images/icons/light_blue_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon24 = QtGui.QIcon()
        icon24.addPixmap(QtGui.QPixmap("images/icons/blue_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon25 = QtGui.QIcon()
        icon25.addPixmap(QtGui.QPixmap("images/icons/purple_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon26 = QtGui.QIcon()
        icon26.addPixmap(QtGui.QPixmap("images/icons/magenta_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon27 = QtGui.QIcon()
        icon27.addPixmap(QtGui.QPixmap("images/icons/pink_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon28 = QtGui.QIcon()
        icon28.addPixmap(QtGui.QPixmap("images/icons/brown_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon29 = QtGui.QIcon()
        icon29.addPixmap(QtGui.QPixmap("images/icons/black_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon30 = QtGui.QIcon()
        icon30.addPixmap(QtGui.QPixmap("images/icons/gray_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon31 = QtGui.QIcon()
        icon31.addPixmap(QtGui.QPixmap("images/icons/light_gray_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon32 = QtGui.QIcon()
        icon32.addPixmap(QtGui.QPixmap("images/icons/white_glazed_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon33 = QtGui.QIcon()
        icon33.addPixmap(QtGui.QPixmap("images/icons/red_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon34 = QtGui.QIcon()
        icon34.addPixmap(QtGui.QPixmap("images/icons/orange_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon35 = QtGui.QIcon()
        icon35.addPixmap(QtGui.QPixmap("images/icons/yellow_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon36 = QtGui.QIcon()
        icon36.addPixmap(QtGui.QPixmap("images/icons/lime_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon37 = QtGui.QIcon()
        icon37.addPixmap(QtGui.QPixmap("images/icons/green_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon38 = QtGui.QIcon()
        icon38.addPixmap(QtGui.QPixmap("images/icons/cyan_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon39 = QtGui.QIcon()
        icon39.addPixmap(QtGui.QPixmap("images/icons/light_blue_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon40 = QtGui.QIcon()
        icon40.addPixmap(QtGui.QPixmap("images/icons/blue_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon41 = QtGui.QIcon()
        icon41.addPixmap(QtGui.QPixmap("images/icons/purple_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon42 = QtGui.QIcon()
        icon42.addPixmap(QtGui.QPixmap("images/icons/magenta_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon43 = QtGui.QIcon()
        icon43.addPixmap(QtGui.QPixmap("images/icons/pink_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon44 = QtGui.QIcon()
        icon44.addPixmap(QtGui.QPixmap("images/icons/brown_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon45 = QtGui.QIcon()
        icon45.addPixmap(QtGui.QPixmap("images/icons/black_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon46 = QtGui.QIcon()
        icon46.addPixmap(QtGui.QPixmap("images/icons/gray_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon47 = QtGui.QIcon()
        icon47.addPixmap(QtGui.QPixmap("images/icons/light_gray_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon48 = QtGui.QIcon()
        icon48.addPixmap(QtGui.QPixmap("images/icons/white_terracotta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon49 = QtGui.QIcon()
        icon49.addPixmap(QtGui.QPixmap("images/icons/red_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon50 = QtGui.QIcon()
        icon50.addPixmap(QtGui.QPixmap("images/icons/orange_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon51 = QtGui.QIcon()
        icon51.addPixmap(QtGui.QPixmap("images/icons/yellow_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon52 = QtGui.QIcon()
        icon52.addPixmap(QtGui.QPixmap("images/icons/lime_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon53 = QtGui.QIcon()
        icon53.addPixmap(QtGui.QPixmap("images/icons/green_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon54 = QtGui.QIcon()
        icon54.addPixmap(QtGui.QPixmap("images/icons/cyan_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon55 = QtGui.QIcon()
        icon55.addPixmap(QtGui.QPixmap("images/icons/light_blue_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon56 = QtGui.QIcon()
        icon56.addPixmap(QtGui.QPixmap("images/icons/blue_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon57 = QtGui.QIcon()
        icon57.addPixmap(QtGui.QPixmap("images/icons/purple_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon58 = QtGui.QIcon()
        icon58.addPixmap(QtGui.QPixmap("images/icons/magenta_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon59 = QtGui.QIcon()
        icon59.addPixmap(QtGui.QPixmap("images/icons/pink_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon60 = QtGui.QIcon()
        icon60.addPixmap(QtGui.QPixmap("images/icons/brown_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon61 = QtGui.QIcon()
        icon61.addPixmap(QtGui.QPixmap("images/icons/black_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon62 = QtGui.QIcon()
        icon62.addPixmap(QtGui.QPixmap("images/icons/gray_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon63 = QtGui.QIcon()
        icon63.addPixmap(QtGui.QPixmap("images/icons/light_gray_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        icon64 = QtGui.QIcon()
        icon64.addPixmap(QtGui.QPixmap("images/icons/white_wool.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)

        self.backboneColorLabel = QtWidgets.QLabel(parent=self.centralwidget)


        self.backboneColorLabel.setObjectName("backboneColorLabel")
        self.sidechainColorLabel = QtWidgets.QLabel(parent=self.centralwidget)

        self.sidechainColorLabel.setObjectName("sidechainColorLabel")
        self.otherColorLabel = QtWidgets.QLabel(parent=self.centralwidget)

        self.otherColorLabel.setObjectName("otherColorLabel")

        self.otherColorBox = MyComboBox(self.centralwidget)

        self.otherColorBox.setObjectName("otherColorBox")
        self.otherColorBox.setEditable(True)

        self.otherColorBox.addItem(icon12, "pink_concrete")
        self.otherColorBox.addItem(icon2, "red_concrete")
        self.otherColorBox.addItem(icon3, "orange_concrete")
        self.otherColorBox.addItem(icon4, "yellow_concrete")
        self.otherColorBox.addItem(icon5, "lime_concrete")
        self.otherColorBox.addItem(icon6, "green_concrete")
        self.otherColorBox.addItem(icon7, "cyan_concrete")
        self.otherColorBox.addItem(icon8, "light_blue_concrete")
        self.otherColorBox.addItem(icon9, "blue_concrete")
        self.otherColorBox.addItem(icon10, "purple_concrete")
        self.otherColorBox.addItem(icon11, "magenta_concrete")
        self.otherColorBox.addItem(icon13, "brown_concrete")
        self.otherColorBox.addItem(icon1, "black_concrete")
        self.otherColorBox.addItem(icon14, "gray_concrete")
        self.otherColorBox.addItem(icon15, "light_gray_concrete")
        self.otherColorBox.addItem(icon16, "white_concrete")
        self.otherColorBox.addItem(icon17, "red_glazed_terracotta")
        self.otherColorBox.addItem(icon18, "orange_glazed_terracotta")
        self.otherColorBox.addItem(icon19, "yellow_glazed_terracotta")
        self.otherColorBox.addItem(icon20, "lime_glazed_terracotta")
        self.otherColorBox.addItem(icon21, "green_glazed_terracotta")
        self.otherColorBox.addItem(icon22, "cyan_glazed_terracotta")
        self.otherColorBox.addItem(icon23, "light_blue_glazed_terracotta")
        self.otherColorBox.addItem(icon24, "blue_glazed_terracotta")
        self.otherColorBox.addItem(icon25, "purple_glazed_terracotta")
        self.otherColorBox.addItem(icon26, "magenta_glazed_terracotta")
        self.otherColorBox.addItem(icon27, "pink_glazed_terracotta")
        self.otherColorBox.addItem(icon28, "brown_glazed_terracotta")
        self.otherColorBox.addItem(icon29, "black_glazed_terracotta")
        self.otherColorBox.addItem(icon30, "gray_glazed_terracotta")
        self.otherColorBox.addItem(icon31, "light_gray_glazed_terracotta")
        self.otherColorBox.addItem(icon32, "white_glazed_terracotta")
        self.otherColorBox.addItem(icon33, "red_terracotta")
        self.otherColorBox.addItem(icon34, "orange_terracotta")
        self.otherColorBox.addItem(icon35, "yellow_terracotta")
        self.otherColorBox.addItem(icon36, "lime_terracotta")
        self.otherColorBox.addItem(icon37, "green_terracotta")
        self.otherColorBox.addItem(icon38, "cyan_terracotta")
        self.otherColorBox.addItem(icon39, "light_blue_terracotta")
        self.otherColorBox.addItem(icon40, "blue_terracotta")
        self.otherColorBox.addItem(icon41, "purple_terracotta")
        self.otherColorBox.addItem(icon42, "magenta_terracotta")
        self.otherColorBox.addItem(icon43, "pink_terracotta")
        self.otherColorBox.addItem(icon44, "brown_terracotta")
        self.otherColorBox.addItem(icon45, "black_terracotta")
        self.otherColorBox.addItem(icon46, "gray_terracotta")
        self.otherColorBox.addItem(icon47, "light_gray_terracotta")
        self.otherColorBox.addItem(icon48, "white_terracotta")
        self.otherColorBox.addItem(icon49, "red_wool")
        self.otherColorBox.addItem(icon50, "orange_wool")
        self.otherColorBox.addItem(icon51, "yellow_wool")
        self.otherColorBox.addItem(icon52, "lime_wool")
        self.otherColorBox.addItem(icon53, "green_wool")
        self.otherColorBox.addItem(icon54, "cyan_wool")
        self.otherColorBox.addItem(icon55, "light_blue_wool")
        self.otherColorBox.addItem(icon56, "blue_wool")
        self.otherColorBox.addItem(icon57, "purple_wool")
        self.otherColorBox.addItem(icon58, "magenta_wool")
        self.otherColorBox.addItem(icon59, "pink_wool")
        self.otherColorBox.addItem(icon60, "brown_wool")
        self.otherColorBox.addItem(icon61, "black_wool")
        self.otherColorBox.addItem(icon62, "gray_wool")
        self.otherColorBox.addItem(icon63, "light_gray_wool")
        self.otherColorBox.addItem(icon64, "wool")
        self.otherColorBox.addItem(icon2, "red_stained_glass")
        self.otherColorBox.addItem(icon3, "orange_stained_glass")
        self.otherColorBox.addItem(icon4, "yellow_stained_glass")
        self.otherColorBox.addItem(icon5, "lime_stained_glass")
        self.otherColorBox.addItem(icon6, "green_stained_glass")
        self.otherColorBox.addItem(icon7, "cyan_stained_glass")
        self.otherColorBox.addItem(icon8, "light_blue_stained_glass")
        self.otherColorBox.addItem(icon9, "blue_stained_glass")
        self.otherColorBox.addItem(icon10, "purple_stained_glass")
        self.otherColorBox.addItem(icon11, "magenta_stained_glass")
        self.otherColorBox.addItem(icon12, "pink_stained_glass")
        self.otherColorBox.addItem(icon13, "brown_stained_glass")
        self.otherColorBox.addItem(icon1, "black_stained_glass")
        self.otherColorBox.addItem(icon14, "gray_stained_glass")
        self.otherColorBox.addItem(icon15, "light_stained_glass")
        self.otherColorBox.addItem(icon16, "white_stained_glass")
        self.otherColorBox.insertSeparator(16)
        self.otherColorBox.insertSeparator(33)
        self.otherColorBox.insertSeparator(50)
        self.otherColorBox.insertSeparator(67)

        self.backboneColorBox = MyComboBox(self.centralwidget)

        self.backboneColorBox.setObjectName("backboneColorBox")
        self.backboneColorBox.setEditable(True)

        self.backboneColorBox.addItem(icon14, "gray_concrete")
        self.backboneColorBox.addItem(icon2, "red_concrete")
        self.backboneColorBox.addItem(icon3, "orange_concrete")
        self.backboneColorBox.addItem(icon4, "yellow_concrete")
        self.backboneColorBox.addItem(icon5, "lime_concrete")
        self.backboneColorBox.addItem(icon6, "green_concrete")
        self.backboneColorBox.addItem(icon7, "cyan_concrete")
        self.backboneColorBox.addItem(icon8, "light_blue_concrete")
        self.backboneColorBox.addItem(icon9, "blue_concrete")
        self.backboneColorBox.addItem(icon10, "purple_concrete")
        self.backboneColorBox.addItem(icon11, "magenta_concrete")
        self.backboneColorBox.addItem(icon12, "pink_concrete")
        self.backboneColorBox.addItem(icon13, "brown_concrete")
        self.backboneColorBox.addItem(icon1, "black_concrete")
        self.backboneColorBox.addItem(icon15, "light_gray_concrete")
        self.backboneColorBox.addItem(icon16, "white_concrete")
        self.backboneColorBox.addItem(icon17, "red_glazed_terracotta")
        self.backboneColorBox.addItem(icon18, "orange_glazed_terracotta")
        self.backboneColorBox.addItem(icon19, "yellow_glazed_terracotta")
        self.backboneColorBox.addItem(icon20, "lime_glazed_terracotta")
        self.backboneColorBox.addItem(icon21, "green_glazed_terracotta")
        self.backboneColorBox.addItem(icon22, "cyan_glazed_terracotta")
        self.backboneColorBox.addItem(icon23, "light_blue_glazed_terracotta")
        self.backboneColorBox.addItem(icon24, "blue_glazed_terracotta")
        self.backboneColorBox.addItem(icon25, "purple_glazed_terracotta")
        self.backboneColorBox.addItem(icon26, "magenta_glazed_terracotta")
        self.backboneColorBox.addItem(icon27, "pink_glazed_terracotta")
        self.backboneColorBox.addItem(icon28, "brown_glazed_terracotta")
        self.backboneColorBox.addItem(icon29, "black_glazed_terracotta")
        self.backboneColorBox.addItem(icon30, "gray_glazed_terracotta")
        self.backboneColorBox.addItem(icon31, "light_gray_glazed_terracotta")
        self.backboneColorBox.addItem(icon32, "white_glazed_terracotta")
        self.backboneColorBox.addItem(icon33, "red_terracotta")
        self.backboneColorBox.addItem(icon34, "orange_terracotta")
        self.backboneColorBox.addItem(icon35, "yellow_terracotta")
        self.backboneColorBox.addItem(icon36, "lime_terracotta")
        self.backboneColorBox.addItem(icon37, "green_terracotta")
        self.backboneColorBox.addItem(icon38, "cyan_terracotta")
        self.backboneColorBox.addItem(icon39, "light_blue_terracotta")
        self.backboneColorBox.addItem(icon40, "blue_terracotta")
        self.backboneColorBox.addItem(icon41, "purple_terracotta")
        self.backboneColorBox.addItem(icon42, "magenta_terracotta")
        self.backboneColorBox.addItem(icon43, "pink_terracotta")
        self.backboneColorBox.addItem(icon44, "brown_terracotta")
        self.backboneColorBox.addItem(icon45, "black_terracotta")
        self.backboneColorBox.addItem(icon46, "gray_terracotta")
        self.backboneColorBox.addItem(icon47, "light_gray_terracotta")
        self.backboneColorBox.addItem(icon48, "white_terracotta")
        self.backboneColorBox.addItem(icon49, "red_wool")
        self.backboneColorBox.addItem(icon50, "orange_wool")
        self.backboneColorBox.addItem(icon51, "yellow_wool")
        self.backboneColorBox.addItem(icon52, "lime_wool")
        self.backboneColorBox.addItem(icon53, "green_wool")
        self.backboneColorBox.addItem(icon54, "cyan_wool")
        self.backboneColorBox.addItem(icon55, "light_blue_wool")
        self.backboneColorBox.addItem(icon56, "blue_wool")
        self.backboneColorBox.addItem(icon57, "purple_wool")
        self.backboneColorBox.addItem(icon58, "magenta_wool")
        self.backboneColorBox.addItem(icon59, "pink_wool")
        self.backboneColorBox.addItem(icon60, "brown_wool")
        self.backboneColorBox.addItem(icon61, "black_wool")
        self.backboneColorBox.addItem(icon62, "gray_wool")
        self.backboneColorBox.addItem(icon63, "light_gray_wool")
        self.backboneColorBox.addItem(icon64, "wool")
        self.backboneColorBox.addItem(icon2, "red_stained_glass")
        self.backboneColorBox.addItem(icon3, "orange_stained_glass")
        self.backboneColorBox.addItem(icon4, "yellow_stained_glass")
        self.backboneColorBox.addItem(icon5, "lime_stained_glass")
        self.backboneColorBox.addItem(icon6, "green_stained_glass")
        self.backboneColorBox.addItem(icon7, "cyan_stained_glass")
        self.backboneColorBox.addItem(icon8, "light_blue_stained_glass")
        self.backboneColorBox.addItem(icon9, "blue_stained_glass")
        self.backboneColorBox.addItem(icon10, "purple_stained_glass")
        self.backboneColorBox.addItem(icon11, "magenta_stained_glass")
        self.backboneColorBox.addItem(icon12, "pink_stained_glass")
        self.backboneColorBox.addItem(icon13, "brown_stained_glass")
        self.backboneColorBox.addItem(icon1, "black_stained_glass")
        self.backboneColorBox.addItem(icon14, "gray_stained_glass")
        self.backboneColorBox.addItem(icon15, "light_stained_glass")
        self.backboneColorBox.addItem(icon16, "white_stained_glass")
        self.backboneColorBox.insertSeparator(16)
        self.backboneColorBox.insertSeparator(33)
        self.backboneColorBox.insertSeparator(50)
        self.backboneColorBox.insertSeparator(67)

        self.sidechainColorBox = MyComboBox(self.centralwidget)

        self.sidechainColorBox.setObjectName("sidechainColorBox")
        self.sidechainColorBox.setEditable(True)

        self.sidechainColorBox.addItem(icon14, "gray_concrete")
        self.sidechainColorBox.addItem(icon2, "red_concrete")
        self.sidechainColorBox.addItem(icon3, "orange_concrete")
        self.sidechainColorBox.addItem(icon4, "yellow_concrete")
        self.sidechainColorBox.addItem(icon5, "lime_concrete")
        self.sidechainColorBox.addItem(icon6, "green_concrete")
        self.sidechainColorBox.addItem(icon7, "cyan_concrete")
        self.sidechainColorBox.addItem(icon8, "light_blue_concrete")
        self.sidechainColorBox.addItem(icon9, "blue_concrete")
        self.sidechainColorBox.addItem(icon10, "purple_concrete")
        self.sidechainColorBox.addItem(icon11, "magenta_concrete")
        self.sidechainColorBox.addItem(icon12, "pink_concrete")
        self.sidechainColorBox.addItem(icon13, "brown_concrete")
        self.sidechainColorBox.addItem(icon1, "black_concrete")
        self.sidechainColorBox.addItem(icon15, "light_gray_concrete")
        self.sidechainColorBox.addItem(icon16, "white_concrete")
        self.sidechainColorBox.addItem(icon17, "red_glazed_terracotta")
        self.sidechainColorBox.addItem(icon18, "orange_glazed_terracotta")
        self.sidechainColorBox.addItem(icon19, "yellow_glazed_terracotta")
        self.sidechainColorBox.addItem(icon20, "lime_glazed_terracotta")
        self.sidechainColorBox.addItem(icon21, "green_glazed_terracotta")
        self.sidechainColorBox.addItem(icon22, "cyan_glazed_terracotta")
        self.sidechainColorBox.addItem(icon23, "light_blue_glazed_terracotta")
        self.sidechainColorBox.addItem(icon24, "blue_glazed_terracotta")
        self.sidechainColorBox.addItem(icon25, "purple_glazed_terracotta")
        self.sidechainColorBox.addItem(icon26, "magenta_glazed_terracotta")
        self.sidechainColorBox.addItem(icon27, "pink_glazed_terracotta")
        self.sidechainColorBox.addItem(icon28, "brown_glazed_terracotta")
        self.sidechainColorBox.addItem(icon29, "black_glazed_terracotta")
        self.sidechainColorBox.addItem(icon30, "gray_glazed_terracotta")
        self.sidechainColorBox.addItem(icon31, "light_gray_glazed_terracotta")
        self.sidechainColorBox.addItem(icon32, "white_glazed_terracotta")
        self.sidechainColorBox.addItem(icon33, "red_terracotta")
        self.sidechainColorBox.addItem(icon34, "orange_terracotta")
        self.sidechainColorBox.addItem(icon35, "yellow_terracotta")
        self.sidechainColorBox.addItem(icon36, "lime_terracotta")
        self.sidechainColorBox.addItem(icon37, "green_terracotta")
        self.sidechainColorBox.addItem(icon38, "cyan_terracotta")
        self.sidechainColorBox.addItem(icon39, "light_blue_terracotta")
        self.sidechainColorBox.addItem(icon40, "blue_terracotta")
        self.sidechainColorBox.addItem(icon41, "purple_terracotta")
        self.sidechainColorBox.addItem(icon42, "magenta_terracotta")
        self.sidechainColorBox.addItem(icon43, "pink_terracotta")
        self.sidechainColorBox.addItem(icon44, "brown_terracotta")
        self.sidechainColorBox.addItem(icon45, "black_terracotta")
        self.sidechainColorBox.addItem(icon46, "gray_terracotta")
        self.sidechainColorBox.addItem(icon47, "light_gray_terracotta")
        self.sidechainColorBox.addItem(icon48, "white_terracotta")
        self.sidechainColorBox.addItem(icon49, "red_wool")
        self.sidechainColorBox.addItem(icon50, "orange_wool")
        self.sidechainColorBox.addItem(icon51, "yellow_wool")
        self.sidechainColorBox.addItem(icon52, "lime_wool")
        self.sidechainColorBox.addItem(icon53, "green_wool")
        self.sidechainColorBox.addItem(icon54, "cyan_wool")
        self.sidechainColorBox.addItem(icon55, "light_blue_wool")
        self.sidechainColorBox.addItem(icon56, "blue_wool")
        self.sidechainColorBox.addItem(icon57, "purple_wool")
        self.sidechainColorBox.addItem(icon58, "magenta_wool")
        self.sidechainColorBox.addItem(icon59, "pink_wool")
        self.sidechainColorBox.addItem(icon60, "brown_wool")
        self.sidechainColorBox.addItem(icon61, "black_wool")
        self.sidechainColorBox.addItem(icon62, "gray_wool")
        self.sidechainColorBox.addItem(icon63, "light_gray_wool")
        self.sidechainColorBox.addItem(icon64, "wool")
        self.sidechainColorBox.addItem(icon2, "red_stained_glass")
        self.sidechainColorBox.addItem(icon3, "orange_stained_glass")
        self.sidechainColorBox.addItem(icon4, "yellow_stained_glass")
        self.sidechainColorBox.addItem(icon5, "lime_stained_glass")
        self.sidechainColorBox.addItem(icon6, "green_stained_glass")
        self.sidechainColorBox.addItem(icon7, "cyan_stained_glass")
        self.sidechainColorBox.addItem(icon8, "light_blue_stained_glass")
        self.sidechainColorBox.addItem(icon9, "blue_stained_glass")
        self.sidechainColorBox.addItem(icon10, "purple_stained_glass")
        self.sidechainColorBox.addItem(icon11, "magenta_stained_glass")
        self.sidechainColorBox.addItem(icon12, "pink_stained_glass")
        self.sidechainColorBox.addItem(icon13, "brown_stained_glass")
        self.sidechainColorBox.addItem(icon1, "black_stained_glass")
        self.sidechainColorBox.addItem(icon14, "gray_stained_glass")
        self.sidechainColorBox.addItem(icon15, "light_stained_glass")
        self.sidechainColorBox.addItem(icon16, "white_stained_glass")
        self.sidechainColorBox.insertSeparator(16)
        self.sidechainColorBox.insertSeparator(33)
        self.sidechainColorBox.insertSeparator(50)
        self.sidechainColorBox.insertSeparator(67)

        self.aScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)

        self.aScaleLabel.setObjectName("aScaleLabel")
        # self.showAtomsCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        # self.showAtomsCheck.setGeometry(QtCore.QRect(440, 10, 121, 17))
        # self.showAtomsCheck.setChecked(True)
        # self.showAtomsCheck.setObjectName("showAtomsCheck")
        # self.showAtomsCheck.setToolTip("Show the atoms of the main models.")
        self.otherMoleculeCheck = QtWidgets.QCheckBox(parent=self.centralwidget)

        self.otherMoleculeCheck.setChecked(True)
        self.otherMoleculeCheck.setObjectName("otherMoleculeCheck")
        self.otherMoleculeCheck.setToolTip("Check to show other non-protein, DNA, or RNA molecules.")
        #self.meshCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        #self.meshCheck.setGeometry(QtCore.QRect(440, 70, 151, 17))
        #self.meshCheck.setObjectName("meshCheck")
        #self.meshCheck.setToolTip("Check to show mesh-style atoms: many fewer blocks")
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

        self.backboneColorLabel.setGeometry(QtCore.QRect(110, 10, 120, 21))
        self.backboneColorBox.setGeometry(QtCore.QRect(240, 10, 175, 22))
        self.showBackboneCheck.setGeometry(QtCore.QRect(240, 37, 121, 17))
        self.colorByBackboneCheck.setGeometry(QtCore.QRect(240, 53, 155, 21))
        self.bScaleLabel.setGeometry(QtCore.QRect(110, 75, 111, 21))
        self.backboneScaleSpinBox.setGeometry(QtCore.QRect(240, 75, 62, 22))
        self.pScaleLabel.setGeometry(QtCore.QRect(110, 100, 71, 21))
        self.pScaleSpinBox.setGeometry(QtCore.QRect(240, 100, 62, 22))

        self.sidechainColorLabel.setGeometry(QtCore.QRect(110, 140, 120, 21))
        self.sidechainColorBox.setGeometry(QtCore.QRect(240, 140, 175, 22))
        self.showSidechainCheck.setGeometry(QtCore.QRect(240, 165, 121, 17))

        self.otherColorLabel.setGeometry(QtCore.QRect(110, 200, 121, 21))
        self.otherColorBox.setGeometry(QtCore.QRect(240, 200, 175, 22))
        self.otherMoleculeCheck.setGeometry(QtCore.QRect(240, 228, 131, 17))
        self.aScaleLabel.setGeometry(QtCore.QRect(110, 250, 61, 21))
        self.aScaleSpinBox.setGeometry(QtCore.QRect(240, 250, 62, 22))

        self.selectPDBFileButton.setGeometry(QtCore.QRect(110, 290, 91, 23))
        self.orText.setGeometry(QtCore.QRect(210, 290, 31, 21))
        self.selectIncludedPDBButton.setGeometry(QtCore.QRect(250, 290, 141, 23))

        self.andText.setGeometry(QtCore.QRect(210, 325, 31, 21))
        self.selectMinecraftSaveButton.setGeometry(QtCore.QRect(250, 325, 141, 23))

        self.simpleOutputCheck.setGeometry(QtCore.QRect(110, 360, 100, 31))
        self.createFunctionsButton.setGeometry(QtCore.QRect(230, 360, 181, 31))

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
        # self.cColorLabel.raise_()
        # self.oColorLabel.raise_()
        # self.nColorLabel.raise_()
        # self.sColorLabel.raise_()
        # self.pColorLabel.raise_()
        self.backboneColorLabel.raise_()
        self.sidechainColorLabel.raise_()
        self.otherColorLabel.raise_()
        # self.oColorBox.raise_()
        # self.nColorBox.raise_()
        # self.pColorBox.raise_()
        self.otherColorBox.raise_()
        # self.sColorBox.raise_()
        # self.cColorBox.raise_()
        self.backboneColorBox.raise_()
        self.sidechainColorBox.raise_()
        self.aScaleLabel.raise_()
        # self.showAtomsCheck.raise_()
        self.otherMoleculeCheck.raise_()
        #self.meshCheck.raise_()
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

        self.otherColorBox.focusOut.connect(lambda: self.check_input(self.otherColorBox, decorative_blocks))
        self.backboneColorBox.focusOut.connect(lambda: self.check_input(self.backboneColorBox, decorative_blocks))
        self.sidechainColorBox.focusOut.connect(lambda: self.check_input(self.sidechainColorBox, decorative_blocks))


    def check_input(self, combobox, valid_options):
        text = combobox.currentText()
        #ensure that text is lowercase
        text = text.lower()
        #replace any space characters with '_'
        text = text.replace(' ', '_')
        if text not in decorative_blocks:
            QMessageBox.warning(self, "Invalid Input", f"{text} is not a valid option.")
            combobox.setCurrentIndex(0)
        else:
            combobox.setCurrentText(text)

    # Slot methods to handle QPushButton clicks
    def handle_select_pdb_file_button(self):
        print("Selecting PDB file")
        self.selectPDB = FileExplorerPopup()
        self.user_pdb_file = self.selectPDB.selected_file
        print(f"The user has this file: {self.user_pdb_file}")

    def handle_select_minecraft_button(self):
        print("minecraft world")
        self.selectMinecraft = MinecraftPopup()
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
        config_data = {'atoms': {}}

        # Add the current text of each combobox to the dictionary
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

        # Add the checked state of each checkbox to the dictionary
        config_data['show_hetatm'] = self.otherMoleculeCheck.isChecked()
        config_data['backbone'] = self.showBackboneCheck.isChecked()
        config_data['sidechain'] = self.showSidechainCheck.isChecked()
        config_data['by_chain'] = self.colorByBackboneCheck.isChecked()
        config_data['simple'] = self.simpleOutputCheck.isChecked()

        # Add the current paths of the files and directories to the dictionary
        # Replace 'file_path' and 'save_path' with the actual paths
        if self.user_pdb_file is None:
            QMessageBox.critical(None, "Error", "Please select a PDB file.")
        elif self.user_minecraft_save is None:
            QMessageBox.critical(None, "Error", "Please select a Minecraft save.")
        else:
            config_data['pdb_file'] = self.user_pdb_file
            config_data['save_path'] = self.user_minecraft_save

            #print(config_data)

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
            print(config_data)
            print(mc_dir)
            print(pdb_name)
            print(pdb_file)
            print(rounded.head())
            print(mc_dir)
            print(atom_df.head())
            print(hetatom_df.head())
            print(hetatm_bonds.head())
            try:
                print("fix")
                skeleton.run_mode(config_data, pdb_name, pdb_file, rounded, mc_dir, atom_df, hetatom_df, hetatm_bonds)
            except Exception as e:
                print(f"Error: {e}")

            mcfiles = mcf.find_mcfunctions(mc_dir, pdb_name.lower())
            #print(mcfiles)

            if config_data["simple"]:
                mcf.create_simple_function(pdb_name, mc_dir)
                mcf.create_clear_function(mc_dir, pdb_name)
                mcf.delete_mcfunctions(mc_dir, "z" + pdb_name.lower())
            else:
                mcf.create_master_function(mcfiles, pdb_name, mc_dir)
                mcf.create_clear_function(mc_dir, pdb_name)

            lower = pdb_name.lower()

            QMessageBox.information(None, "Model generated", f"Finished!\nRemember to /reload in your world and /function protein:build_{lower}")


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
        self.Custom = UI.CustomWindow()
        self.Custom.show()
        self.hide()

    def handle_skeleton_mode(self):
        print("Skeleton mode button clicked")
        self.Skeleton = SkeletonWindow()
        self.Skeleton.show()
        #Turn off main window
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

    def handle_ribbon_mode(self):
        print("Ribbon mode button clicked")


    def retranslateUi(self, SkeletonWindow):
        _translate = QtCore.QCoreApplication.translate
        #SkeletonWindow.setWindowTitle(_translate("SkeletonWindow", "MainWindow"))
        self.switchModeLabel.setText(_translate("SkeletonWindow", "Switch Mode"))
        self.CustomMode.setText(_translate("SkeletonWindow", "Custom"))
        self.SkeletonMode.setText(_translate("SkeletonWindow", "Skeleton"))
        self.XRayMode.setText(_translate("SkeletonWindow", "X-Ray"))
        self.SpaceFillingMode.setText(_translate("SkeletonWindow", "Space Filling"))
        self.AminoAcidMode.setText(_translate("SkeletonWindow", "Amino Acids"))
        self.RibbonMode.setText(_translate("SkeletonWindow", "Ribbon"))
        self.github.setText(_translate("SkeletonWindow", "Github"))
        self.help.setText(_translate("SkeletonWindow", "Help"))
        self.rcsbButton.setText(_translate("SkeletonWindow", "RCSB.org"))
        self.mc2pdbLabel.setText(_translate("SkeletonWindow", "MC2PDB"))
        self.pdbDatabaseLabel.setText(_translate("SkeletonWindow", "PDB Database"))
        # self.cColorLabel.setText(_translate("SkeletonWindow", "Select C atom color:"))
        # self.oColorLabel.setText(_translate("SkeletonWindow", "Select O atom color:"))
        # self.nColorLabel.setText(_translate("SkeletonWindow", "Select N atom color:"))
        # self.sColorLabel.setText(_translate("SkeletonWindow", "Select S atom color:"))
        # self.pColorLabel.setText(_translate("SkeletonWindow", "Select P atom color:"))
        self.backboneColorLabel.setText(_translate("SkeletonWindow", "Select backbone color:"))
        self.sidechainColorLabel.setText(_translate("SkeletonWindow", "Select sidechain color:"))
        self.otherColorLabel.setText(_translate("SkeletonWindow", "Select other color:"))
        self.aScaleLabel.setText(_translate("SkeletonWindow", "Atom scale:"))
        # self.showAtomsCheck.setText(_translate("SkeletonWindow", "Show model atoms"))
        self.otherMoleculeCheck.setText(_translate("SkeletonWindow", "Show other molecules"))
        #self.meshCheck.setText(_translate("SkeletonWindow", "Use \"mesh-style\" atoms"))
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

if __name__ == "__main__":
    app = QApplication([])
    main_window = SkeletonWindow()
    main_window.show()
    app.exec()