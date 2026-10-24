from PyQt6.QtWidgets import QApplication, QWidgetAction, QMainWindow, QFileDialog, QMenuBar
from PyQt6.QtOpenGL import QOpenGLWindow
from PyQt6.QtCore import Qt
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np
import pandas as pd
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

        openFile = QWidgetAction('Open', self)
        openFile.triggered.connect(self.showDialog)
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)

    def showDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')

        if fname[0]:
            self.glWidget.load_points(fname[0])

class GLWidget(QOpenGLWindow):
    def __init__(self, parent):
        QOpenGLWindow.__init__(self, parent)
        self.points = None
        self.rotX = 0.0
        self.rotY = 0.0
        self.lastPos = None

    def load_points(self, fname):
        print("Loading points...")
        pdb_df = pdbm.read_pdb(fname)
        print("Points loaded.")
        rounded = pdbm.round_df(pdb_df)
        print("Data rounded.")
        rounded = rounded.drop_duplicates(subset=['X', 'Y', 'Z'], keep='first')
        print("Duplicates dropped.")

        # Limit the number of points
        if len(rounded) > 10000:  # Adjust this value as needed
            print("Limiting points...")
            rounded = rounded.sample(10000)  # Adjust this value as needed
            print("Points limited.")

        print("Constructing surface array...")
        tmp_points = pdbm.construct_surface_array(rounded)
        print("Surface array constructed.")
        # Downsample the points array
        print("Downsampling points array...")
        self.points = tmp_points[::2, ::2, ::2]
        print(f"Points array shape: {self.points.shape}, dtype: {self.points.dtype}")
        self.update()
        print("Points loaded successfully.")

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.points is not None:
            glPushMatrix()
            glRotatef(self.rotX, 1.0, 0.0, 0.0)
            glRotatef(self.rotY, 0.0, 1.0, 0.0)

            glColor3f(1.0, 1.0, 1.0)
            glBegin(GL_POINTS)
            for point in np.nditer(self.points):
                glVertex3fv(point)
            glEnd()
            glPopMatrix()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60.0, w/h, 0.01, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        if event.buttons() & Qt.MouseButton.LeftButton:
            self.rotX += dy
            self.rotY += dx
        elif event.buttons() & Qt.MouseButton.RightButton:
            self.rotX += dy
            self.rotY += dx

        self.lastPos = event.pos()
        self.update()

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())