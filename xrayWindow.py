import os
from shutil import copyfile
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QApplication, QListWidget, QPushButton, QMainWindow, QMessageBox, QLabel, QVBoxLayout, QWidget, QStylePainter
from PyQt6.QtGui import QMovie, QPalette, QBrush, QPixmap, QDesktopServices, QIcon
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6 import QtCore, QtGui, QtWidgets

import skeletonWindow
import space_fillingWindow
import ribbonWindow
import amino_acidsWindow
import customWindow

from variables import decorative_blocks
import pandas as pd

import pdb_manipulation as pdbm
import minecraft_functions as mcf
import xray
from utilUI import MyComboBox, NothingSelected, IncludedPDBPopup, MinecraftPopup, FileExplorerPopup

class XrayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_pdb_file = None
        self.user_minecraft_save = None
        self.setWindowTitle("X-ray mode")
        self.resize(607, 411)
        self.setWindowIcon(QIcon('images/icons/logo.png'))

        # Set style to Fusion
        #self.setStyle("Fusion")
        self.centralwidget = QtWidgets.QWidget(parent=self)
        self.centralwidget.setObjectName("centralwidget")
        self.switchModeLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.switchModeLabel.setGeometry(QtCore.QRect(0, 0, 101, 31))
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
        self.vSepLine.setGeometry(QtCore.QRect(90, 0, 20, 431))
        self.vSepLine.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.vSepLine.setLineWidth(2)
        self.vSepLine.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.vSepLine.setObjectName("vSepLine")
        self.CustomMode = QtWidgets.QPushButton(parent=self.centralwidget)
        self.CustomMode.setGeometry(QtCore.QRect(10, 30, 75, 23))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.CustomMode.setFont(font)
        self.CustomMode.setObjectName("CustomMode")
        self.SkeletonMode = QtWidgets.QPushButton(parent=self.centralwidget)
        self.SkeletonMode.setGeometry(QtCore.QRect(10, 60, 75, 23))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.SkeletonMode.setFont(font)
        self.SkeletonMode.setObjectName("SkeletonMode")
        self.XRayMode = QtWidgets.QPushButton(parent=self.centralwidget)
        self.XRayMode.setGeometry(QtCore.QRect(10, 90, 75, 23))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.XRayMode.setFont(font)
        self.XRayMode.setObjectName("XRayMode")
        self.SpaceFillingMode = QtWidgets.QPushButton(parent=self.centralwidget)
        self.SpaceFillingMode.setGeometry(QtCore.QRect(10, 120, 75, 23))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.SpaceFillingMode.setFont(font)
        self.SpaceFillingMode.setObjectName("SpaceFillingMode")
        self.AminoAcidMode = QtWidgets.QPushButton(parent=self.centralwidget)
        self.AminoAcidMode.setGeometry(QtCore.QRect(10, 180, 75, 23))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.AminoAcidMode.setFont(font)
        self.AminoAcidMode.setObjectName("AminoAcidMode")
        self.RibbonMode = QtWidgets.QPushButton(parent=self.centralwidget)
        self.RibbonMode.setGeometry(QtCore.QRect(10, 150, 75, 23))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.RibbonMode.setFont(font)
        self.RibbonMode.setObjectName("RibbonMode")
        self.github = QtWidgets.QPushButton(parent=self.centralwidget)
        self.github.setGeometry(QtCore.QRect(10, 290, 75, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.github.setFont(font)
        self.github.setObjectName("github")
        self.help = QtWidgets.QPushButton(parent=self.centralwidget)
        self.help.setGeometry(QtCore.QRect(10, 250, 75, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.help.setFont(font)
        self.help.setObjectName("help")
        self.rcsbButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.rcsbButton.setGeometry(QtCore.QRect(10, 360, 75, 31))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.rcsbButton.setFont(font)
        self.rcsbButton.setObjectName("rcsbButton")
        self.mc2pdbLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.mc2pdbLabel.setGeometry(QtCore.QRect(10, 220, 71, 21))
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
        self.pdbDatabaseLabel.setGeometry(QtCore.QRect(0, 330, 91, 21))
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
        self.modeInfoHLine.setGeometry(QtCore.QRect(10, 210, 71, 16))
        self.modeInfoHLine.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.modeInfoHLine.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.modeInfoHLine.setObjectName("modeInfoHLine")
        self.infoDatabaseHLine = QtWidgets.QFrame(parent=self.centralwidget)
        self.infoDatabaseHLine.setGeometry(QtCore.QRect(10, 320, 71, 16))
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
        self.backboneColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.backboneColorLabel.setGeometry(QtCore.QRect(110, 240, 120, 21))
        self.backboneColorLabel.setObjectName("backboneColorLabel")
        self.sidechainColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.sidechainColorLabel.setGeometry(QtCore.QRect(110, 210, 120, 21))
        self.sidechainColorLabel.setObjectName("sidechainColorLabel")
        self.otherColorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.otherColorLabel.setGeometry(QtCore.QRect(110, 160, 121, 21))
        self.otherColorLabel.setObjectName("otherColorLabel")
        #self.oColorBox = QtWidgets.QComboBox(parent=self.centralwidget)
        self.oColorBox = MyComboBox(self.centralwidget)
        self.oColorBox.setGeometry(QtCore.QRect(240, 40, 175, 22))
        self.oColorBox.setObjectName("oColorBox")
        self.oColorBox.setEditable(True)

        self.oColorBox.addItem(icon2, "red_stained_glass")
        self.oColorBox.addItem(icon3, "orange_stained_glass")
        self.oColorBox.addItem(icon4, "yellow_stained_glass")
        self.oColorBox.addItem(icon5, "lime_stained_glass")
        self.oColorBox.addItem(icon6, "green_stained_glass")
        self.oColorBox.addItem(icon7, "cyan_stained_glass")
        self.oColorBox.addItem(icon8, "light_blue_stained_glass")
        self.oColorBox.addItem(icon9, "blue_stained_glass")
        self.oColorBox.addItem(icon10, "purple_stained_glass")
        self.oColorBox.addItem(icon11, "magenta_stained_glass")
        self.oColorBox.addItem(icon12, "pink_stained_glass")
        self.oColorBox.addItem(icon13, "brown_stained_glass")
        self.oColorBox.addItem(icon1, "black_stained_glass")
        self.oColorBox.addItem(icon14, "gray_stained_glass")
        self.oColorBox.addItem(icon15, "light_stained_glass")
        self.oColorBox.addItem(icon16, "white_stained_glass")

        self.nColorBox = MyComboBox(self.centralwidget)
        self.nColorBox.setGeometry(QtCore.QRect(240, 70, 175, 22))
        self.nColorBox.setObjectName("nColorBox")
        self.nColorBox.setEditable(True)

        self.nColorBox.addItem(icon9, "blue_stained_glass")
        self.nColorBox.addItem(icon2, "red_stained_glass")
        self.nColorBox.addItem(icon3, "orange_stained_glass")
        self.nColorBox.addItem(icon4, "yellow_stained_glass")
        self.nColorBox.addItem(icon5, "lime_stained_glass")
        self.nColorBox.addItem(icon6, "green_stained_glass")
        self.nColorBox.addItem(icon7, "cyan_stained_glass")
        self.nColorBox.addItem(icon8, "light_blue_stained_glass")
        self.nColorBox.addItem(icon10, "purple_stained_glass")
        self.nColorBox.addItem(icon11, "magenta_stained_glass")
        self.nColorBox.addItem(icon12, "pink_stained_glass")
        self.nColorBox.addItem(icon13, "brown_stained_glass")
        self.nColorBox.addItem(icon1, "black_stained_glass")
        self.nColorBox.addItem(icon14, "gray_stained_glass")
        self.nColorBox.addItem(icon15, "light_stained_glass")
        self.nColorBox.addItem(icon16, "white_stained_glass")

        self.pColorBox = MyComboBox(self.centralwidget)
        self.pColorBox.setGeometry(QtCore.QRect(240, 130, 175, 22))
        self.pColorBox.setObjectName("pColorBox")
        self.pColorBox.setEditable(True)

        self.pColorBox.addItem(icon5, "lime_stained_glass")
        self.pColorBox.addItem(icon2, "red_stained_glass")
        self.pColorBox.addItem(icon3, "orange_stained_glass")
        self.pColorBox.addItem(icon4, "yellow_stained_glass")
        self.pColorBox.addItem(icon6, "green_stained_glass")
        self.pColorBox.addItem(icon7, "cyan_stained_glass")
        self.pColorBox.addItem(icon8, "light_blue_stained_glass")
        self.pColorBox.addItem(icon9, "blue_stained_glass")
        self.pColorBox.addItem(icon10, "purple_stained_glass")
        self.pColorBox.addItem(icon11, "magenta_stained_glass")
        self.pColorBox.addItem(icon12, "pink_stained_glass")
        self.pColorBox.addItem(icon13, "brown_stained_glass")
        self.pColorBox.addItem(icon1, "black_stained_glass")
        self.pColorBox.addItem(icon14, "gray_stained_glass")
        self.pColorBox.addItem(icon15, "light_stained_glass")
        self.pColorBox.addItem(icon16, "white_stained_glass")

        self.otherColorBox = MyComboBox(self.centralwidget)
        self.otherColorBox.setGeometry(QtCore.QRect(240, 160, 175, 22))
        self.otherColorBox.setObjectName("otherColorBox")
        self.otherColorBox.setEditable(True)

        self.otherColorBox.addItem(icon12, "pink_stained_glass")
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
        self.otherColorBox.addItem(icon13, "brown_stained_glass")
        self.otherColorBox.addItem(icon1, "black_stained_glass")
        self.otherColorBox.addItem(icon14, "gray_stained_glass")
        self.otherColorBox.addItem(icon15, "light_stained_glass")
        self.otherColorBox.addItem(icon16, "white_stained_glass")

        self.sColorBox = MyComboBox(self.centralwidget)
        self.sColorBox.setGeometry(QtCore.QRect(240, 100, 175, 22))
        self.sColorBox.setObjectName("sColorBox")
        self.sColorBox.setEditable(True)

        self.sColorBox.addItem(icon4, "yellow_stained_glass")
        self.sColorBox.addItem(icon2, "red_stained_glass")
        self.sColorBox.addItem(icon3, "orange_stained_glass")
        self.sColorBox.addItem(icon5, "lime_stained_glass")
        self.sColorBox.addItem(icon6, "green_stained_glass")
        self.sColorBox.addItem(icon7, "cyan_stained_glass")
        self.sColorBox.addItem(icon8, "light_blue_stained_glass")
        self.sColorBox.addItem(icon9, "blue_stained_glass")
        self.sColorBox.addItem(icon10, "purple_stained_glass")
        self.sColorBox.addItem(icon11, "magenta_stained_glass")
        self.sColorBox.addItem(icon12, "pink_stained_glass")
        self.sColorBox.addItem(icon13, "brown_stained_glass")
        self.sColorBox.addItem(icon1, "black_stained_glass")
        self.sColorBox.addItem(icon14, "gray_stained_glass")
        self.sColorBox.addItem(icon15, "light_stained_glass")
        self.sColorBox.addItem(icon16, "white_stained_glass")

        self.cColorBox = MyComboBox(self.centralwidget)
        self.cColorBox.setGeometry(QtCore.QRect(240, 10, 175, 22))
        self.cColorBox.setObjectName("cColorBox")
        self.cColorBox.setEditable(True)

        self.cColorBox.addItem(icon1, "black_stained_glass")
        self.cColorBox.addItem(icon2, "red_stained_glass")
        self.cColorBox.addItem(icon3, "orange_stained_glass")
        self.cColorBox.addItem(icon4, "yellow_stained_glass")
        self.cColorBox.addItem(icon5, "lime_stained_glass")
        self.cColorBox.addItem(icon6, "green_stained_glass")
        self.cColorBox.addItem(icon7, "cyan_stained_glass")
        self.cColorBox.addItem(icon8, "light_blue_stained_glass")
        self.cColorBox.addItem(icon9, "blue_stained_glass")
        self.cColorBox.addItem(icon10, "purple_stained_glass")
        self.cColorBox.addItem(icon11, "magenta_stained_glass")
        self.cColorBox.addItem(icon12, "pink_stained_glass")
        self.cColorBox.addItem(icon13, "brown_stained_glass")
        self.cColorBox.addItem(icon14, "gray_stained_glass")
        self.cColorBox.addItem(icon15, "light_stained_glass")
        self.cColorBox.addItem(icon16, "white_stained_glass")

        self.backboneColorBox = MyComboBox(self.centralwidget)
        self.backboneColorBox.setGeometry(QtCore.QRect(240, 240, 175, 22))
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

        self.sidechainColorBox = MyComboBox(self.centralwidget)
        self.sidechainColorBox.setGeometry(QtCore.QRect(240, 210, 175, 22))
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

        self.aScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.aScaleLabel.setGeometry(QtCore.QRect(440, 100, 61, 21))
        self.aScaleLabel.setObjectName("aScaleLabel")
        self.showAtomsCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.showAtomsCheck.setGeometry(QtCore.QRect(440, 10, 121, 17))
        self.showAtomsCheck.setChecked(True)
        self.showAtomsCheck.setObjectName("showAtomsCheck")
        self.showAtomsCheck.setToolTip("Show the atoms of the main models.")
        self.otherMoleculeCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.otherMoleculeCheck.setGeometry(QtCore.QRect(440, 40, 131, 17))
        self.otherMoleculeCheck.setChecked(True)
        self.otherMoleculeCheck.setObjectName("otherMoleculeCheck")
        self.otherMoleculeCheck.setToolTip("Check to show other non-protein, DNA, or RNA molecules.")
        self.meshCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.meshCheck.setGeometry(QtCore.QRect(440, 70, 151, 17))
        self.meshCheck.setObjectName("meshCheck")
        self.meshCheck.setToolTip("Check to show mesh-style atoms: many fewer blocks")
        self.aScaleSpinBox = QtWidgets.QDoubleSpinBox(parent=self.centralwidget)
        self.aScaleSpinBox.setGeometry(QtCore.QRect(530, 100, 62, 22))
        self.aScaleSpinBox.setDecimals(1)
        self.aScaleSpinBox.setMinimum(1.0)
        self.aScaleSpinBox.setMaximum(50.0)
        self.aScaleSpinBox.setSingleStep(0.5)
        self.aScaleSpinBox.setProperty("value", 1.5)
        self.aScaleSpinBox.setObjectName("aScaleSpinBox")
        self.aScaleSpinBox.setToolTip("Change the diameter (rounded up) of each atom.")
        self.showBackboneCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.showBackboneCheck.setGeometry(QtCore.QRect(440, 240, 121, 17))
        self.showBackboneCheck.setChecked(True)
        self.showBackboneCheck.setObjectName("showBackboneCheck")
        self.showBackboneCheck.setToolTip("Show the N-C-C backbone of the main models.")
        self.showSidechainCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.showSidechainCheck.setGeometry(QtCore.QRect(440, 210, 121, 17))
        self.showSidechainCheck.setChecked(True)
        self.showSidechainCheck.setObjectName("showSidechainCheck")
        self.showSidechainCheck.setToolTip("Show amino acid R-groups")
        self.pScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.pScaleLabel.setGeometry(QtCore.QRect(440, 130, 71, 21))
        self.pScaleLabel.setObjectName("pScaleLabel")
        self.pScaleSpinBox = QtWidgets.QDoubleSpinBox(parent=self.centralwidget)
        self.pScaleSpinBox.setGeometry(QtCore.QRect(530, 130, 62, 22))
        self.pScaleSpinBox.setDecimals(1)
        self.pScaleSpinBox.setMinimum(1.0)
        self.pScaleSpinBox.setMaximum(50.0)
        self.pScaleSpinBox.setSingleStep(0.5)
        self.pScaleSpinBox.setObjectName("pScaleSpinBox")
        self.pScaleSpinBox.setToolTip("Scale the entire model by this factor.")
        self.bScaleLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.bScaleLabel.setGeometry(QtCore.QRect(440, 270, 111, 21))
        self.bScaleLabel.setObjectName("bScaleLabel")
        self.backboneScaleSpinBox = QtWidgets.QDoubleSpinBox(parent=self.centralwidget)
        self.backboneScaleSpinBox.setGeometry(QtCore.QRect(530, 270, 62, 22))
        self.backboneScaleSpinBox.setDecimals(1)
        self.backboneScaleSpinBox.setMinimum(1.0)
        self.backboneScaleSpinBox.setMaximum(50.0)
        self.backboneScaleSpinBox.setSingleStep(0.5)
        self.backboneScaleSpinBox.setObjectName("backboneScaleSpinBox")
        self.backboneScaleSpinBox.setToolTip("Scale the width of the backbone by this factor.")
        self.selectIncludedPDBButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.selectIncludedPDBButton.setGeometry(QtCore.QRect(250, 320, 141, 23))
        self.selectIncludedPDBButton.setObjectName("selectIncludedPDBButton")
        self.selectMinecraftSaveButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.selectMinecraftSaveButton.setGeometry(QtCore.QRect(440, 320, 131, 23))
        self.selectMinecraftSaveButton.setObjectName("selectMinecraftSaveButton")
        self.simpleOutputCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.simpleOutputCheck.setGeometry(QtCore.QRect(110, 370, 100, 31))
        self.simpleOutputCheck.setChecked(True)
        self.simpleOutputCheck.setObjectName("simpleOutputCheck")
        self.simpleOutputCheck.setToolTip("Un-select to create individual commands for each molecule")
        self.selectPDBFileButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.selectPDBFileButton.setGeometry(QtCore.QRect(110, 320, 91, 23))
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
        self.orText.setGeometry(QtCore.QRect(210, 320, 21, 21))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.orText.setFont(font)
        self.orText.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.orText.setObjectName("or")
        self.andText = QtWidgets.QLabel(parent=self.centralwidget)
        self.andText.setGeometry(QtCore.QRect(400, 320, 31, 21))
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
        config_data['by_chain'] = False
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
                #print("Fix")
                xray.run_mode(config_data, pdb_name, pdb_file, rounded, mc_dir, atom_df, hetatom_df, hetatm_bonds)
            except Exception as e:
                print(f"Error: {e}")

            mcfiles = mcf.find_mcfunctions(mc_dir, pdb_name.lower())
            print(mcfiles)

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
        self.Custom = customWindow.CustomWindow()
        self.Custom.show()
        self.hide()

    def handle_skeleton_mode(self):
        print("Skeleton mode button clicked")
        self.Skeleton = skeletonWindow.SkeletonWindow()
        self.Skeleton.show()
        #Turn off main window
        self.hide()

    def handle_xray_mode(self):
        print("X-Ray mode button clicked")


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
        self.otherColorLabel.setText(_translate("XrayWindow", "Select other color:"))
        self.aScaleLabel.setText(_translate("XrayWindow", "Atom scale:"))
        self.showAtomsCheck.setText(_translate("XrayWindow", "Show model atoms"))
        self.otherMoleculeCheck.setText(_translate("XrayWindow", "Show other molecules"))
        self.meshCheck.setText(_translate("XrayWindow", "Use \"mesh-style\" atoms"))
        self.showBackboneCheck.setText(_translate("XrayWindow", "Show backbone"))
        self.showSidechainCheck.setText(_translate("XrayWindow", "Show sidechain"))
        #self.colorByBackboneCheck.setText(_translate("XrayWindow", "Color backbone by chain"))
        self.pScaleLabel.setText(_translate("XrayWindow", "Protein scale:"))
        self.bScaleLabel.setText(_translate("XrayWindow", "Backbone scale:"))
        self.selectIncludedPDBButton.setText(_translate("XrayWindow", "Select Included PDB File"))
        self.selectMinecraftSaveButton.setText(_translate("XrayWindow", "Select Minecraft Save"))
        self.simpleOutputCheck.setText(_translate("XrayWindow", "Simple output"))
        self.selectPDBFileButton.setText(_translate("XrayWindow", "Select PDB File"))
        self.createFunctionsButton.setText(_translate("XrayWindow", "Create Minecraft Functions"))
        self.orText.setText(_translate("XrayWindow", "or"))
        self.andText.setText(_translate("XrayWindow", "and"))

if __name__ == "__main__":
    app = QApplication([])
    main_window = XrayWindow()
    main_window.show()
    app.exec()