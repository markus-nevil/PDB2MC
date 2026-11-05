"""
The welcome window's background: example models fading from one to the next.

It replaces an animated GIF of the same pictures (40 MB, because every in-between frame of each fade was stored);
the fades are now drawn as the window runs, from the pictures in UI/images/welcome.
"""
import glob
import os

from PyQt6 import QtCore, QtGui, QtWidgets

from PDB2MC import resources

# How long each picture stays, and how long it takes to fade into the next (the GIF's own timing)
HOLD_MS = 2500
FADE_MS = 1900
FRAME_MS = 40


def welcome_pictures():
    """The pictures of the slideshow, in order."""
    return sorted(glob.glob(os.path.join(resources.image("welcome"), "welcome_*.jpg")),
                  key=lambda path: int(os.path.splitext(path)[0].rsplit("_", 1)[1]))


class Slideshow(QtWidgets.QWidget):
    def __init__(self, parent=None, pictures=None):
        super().__init__(parent)
        self.pixmaps = [QtGui.QPixmap(path) for path in (pictures or welcome_pictures())]
        self.pixmaps = [pixmap for pixmap in self.pixmaps if not pixmap.isNull()]
        self._clock = QtCore.QElapsedTimer()
        self._clock.start()
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.update)
        if len(self.pixmaps) > 1:
            self._timer.start(FRAME_MS)

    def state(self, elapsed_ms):
        """(picture shown, next picture, how far the fade into the next has gone, 0-1) at a time."""
        count = len(self.pixmaps)
        step, into = divmod(int(elapsed_ms), HOLD_MS + FADE_MS)
        current = step % count
        return current, (current + 1) % count, max(0.0, (into - HOLD_MS) / FADE_MS)

    def paintEvent(self, event):
        if not self.pixmaps:
            return
        painter = QtGui.QPainter(self)
        current, following, fade = self.state(self._clock.elapsed())
        painter.drawPixmap(0, 0, self.pixmaps[current])
        if fade > 0:
            painter.setOpacity(fade)
            painter.drawPixmap(0, 0, self.pixmaps[following])
        painter.end()

    def stop(self):
        self._timer.stop()
