import os
import sys
import requests

from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6 import QtCore, QtGui, QtWidgets

# UI windows
from UI import (
    help_window, custom_window, skeleton_window, xray_window,
    space_filling_window, ribbon_window, amino_acids_window, tool_window
)
from UI.utilities import InformationBox

# Version handling
from packaging import version as packaging_version
from importlib.metadata import version, PackageNotFoundError
from PDB2MC.version import version

help_window = None

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

        # Check for updates after startup
        self.timer = QtCore.QTimer()
        self.timer.singleShot(1000, self.is_outdated)

    def is_outdated(self):
        """
        Checks if the local version is older than the latest GitHub release.
        Shows a popup if an update is available.
        Silently ignores connection errors.
        """
        repo_owner = "markus-nevil"
        repo_name = "PDB2MC"

        try:
            response = requests.get(
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest", timeout=5
            )
            response.raise_for_status()
            latest_release = response.json().get("tag_name", None)
        except requests.ConnectionError:
            return  # No internet, ignore
        except Exception:
            return  # Any other error, ignore

        if latest_release is not None:
            try:
                local_version = packaging_version.parse(str(version))
                remote_version = packaging_version.parse(str(latest_release))
                if local_version < remote_version:
                    self.show_information_box(
                        title_text="New Version Available!",
                        text=f"There is a new PDB2MC version available.\n"
                             f"Download Release v{remote_version} from Github.\n"
                             f"https://github.com/markus-nevil/PDB2MC",
                        icon_path="images/icons/icon_good.png"
                    )
            except Exception:
                pass  # Ignore version parsing errors

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
        """
        Opens the help window, centering it on the screen.
        """
        from UI.help_window import HelpWindow
        help_window = HelpWindow.instance()
        if help_window.isVisible():
            help_window.raise_()
            help_window.activateWindow()
        else:
            help_window.show()

        # Center the help window
        frame_geometry = help_window.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        help_window.move(frame_geometry.topLeft())

    def handle_dropdown_change(self, text):
        """
        Handles mode selection from the dropdown.
        Opens the corresponding window and hides the main window.
        """
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
        """
        Sets UI text for widgets.
        """
        _translate = QtCore.QCoreApplication.translate
        self.comboBox.setItemText(1, _translate("MainWindow", "Custom"))
        self.help.setText(_translate("MainWindow", "Help"))
        self.label_2.setText(_translate("MainWindow", "Select Mode:"))

def get_images_path():
    """
    Returns the path to the images directory, depending on execution context.
    """
    if getattr(sys, 'frozen', False):
        # Compiled executable
        import importlib.resources as importlib_resources
        images_dir = importlib_resources.files('UI').joinpath('images')
        return images_dir
    else:
        # Python script or installed package
        current_dir = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(current_dir, '..', 'UI')
        return images_dir

def get_version(package_name):
    """
    Returns the installed version of a package, or None if not found.
    """
    try:
        return version(package_name)
    except PackageNotFoundError:
        return None

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