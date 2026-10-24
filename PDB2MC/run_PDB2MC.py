import os
import sys
import requests

from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import QThread, pyqtSignal
from UI.base_mode_window import open_help, open_mode_window
from UI.utilities import InformationBox

# Version handling
from packaging import version as packaging_version
from PDB2MC.version import version
from PDB2MC import resources

MODE_ATTRIBUTES = {
    "Custom": "custom_window", "Skeleton": "skeleton_window", "X-Ray": "xray_window",
    "Space Filling": "space_filling_window", "Ribbon": "ribbon_window",
    "Amino Acids": "amino_acids_window", "Tools": "tool_window",
}


def latest_release(repo="markus-nevil/PDB2MC", timeout=5):
    """Tag of the latest GitHub release, or None when it can't be fetched."""
    try:
        response = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", timeout=timeout)
        response.raise_for_status()
        return response.json().get("tag_name")
    except Exception:
        return None


def is_newer(remote, local=version):
    try:
        return packaging_version.parse(str(local)) < packaging_version.parse(str(remote))
    except Exception:
        return False


class UpdateCheck(QThread):
    """Looks up the latest release in the background; emits newer_version when it beats this version."""
    newer_version = pyqtSignal(str)

    def run(self):
        remote = latest_release()
        if remote is not None and is_newer(remote):
            self.newer_version.emit(str(packaging_version.parse(str(remote))))


class MainWindow(QMainWindow):
    """
    Main application window for PDB2MC.
    Handles UI setup, navigation, and version checking.
    """
    def __init__(self):
        super().__init__()

        self.setObjectName("MainWindow")
        self.setWindowTitle("Welcome to PDB2MC")
        self.setFixedSize(929, 621)
        os.chdir(get_images_path())

        self.setWindowIcon(QIcon('images/icons/logo.png'))

        # Central widget and background GIF
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

        # Version label
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

        # Mode selection combo box
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

        # Title image
        labelTitle = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap("images/title.png")
        pixmap = pixmap.scaled(500, 500)
        labelTitle.setScaledContents(True)
        labelTitle.setGeometry(QtCore.QRect(215, 50, 500, 118))
        labelTitle.setPixmap(pixmap)
        labelTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.layout().addWidget(labelTitle)

        # Help button
        self.help = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(25)
        self.help.setFont(font)
        self.help.setObjectName("help")
        self.help.setGeometry(QtCore.QRect(755, 560, 150, 51))

        # Labels for UI
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

        # Connect signals
        self.comboBox.currentTextChanged.connect(self.handle_dropdown_change)
        self.help.clicked.connect(self.handle_help_button)

        # Check for updates after startup, off the GUI thread (the request can take seconds offline)
        self.update_check = UpdateCheck(self)
        self.update_check.newer_version.connect(self.announce_update)
        QtCore.QTimer.singleShot(1000, self.is_outdated)

    def is_outdated(self):
        """Start the background check for a newer GitHub release."""
        if not self.update_check.isRunning():
            self.update_check.start()

    def announce_update(self, remote_version):
        self.show_information_box(
            title_text="New Version Available!",
            text=f"There is a new PDB2MC version available.\n"
                 f"Download Release v{remote_version} from Github.\n"
                 f"https://github.com/markus-nevil/PDB2MC",
            icon_path="images/icons/icon_good.png"
        )

    def show_information_box(self, title_text, text, icon_path):
        """
        Shows an information popup window.
        """
        self.info_box = InformationBox()
        self.info_box.set_text(text)
        self.info_box.set_title(title_text)
        self.info_box.set_icon(icon_path)
        self.info_box.show()

    def handle_help_button(self):
        """Opens the help window, centred on the screen."""
        open_help(self)

    def handle_dropdown_change(self, text):
        """Opens the window of the selected mode and hides the main window."""
        window = open_mode_window(text.strip(), self)
        if window is not None:
            # kept as attributes for callers that look up the opened window
            setattr(self, MODE_ATTRIBUTES.get(text.strip(), "mode_window"), window)

    def retranslateUi(self, MainWindow):
        """
        Sets UI text for widgets.
        """
        _translate = QtCore.QCoreApplication.translate
        self.comboBox.setItemText(1, _translate("MainWindow", "Custom"))
        self.help.setText(_translate("MainWindow", "Help"))
        self.label_2.setText(_translate("MainWindow", "Select Mode:"))

def get_images_path():
    """
    Returns the UI directory (relative paths such as 'images/bg.gif' resolve against it),
    for a source checkout, an installed package or a PyInstaller build.
    """
    return resources.ui_dir()

def main():
    """
    Entry point for the application.
    """
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    try:
        app.exec()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()