from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
import os
from .sidebar import Sidebar
from .utilities import InformationBox  # reuse existing popup
from PDB2MC import pdb_manipulation as pdbm  # some windows use it; safe to import

class BaseModeWindow(QtWidgets.QMainWindow):
    """
    Base window for all mode-specific windows.
    Left column is a Sidebar (fixed width), right column is a content area for derived windows to populate.
    Provides default handlers for sidebar signals (can be overridden in subclasses).
    """
    def __init__(self, width: int = 600, height: int = 431, sidebar_width: int = 90):
        super().__init__()
        self.resize(width, height)
        self._sidebar_width = sidebar_width
        self._init_ui()

    def _init_ui(self):
        # central widget with horizontal layout: sidebar + content
        central = QtWidgets.QWidget(self)
        hbox = QtWidgets.QHBoxLayout(central)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self, fixed_width=self._sidebar_width)
        hbox.addWidget(self.sidebar)

        # Content area (subclasses will add their widgets to content_layout)
        self.content_widget = QtWidgets.QWidget(self)
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(6)
        hbox.addWidget(self.content_widget, 1)  # stretch: content takes remaining space

        self.setCentralWidget(central)

        # connect sidebar signals to handlers (can be overridden)
        self.sidebar.mode_selected.connect(self.switch_mode)
        self.sidebar.help_requested.connect(self.open_help)
        self.sidebar.github_requested.connect(self.open_github)
        self.sidebar.rcsb_requested.connect(self.open_rcsb)
        self.sidebar.tools_requested.connect(self.open_tools)

    # Default handlers - subclasses can override or call super()
    def switch_mode(self, mode_name: str):
        """
        Default mode switch: imports and shows the selected mode window.
        Subclasses may override to provide custom behavior.
        """
        try:
            if mode_name == "Custom":
                from .custom_window import CustomWindow
                w = CustomWindow()
            elif mode_name == "Skeleton":
                from .skeleton_window import SkeletonWindow
                w = SkeletonWindow()
            elif mode_name == "X-Ray":
                from .xray_window import XrayWindow
                w = XrayWindow()
            elif mode_name == "Space Filling":
                from .space_filling_window import spWindow
                w = spWindow()
            elif mode_name == "Amino Acids":
                from .amino_acids_window import AAWindow
                w = AAWindow()
            elif mode_name == "Ribbon":
                from .ribbon_window import RibbonWindow
                w = RibbonWindow()
            else:
                return
            w.show()
            self.hide()
        except Exception as e:
            self.show_information_box("Error switching mode", str(e), "images/icons/icon_bad.png")

    def open_help(self):
        try:
            from .help_window import HelpWindow
            help_window = HelpWindow.instance()
            help_window.show()
            help_window.raise_()
            help_window.activateWindow()
        except Exception as e:
            self.show_information_box("Help error", str(e), "images/icons/icon_bad.png")

    def open_github(self):
        QDesktopServices.openUrl(QUrl("https://github.com/markus-nevil/mcpdb"))

    def open_rcsb(self):
        QDesktopServices.openUrl(QUrl("https://www.rcsb.org/"))

    def open_tools(self):
        try:
            from .tool_window import ToolWindow
            w = ToolWindow()
            w.show()
            self.hide()
        except Exception as e:
            self.show_information_box("Tools error", str(e), "images/icons/icon_bad.png")

    def show_information_box(self, title_text, text, icon_path):
        ib = InformationBox()
        ib.set_text(text)
        ib.set_title(title_text)
        ib.set_icon(icon_path)
        ib.show()

