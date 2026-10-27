"""
Experimental 3D preview of a structure's surface points (not yet wired into the main program).
Requires PyOpenGL (pip install PyOpenGL), which is not a PDB2MC dependency.
Run directly: python -m UI.rotation_window
"""
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt6.QtGui import QAction
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from PDB2MC import pdb_manipulation as pdbm

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle('3D Viewer')

        self.glWidget = GLWidget(self)
        self.setCentralWidget(self.glWidget)

        openFile = QAction('Open', self)
        openFile.triggered.connect(self.showDialog)
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)

    def showDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '', 'Structure files (*.pdb *.cif)')

        if fname[0]:
            self.glWidget.load_points(fname[0])

class GLWidget(QOpenGLWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.points = None
        self.rotX = 0.0
        self.rotY = 0.0
        self.lastPos = None

    def load_points(self, fname):
        pdb_df = pdbm.structure_to_df(pdbm.load_structure(fname))
        rounded = pdbm.round_df(pdb_df)
        rounded = rounded.drop_duplicates(subset=['X', 'Y', 'Z'], keep='first')

        # Limit the number of points
        if len(rounded) > 10000:  # Adjust this value as needed
            rounded = rounded.sample(10000)  # Adjust this value as needed

        surface = pdbm.construct_surface_array(rounded)
        # Occupied voxels -> point cloud centred on the origin and scaled to fit the view
        points = np.argwhere(surface[::2, ::2, ::2] > 0).astype(np.float32)
        if len(points):
            points -= points.mean(axis=0)
            points /= max(1.0, float(np.abs(points).max()))
        self.points = points
        self.update()

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.points is not None and len(self.points):
            glPushMatrix()
            glRotatef(self.rotX, 1.0, 0.0, 0.0)
            glRotatef(self.rotY, 0.0, 1.0, 0.0)

            glColor3f(1.0, 1.0, 1.0)
            glBegin(GL_POINTS)
            for point in self.points:
                glVertex3fv(point)
            glEnd()
            glPopMatrix()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60.0, w / max(1, h), 0.01, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

    def mousePressEvent(self, event):
        self.lastPos = event.position()

    def mouseMoveEvent(self, event):
        if self.lastPos is None:
            self.lastPos = event.position()
        dx = event.position().x() - self.lastPos.x()
        dy = event.position().y() - self.lastPos.y()

        if event.buttons() & (Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton):
            self.rotX += dy
            self.rotY += dx

        self.lastPos = event.position()
        self.update()

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
