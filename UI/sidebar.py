from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel, QPushButton

# Master constants (change these to adjust sidebar globally)
SIDEBAR_WIDTH = 110            # master sidebar width (px)
SIDEBAR_PADDING = 12           # horizontal padding inside sidebar
SIDEBAR_BUTTON_HEIGHT = 30     # uniform button height (px)

class Sidebar(QWidget):
    """
    Left-hand navigation column shared by the mode windows.
    Emits mode_selected(<mode name>) and *_requested signals; windows connect to these instead of
    wiring each button themselves (see base_mode_window.connect_sidebar).
    """
    mode_selected = QtCore.pyqtSignal(str)
    help_requested = QtCore.pyqtSignal()
    github_requested = QtCore.pyqtSignal()
    rcsb_requested = QtCore.pyqtSignal()
    tools_requested = QtCore.pyqtSignal()

    def __init__(self, parent=None, width: int | None = None, padding: int | None = None):
        super().__init__(parent)
        self.setObjectName("sidebar")

        # Use provided width or the module-level master width
        self._master_width = width if (width is not None) else SIDEBAR_WIDTH
        self.setFixedWidth(self._master_width)

        # padding and button sizing
        self._padding = padding if (padding is not None) else SIDEBAR_PADDING
        self._button_height = SIDEBAR_BUTTON_HEIGHT

        # store created buttons and their original texts for dynamic eliding
        self._buttons = []
        self._button_texts = {}

        # Ensure the sidebar can expand vertically
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)

        # Main vertical layout with horizontal padding
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(self._padding, 6, self._padding, 6)
        self._layout.setSpacing(6)

        # --- Top group: mode switch label + mode buttons ---
        self.switchModeLabel = QLabel("Switch Mode", parent=self)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setUnderline(False)
        self.switchModeLabel.setFont(font)
        self.switchModeLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.switchModeLabel.setObjectName("switchModeLabel")
        self.switchModeLabel.setWordWrap(True)
        self.switchModeLabel.setFixedWidth(max(10, self._master_width - (self._padding * 2)))
        self._layout.addWidget(self.switchModeLabel)

        # Buttons factory
        def make_button(name, point=11):
            b = QPushButton(name, parent=self)
            f = QtGui.QFont()
            f.setPointSize(point)
            b.setFont(f)
            b.setObjectName(name.replace(" ", "") + "Button")
            # register and size
            self._button_texts[b] = name
            self._buttons.append(b)
            try:
                b.setFixedWidth(max(10, self._master_width - (self._padding * 2)))
                b.setFixedHeight(self._button_height)
            except Exception:
                pass
            return b

        self.CustomMode = make_button("Custom", 11)
        self.SkeletonMode = make_button("Skeleton", 11)
        self.XRayMode = make_button("X-Ray", 11)
        self.SpaceFillingMode = make_button("Space Filling", 8)
        self.AminoAcidMode = make_button("Amino Acids", 8)
        self.RibbonMode = make_button("Ribbon", 11)

        for w in (self.CustomMode, self.SkeletonMode, self.XRayMode,
                  self.SpaceFillingMode, self.RibbonMode, self.AminoAcidMode):
            self._layout.addWidget(w)
            # emit the full mode name; the visible text may be elided
            w.clicked.connect(lambda _checked=False, mode=self._button_texts[w]: self.mode_selected.emit(mode))

        # divider
        self.modeInfoHLine = QFrame(parent=self)
        self.modeInfoHLine.setFrameShape(QFrame.Shape.HLine)
        self.modeInfoHLine.setFrameShadow(QFrame.Shadow.Sunken)
        self.modeInfoHLine.setObjectName("modeInfoHLine")
        self._layout.addWidget(self.modeInfoHLine)

        self._layout.addStretch(1)

        # middle group: label + buttons
        self.mc2pdbLabel = QLabel("PDB2MC", parent=self)
        f2 = QtGui.QFont()
        f2.setPointSize(11)
        self.mc2pdbLabel.setFont(f2)
        self.mc2pdbLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.mc2pdbLabel.setObjectName("mc2pdbLabel")
        self.mc2pdbLabel.setWordWrap(True)
        self.mc2pdbLabel.setFixedWidth(max(10, self._master_width - (self._padding * 2)))
        self._layout.addWidget(self.mc2pdbLabel)

        self.help = QPushButton("Help", parent=self)
        self.github = QPushButton("Github", parent=self)
        self.tools = QPushButton("Tools", parent=self)
        for btn in (self.help, self.github, self.tools):
            f = QtGui.QFont()
            f.setPointSize(10)
            btn.setFont(f)
            self._button_texts[btn] = btn.text()
            self._buttons.append(btn)
            try:
                btn.setFixedWidth(max(10, self._master_width - (self._padding * 2)))
                btn.setFixedHeight(self._button_height)
            except Exception:
                pass
            self._layout.addWidget(btn)

        # another divider + db label + rcsb button
        self.infoDatabaseHLine = QFrame(parent=self)
        self.infoDatabaseHLine.setFrameShape(QFrame.Shape.HLine)
        self.infoDatabaseHLine.setFrameShadow(QFrame.Shadow.Sunken)
        self.infoDatabaseHLine.setObjectName("infoDatabaseHLine")
        self._layout.addWidget(self.infoDatabaseHLine)

        self.pdbDatabaseLabel = QLabel("PDB Database", parent=self)
        f3 = QtGui.QFont()
        f3.setPointSize(10)
        self.pdbDatabaseLabel.setFont(f3)
        self.pdbDatabaseLabel.setObjectName("pdbDatabaseLabel")
        # allow wrapping and use the same internal width calculation as other labels
        self.pdbDatabaseLabel.setWordWrap(True)
        self.pdbDatabaseLabel.setFixedWidth(max(10, self._master_width - (self._padding * 2)))
        self.pdbDatabaseLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self.pdbDatabaseLabel)

        self.rcsbButton = QPushButton("RCSB.org", parent=self)
        f4 = QtGui.QFont()
        f4.setPointSize(9)
        self.rcsbButton.setFont(f4)
        self._button_texts[self.rcsbButton] = self.rcsbButton.text()
        self._buttons.append(self.rcsbButton)
        try:
            self.rcsbButton.setFixedWidth(max(10, self._master_width - (self._padding * 2)))
            self.rcsbButton.setFixedHeight(self._button_height)
        except Exception:
            pass
        self._layout.addWidget(self.rcsbButton)

        self._layout.addStretch(2)

        self.help.clicked.connect(self.help_requested)
        self.github.clicked.connect(self.github_requested)
        self.tools.clicked.connect(self.tools_requested)
        self.rcsbButton.clicked.connect(self.rcsb_requested)

        # right-edge vertical separator (visual)
        self.vSepLine = QFrame(self)
        self.vSepLine.setFrameShadow(QFrame.Shadow.Sunken)
        self.vSepLine.setLineWidth(2)
        self.vSepLine.setFrameShape(QFrame.Shape.VLine)
        self.vSepLine.setObjectName("vSepLine")
        self.vSepLine.setGeometry(max(0, self._master_width - 4), 0, 4, max(1, self.height()))

        # parent event filter for height sync
        self._parent_widget = None
        if isinstance(parent, QtWidgets.QWidget):
            try:
                parent.installEventFilter(self)
                self._parent_widget = parent
                if parent.height() > 0:
                    self.setFixedHeight(parent.height())
            except Exception:
                pass

        # finalize button text sizing now that geometry is set
        self._elide_button_texts()

    def eventFilter(self, obj, event):
        # Only parent resizes matter; this filter sees every parent event (paint, mouse move, ...)
        if obj is self._parent_widget and event.type() == QtCore.QEvent.Type.Resize:
            new_h = obj.height()
            if new_h > 0:
                # setFixedHeight triggers resizeEvent, which re-positions the separator and re-elides
                self.setFixedHeight(new_h)
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        try:
            if hasattr(self, "vSepLine"):
                w = max(0, self.width())
                self.vSepLine.setGeometry(max(0, w - 4), 0, 4, max(1, self.height()))
        except Exception:
            pass

        try:
            self._elide_button_texts()
        except Exception:
            pass

        super().resizeEvent(event)

    def _elide_button_texts(self):
        for btn in list(self._buttons):
            try:
                orig = self._button_texts.get(btn, btn.text())
                fm = QtGui.QFontMetrics(btn.font())
                avail = max(8, btn.width() - 8)
                elided = fm.elidedText(orig, QtCore.Qt.TextElideMode.ElideRight, avail)
                btn.setText(elided)
                btn.setToolTip(orig)
            except Exception:
                pass
