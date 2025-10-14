import os

from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6 import QtCore, QtGui, QtWidgets
from UI import help_window, custom_window, skeleton_window, xray_window, space_filling_window, ribbon_window, amino_acids_window, tool_window
import sys
#import pkg_resources
import importlib.resources as importlib_resources
from packaging import version
from importlib.metadata import version, PackageNotFoundError
from PDB2MC.version import version
from UI.utilities import InformationBox
import requests

help_window = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setObjectName("MainWindow")
        self.setWindowTitle("Welcome to PDB2MC")
        self.setFixedSize(929, 621)
        os.chdir(get_images_path())

        self.setWindowIcon(QIcon('images/icons/logo.png'))

        self.centralwidget = QtWidgets.QWidget(parent=self)
        self.centralwidget.setObjectName("centralwidget")

        self.label = QtWidgets.QLabel(parent=self.centralwidget)
        self.label.setGeometry(QtCore.QRect(-130, 0, 1161, 631))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setText("")

        movie = QtGui.QMovie("images/bg.gif")
        self.label.setMovie(movie)
        movie.start()

        self.version_label = QLabel(f'Version: {version}', self)
        self.version_label.setGeometry(0, 0, 130, 30)
        self.version_label.move(5, 590)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(500)
        self.version_label.setFont(font)
        self.version_label.setStyleSheet("background-color: rgba(255, 255, 255, 127);")
        self.version_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.layout().addWidget(self.version_label)
        self.version_label.setObjectName("version_label")

        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.comboBox = QtWidgets.QComboBox(parent=self.centralwidget)
        self.comboBox.setGeometry(QtCore.QRect(340, 560, 231, 51))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.comboBox.setFont(font)
        self.comboBox.setToolTip("")
        self.comboBox.setToolTipDuration(5)
        self.comboBox.setWhatsThis("")
        self.comboBox.setFrame(True)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.setItemText(0, " -None Selected-")
        self.comboBox.addItem("Custom")
        self.comboBox.addItem("Skeleton")
        self.comboBox.addItem("X-Ray")
        self.comboBox.addItem("Space Filling")
        self.comboBox.addItem("Ribbon")
        self.comboBox.addItem("Amino Acids")
        self.comboBox.addItem("Tools")

        labelTitle = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap("images/title.png")
        pixmap = pixmap.scaled(500, 500)
        labelTitle.setScaledContents(True)
        labelTitle.setGeometry(QtCore.QRect(215, 50, 500, 118))

        labelTitle.setPixmap(pixmap)
        labelTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.layout().addWidget(labelTitle)

        self.help = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(25)
        self.help.setFont(font)
        self.help.setObjectName("help")
        self.help.setGeometry(QtCore.QRect(755, 560, 150, 51))

        self.label_2 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(340, 510, 141, 71))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setUnderline(True)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(270, 0, 371, 71))
        font = QtGui.QFont()
        font.setPointSize(29)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.setCentralWidget(self.centralwidget)
        self.retranslateUi(self)

        QtCore.QMetaObject.connectSlotsByName(self)

        # Connect the currentTextChanged signal to a slot method
        self.comboBox.currentTextChanged.connect(self.handle_dropdown_change)
        self.help.clicked.connect(self.handle_help_button)

        self.timer = QtCore.QTimer()
        self.timer.singleShot(1000, self.is_outdated)

    def is_outdated(self):

        #user_version = version.parse(version)
        repo_owner = "markus-nevil"
        repo_name = "PDB2MC"

        # Get the latest release from GitHub
        try:
            response = requests.get(f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest")
            response.raise_for_status()  # Raise an exception if the request failed
            latest_release = response.json()["tag_name"]
            print(latest_release)
        except requests.ConnectionError:
            return

        ## TODO: Implement the version check
        # # Compare the local version with the latest release
        # if latest_release is not None:
        #     if version.parse(user_version) < version.parse(latest_release):
        #         self.show_information_box(title_text=f"New Version Available!",
        #                                   text=f"There is a new PDB2MC version available.\n Download Release v{version.parse(latest_release)} from Github.\nhttps://github.com/markus-nevil/PDB2MC",
        #                                   icon_path="images/icons/icon_good.png")

    def show_information_box(self, title_text, text, icon_path):
        self.info_box = InformationBox()
        self.info_box.set_text(text)
        self.info_box.set_title(title_text)
        self.info_box.set_icon(icon_path)
        self.info_box.show()
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

    def handle_dropdown_change(self, text):
        if text == "Custom":
            self.custom_window = custom_window.CustomWindow()
            self.custom_window.show()
            self.hide()
        if text == "Skeleton":
            self.skeleton_window = skeleton_window.SkeletonWindow()
            self.skeleton_window.show()
            self.hide()
        if text == "X-Ray":
            self.xray_window = xray_window.XrayWindow()
            self.xray_window.show()
            self.hide()
        if text == "Space Filling":
            self.SpaceFilling = space_filling_window.spWindow()
            self.SpaceFilling.show()
            self.hide()
        if text == "Ribbon":
            self.ribbon_window = ribbon_window.RibbonWindow()
            self.ribbon_window.show()
            self.hide()
        if text == "Amino Acids":
            self.amino_acids_window = amino_acids_window.AAWindow()
            self.amino_acids_window.show()
            self.hide()
        if text == "Tools":
            self.tool_window = tool_window.ToolWindow()
            self.tool_window.show()
            self.hide()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        self.comboBox.setItemText(1, _translate("MainWindow", "Custom"))
        self.help.setText(_translate("MainWindow", "Help"))
        # self.comboBox.setItemText(4, _translate("MainWindow", "Space Filling"))
        # self.comboBox.setItemText(5, _translate("MainWindow", "Ribbon"))
        # self.comboBox.setItemText(6, _translate("MainWindow", "Amino Acids"))
        self.label_2.setText(_translate("MainWindow", "Select Mode:"))

def get_images_path():
    if getattr(sys, 'frozen', False):
        # The program is running as a compiled executable
        images_dir = importlib_resources.files('UI').joinpath('images')
        #images_dir = pkg_resources.resource_filename('UI', 'images')
        #images_dir = os.path.join(images_dir, '..')
        return images_dir
    else:
        # The program is running as a Python script or it's installed in the Python environment
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the UI/images directory
        images_dir = os.path.join(current_dir, '..', 'UI')
        return images_dir

# def get_version(package_name):
#     try:
#         return pkg_resources.get_distribution(package_name).version
#     except pkg_resources.DistributionNotFound:
#         return None

def get_version(package_name):
    try:
        return version(package_name)
    except PackageNotFoundError:
        return None

def main():
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    try:
        app.exec()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()