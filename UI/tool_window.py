import os

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow

from PDB2MC import minecraft_functions as mcf, resources, triggers
from UI import messages, tooltips
from UI.base_mode_window import connect_sidebar, icon_path
from UI.session import SESSION
from UI.settings_dialogs import DefaultFolderDialog, MetalIonDialog
from UI.sidebar import Sidebar, SIDEBAR_WIDTH
from UI.utilities import MinecraftPopup, get_presets_path, show_message

TOOL_BUTTONS = [
    ("metalIonSettings", "Metal Ion Settings"),
    ("defaultFolder", "Default PDB/CIF Folder"),
    ("removeFunctionFiles", "Remove Function Files"),
    ("openFunctionDir", "Open Minecraft Function Directory"),
    ("openIncludedDir", "Open 'Presets' Directory"),
    ("movePreset", "Copy Blank World to Minecraft"),
]


def open_folder(path):
    QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(os.path.normpath(path)))


class ToolWindow(QMainWindow):
    MODE_NAME = "Tools"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Utilities")
        self.setWindowIcon(QIcon(icon_path('logo.png')))
        width, height = 450, 411
        self.centralwidget = QtWidgets.QWidget(parent=self)
        self.setCentralWidget(self.centralwidget)
        self.bg = QtWidgets.QLabel(parent=self.centralwidget)
        self.bg.setPixmap(QtGui.QPixmap(resources.image("MC2PDB bg.png")))
        self.bg.setScaledContents(True)
        self.bg.setGeometry(0, 0, width, height)

        font = QtGui.QFont()
        font.setPointSize(11)
        for i, (name, text) in enumerate(TOOL_BUTTONS):
            button = QtWidgets.QPushButton(text, parent=self.centralwidget)
            button.setFont(font)
            button.setGeometry(QtCore.QRect(SIDEBAR_WIDTH + 40, 20 + 60 * i, 260, 50))
            button.setToolTip(tooltips.tip(tooltips.TOOLS, name))
            setattr(self, name, button)

        self.sidebar = Sidebar(self.centralwidget, width=SIDEBAR_WIDTH)
        self.sidebar.setGeometry(0, 0, SIDEBAR_WIDTH, height)
        self.sidebar.setFixedHeight(height)
        connect_sidebar(self, self.sidebar)
        self.setFixedSize(width, height)

        self.metalIonSettings.clicked.connect(self.handle_metal_ion_settings)
        self.defaultFolder.clicked.connect(self.handle_default_folder)
        self.removeFunctionFiles.clicked.connect(self.handle_remove_function_files)
        self.openFunctionDir.clicked.connect(self.handle_open_function_dir)
        self.openIncludedDir.clicked.connect(lambda: open_folder(get_presets_path()))
        self.movePreset.clicked.connect(self.handle_move_preset_button)

    def choose_save(self):
        """The Minecraft save picked in a mode window, or ask for one."""
        if SESSION.save_path:
            return SESSION.save_path
        popup = MinecraftPopup()
        if popup.selected_directory:
            SESSION.save_path = popup.selected_directory
        return popup.selected_directory

    def handle_metal_ion_settings(self):
        self.metal_dialog = MetalIonDialog(self)
        self.metal_dialog.exec()

    def handle_default_folder(self):
        self.folder_dialog = DefaultFolderDialog(self)
        self.folder_dialog.exec()

    def handle_remove_function_files(self):
        self.selectMinecraft = MinecraftPopup()
        if self.selectMinecraft.selected_directory is None:
            return
        save = self.selectMinecraft.selected_directory
        mcf.delete_nbt_mcfunctions_from_dir(save)
        triggers.sync(save)
        show_message(self, messages.FILES_REMOVED, folder=mcf.world_dir(save))

    def handle_open_function_dir(self):
        save = self.choose_save()
        if save:
            open_folder(save)

    def handle_move_preset_button(self):
        wd = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", ".minecraft", "saves")
        mcf.copy_blank_world(wd)
        show_message(self, messages.BLANK_WORLD_COPIED)


if __name__ == "__main__":
    app = QApplication([])
    main_window = ToolWindow()
    main_window.show()
    app.exec()
