"""
The Preview window: the model turning in a voxel volume, coloured with the window's settings, and how big it
will be in Minecraft at the chosen protein scale. The wording is in UI/messages.py (PREVIEW, PREVIEW_*).
"""
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtGui import QFont, QIcon

from PDB2MC import build, resources
from . import messages
from .utilities import apply_message_style
from .voxel_view import VoxelVolume, model_voxels

VOLUME_SIZE = 360


def size_text(size, scale):
    """The size estimate of a model as rich text, with a warning when it is too tall or very large."""
    shown = {key: f"{value:,}" if isinstance(value, int) and not isinstance(value, bool) else value
             for key, value in size.items()}
    text = messages.PREVIEW.render(scale=f"{scale:g}", **shown)
    if size['too_tall']:
        text += messages.PREVIEW_TOO_TALL.render(height=shown['height'], limit=f"{build.WORLD_HEIGHT:,}")
    elif size['large']:
        text += messages.PREVIEW_LARGE.render(chunks=shown['chunks'])
    return text


class PreviewDialog(QtWidgets.QDialog):
    def __init__(self, structure, config, mode, parent=None):
        super().__init__(parent)
        self.setWindowTitle(messages.PREVIEW.title)
        self.setWindowIcon(QIcon(resources.image('icons', 'logo.png')))
        apply_message_style(self)
        self.size = build.model_size(structure, config, mode)

        self.volume = VoxelVolume(self, size=VOLUME_SIZE)
        self.volume.set_model(*model_voxels(structure, config))
        # Show the whole model at once rather than filling it up as the progress window does
        self.volume.set_progress(100)
        self.volume.shown = 1.0

        self.label = QtWidgets.QLabel(self)
        self.label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.label.setFont(QFont(messages.FONT_FAMILY, messages.PREVIEW.font_size))
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.label.setText(size_text(self.size, config.get('scale', 1.0)))
        self.label.setFixedWidth(VOLUME_SIZE)

        self.closeButton = QtWidgets.QPushButton(messages.PREVIEW.button, self)
        self.closeButton.setDefault(True)
        self.closeButton.clicked.connect(self.close)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.volume, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.label)
        layout.addWidget(self.closeButton, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetFixedSize)

    def closeEvent(self, event):
        self.volume.stop()
        super().closeEvent(event)
