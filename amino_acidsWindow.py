import os
from shutil import copyfile
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QApplication, QListWidget, QPushButton, QMainWindow, QMessageBox, QLabel, QVBoxLayout, QWidget, QStylePainter
from PyQt6.QtGui import QMovie, QPalette, QBrush, QPixmap, QDesktopServices, QIcon
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6 import QtCore, QtGui, QtWidgets

import UI
import skeletonWindow
import xrayWindow
import space_fillingWindow
import ribbonWindow
import amino_acidsWindow
import customWindow
from variables import decorative_blocks
import pandas as pd

import pdb_manipulation as pdbm
import minecraft_functions as mcf
import amino_acids
from utilUI import MyComboBox, NothingSelected, IncludedPDBPopup, MinecraftPopup, FileExplorerPopup

class AAWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_pdb_file = None
        self.user_minecraft_save = None
        self.setWindowTitle("Amino Acid Mode")
        self.setWindowIcon(QIcon('images/icons/logo.png'))

        self.resize(695, 411)
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
            "wool": "icon64",
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
            "light_stained_glass": "icon15",
            "white_stained_glass": "icon16"
        }

        color_boxes = [self.AlaColorBox, self.ArgColorBox, self.AsnColorBox, self.AspColorBox,
                       self.CysColorBox, self.GlnColorBox, self.GluColorBox, self.GlyColorBox, self.HisColorBox,
                       self.IleColorBox, self.LeuColorBox, self.LysColorBox, self.MetColorBox, self.PheColorBox,
                       self.ProColorBox, self.SerColorBox, self.ThrColorBox, self.TrpColorBox, self.TyrColorBox,
                       self.ValColorBox, self.backboneColorBox]

        for color_box in color_boxes:
            for value, icon in icon_dict.items():
                color_box.addItem(eval(icon), value)
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

        self.backboneColorLabel.setGeometry(QtCore.QRect(110, 270, 120, 21))
        self.backboneColorBox.setGeometry(QtCore.QRect(210, 270, 175, 22))
        self.showBackboneCheck.setGeometry(QtCore.QRect(395, 270, 121, 17))
        self.backboneScaleSpinBox.setGeometry(QtCore.QRect(510, 270, 62, 22))

        #self.colorByBackboneCheck.setGeometry(QtCore.QRect(240, 530, 155, 21))
        #self.bScaleLabel.setGeometry(QtCore.QRect(110, 270, 111, 21))

        self.pScaleLabel.setGeometry(QtCore.QRect(110, 300, 71, 21))
        self.pScaleSpinBox.setGeometry(QtCore.QRect(210, 300, 62, 22))

        self.otherMoleculeCheck.setGeometry(QtCore.QRect(240, 2280, 131, 17))
        self.aScaleLabel.setGeometry(QtCore.QRect(395, 300, 61, 21))
        self.aScaleSpinBox.setGeometry(QtCore.QRect(510, 300, 62, 22))

        self.selectPDBFileButton.setGeometry(QtCore.QRect(110, 340, 91, 23))
        self.orText.setGeometry(QtCore.QRect(210, 340, 31, 21))
        self.selectIncludedPDBButton.setGeometry(QtCore.QRect(250, 340, 141, 23))
        self.andText.setGeometry(QtCore.QRect(400, 340, 31, 21))
        self.selectMinecraftSaveButton.setGeometry(QtCore.QRect(450, 340, 141, 23))

        self.simpleOutputCheck.setGeometry(QtCore.QRect(110, 375, 100, 31))
        self.createFunctionsButton.setGeometry(QtCore.QRect(230, 375, 181, 31))

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

        #self.otherColorBox.focusOut.connect(lambda: self.check_input(self.otherColorBox, decorative_blocks))
        self.backboneColorBox.focusOut.connect(lambda: self.check_input(self.backboneColorBox, decorative_blocks))
        self.AlaColorBox.focusOut.connect(lambda: self.check_input(self.AlaColorBox, decorative_blocks))
        self.ArgColorBox.focusOut.connect(lambda: self.check_input(self.ArgColorBox, decorative_blocks))
        self.AsnColorBox.focusOut.connect(lambda: self.check_input(self.AsnColorBox, decorative_blocks))
        self.AspColorBox.focusOut.connect(lambda: self.check_input(self.AspColorBox, decorative_blocks))
        self.CysColorBox.focusOut.connect(lambda: self.check_input(self.CysColorBox, decorative_blocks))
        self.GlnColorBox.focusOut.connect(lambda: self.check_input(self.GlnColorBox, decorative_blocks))
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
        self.selectMinecraft = MinecraftPopup()
        if self.selectMinecraft.selected_directory is None:
            QMessageBox.critical(None, "Error", "Remember to select a Minecraft save.")
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

            try:
                print("fix")
                amino_acids.run_mode(rounded, config_data, pdb_name, mc_dir)
            except Exception as e:
                print(f"Error: {e}")

            mcfiles = mcf.find_mcfunctions(mc_dir, pdb_name.lower())

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
        self.Ribbon = ribbonWindow.RibbonWindow()
        self.Ribbon.show()
        self.hide()


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
        #self.otherColorLabel.setText(_translate("AAWindow", "Select other color:"))
        self.aScaleLabel.setText(_translate("AAWindow", "Atom scale:"))
        self.otherMoleculeCheck.setText(_translate("AAWindow", "Show other molecules"))
        self.showBackboneCheck.setText(_translate("AAWindow", "Show backbone"))
        #self.showSidechainCheck.setText(_translate("AAWindow", "Show sidechain"))
        #self.colorByBackboneCheck.setText(_translate("AAWindow", "Color backbone by chain"))
        self.pScaleLabel.setText(_translate("AAWindow", "Protein scale:"))
        #self.bScaleLabel.setText(_translate("AAWindow", "Backbone scale:"))
        self.selectIncludedPDBButton.setText(_translate("AAWindow", "Select Included PDB File"))
        self.selectMinecraftSaveButton.setText(_translate("AAWindow", "Select Minecraft Save"))
        self.simpleOutputCheck.setText(_translate("AAWindow", "Simple output"))
        self.selectPDBFileButton.setText(_translate("AAWindow", "Select PDB File"))
        self.createFunctionsButton.setText(_translate("AAWindow", "Create Minecraft Functions"))
        self.orText.setText(_translate("AAWindow", "or"))
        self.andText.setText(_translate("AAWindow", "and"))

if __name__ == "__main__":
    app = QApplication([])
    main_window = AAWindow()
    main_window.show()
    try:
        app.exec()
    except KeyboardInterrupt:
        pass