from PyQt6 import QtWidgets
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
from .sidebar import Sidebar, SIDEBAR_WIDTH
from .utilities import InformationBox  # reuse existing popup
from PDB2MC import resources

GITHUB_URL = "https://github.com/markus-nevil/PDB2MC"
RCSB_URL = "https://www.rcsb.org/"

# Windows opened through open_mode_window. Holding a reference keeps a window alive after the
# window that opened it is hidden; without one, PyQt garbage-collects it and it vanishes immediately.
_open_windows = {}


def create_mode_window(mode_name):
    """Instantiate the window for a sidebar mode name, or None for an unknown name."""
    if mode_name == "Custom":
        from .custom_window import CustomWindow
        return CustomWindow()
    if mode_name == "Skeleton":
        from .skeleton_window import SkeletonWindow
        return SkeletonWindow()
    if mode_name == "X-Ray":
        from .xray_window import XrayWindow
        return XrayWindow()
    if mode_name == "Space Filling":
        from .space_filling_window import spWindow
        return spWindow()
    if mode_name == "Amino Acids":
        from .amino_acids_window import AAWindow
        return AAWindow()
    if mode_name == "Ribbon":
        from .ribbon_window import RibbonWindow
        return RibbonWindow()
    if mode_name == "Tools":
        from .tool_window import ToolWindow
        return ToolWindow()
    return None


def open_mode_window(mode_name, current=None):
    """Show the window for mode_name and hide `current`. Re-selecting the current mode does nothing."""
    if current is not None and getattr(current, "MODE_NAME", None) == mode_name:
        return current
    window = create_mode_window(mode_name)
    if window is None:
        return None
    _open_windows[mode_name] = window
    window.show()
    if current is not None:
        current.hide()
    return window


def open_help(parent=None):
    from .help_window import HelpWindow
    help_window = HelpWindow.instance()
    help_window.show()
    help_window.raise_()
    help_window.activateWindow()
    if parent is not None and parent.screen() is not None:
        # centre on the screen of the window that asked for help
        frame_geometry = help_window.frameGeometry()
        frame_geometry.moveCenter(parent.screen().availableGeometry().center())
        help_window.move(frame_geometry.topLeft())
    return help_window


def show_information_box(owner, title_text, text, icon_path):
    """Show an InformationBox, keeping a reference on `owner` so it is not garbage-collected."""
    box = InformationBox()
    box.set_text(text)
    box.set_title(title_text)
    box.set_icon(icon_path)
    box.show()
    owner.info_box = box
    return box


def connect_sidebar(window, sidebar):
    """Wire a Sidebar's signals to the standard actions for `window`."""
    sidebar.mode_selected.connect(lambda mode: open_mode_window(mode, window))
    sidebar.tools_requested.connect(lambda: open_mode_window("Tools", window))
    sidebar.help_requested.connect(lambda: open_help(window))
    sidebar.github_requested.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
    sidebar.rcsb_requested.connect(lambda: QDesktopServices.openUrl(QUrl(RCSB_URL)))


class BaseModeWindow(QtWidgets.QMainWindow):
    """
    Base window for mode-specific windows.
    Left column is a Sidebar (fixed width), right column is a content area for derived windows to populate.
    Set MODE_NAME in subclasses so re-selecting the current mode is a no-op.
    """
    MODE_NAME = None

    def __init__(self, width: int = 600, height: int = 431, sidebar_width: int = SIDEBAR_WIDTH):
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
        self.sidebar = Sidebar(central, width=self._sidebar_width)
        hbox.addWidget(self.sidebar)

        # Content area (subclasses will add their widgets to content_layout)
        self.content_widget = QtWidgets.QWidget(central)
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(6)
        hbox.addWidget(self.content_widget, 1)  # stretch: content takes remaining space

        self.setCentralWidget(central)
        connect_sidebar(self, self.sidebar)

    def show_information_box(self, title_text, text, icon_path):
        return show_information_box(self, title_text, text, icon_path)

    @staticmethod
    def icon(name):
        """Absolute path of an icon in UI/images/icons."""
        return resources.image('icons', name)
