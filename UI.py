from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QApplication, QListWidget, QPushButton, QMainWindow, QMessageBox, QLabel, QVBoxLayout, QWidget, QStylePainter
from PyQt6.QtGui import QMovie, QPalette, QBrush, QPixmap, QDesktopServices, QIcon
from PyQt6 import QtCore, QtGui, QtWidgets

import skeletonWindow
import xrayWindow
import space_fillingWindow
import ribbonWindow
import amino_acidsWindow
import customWindow
import utilityWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setObjectName("MainWindow")
        self.setWindowTitle("Welcome to PDB2MC")
        self.setFixedSize(929, 621)
        self.setWindowIcon(QIcon('images/icons/logo.png'))
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

        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
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
        self.comboBox.addItem("Utilities")

        labelTitle = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap("images/title.png")
        pixmap = pixmap.scaled(500, 500)
        labelTitle.setScaledContents(True)
        labelTitle.setGeometry(QtCore.QRect(215, 50, 500, 118))

        labelTitle.setPixmap(pixmap)
        labelTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.layout().addWidget(labelTitle)

        self.help = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(25)
        self.help.setFont(font)
        self.help.setObjectName("help")
        self.help.setGeometry(QtCore.QRect(755, 560, 150, 51))

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

        # Connect the currentTextChanged signal to a slot method
        self.comboBox.currentTextChanged.connect(self.handle_dropdown_change)
        self.help.clicked.connect(self.handle_help_button)

    def handle_help_button(self):
        print("Help button clicked")
        QDesktopServices.openUrl(QtCore.QUrl("https://github.com/markus-nevil/mcpdb/blob/main/README.md"))

    def handle_dropdown_change(self, text):
        if text == "Custom":
            self.custom_window = customWindow.CustomWindow()
            self.custom_window.show()
            #Turn off main window
            self.hide()
        if text == "Skeleton":
            self.skeleton_window = skeletonWindow.SkeletonWindow()
            self.skeleton_window.show()
            self.hide()
        if text == "X-Ray":
            self.xray_window = xrayWindow.XrayWindow()
            self.xray_window.show()
            self.hide()
        if text == "Space Filling":
            self.SpaceFilling = space_fillingWindow.spWindow()
            self.SpaceFilling.show()
            self.hide()
        if text == "Ribbon":
            self.ribbon_window = ribbonWindow.RibbonWindow()
            self.ribbon_window.show()
            self.hide()
        if text == "Amino Acids":
            self.amino_acid_window = amino_acidsWindow.AAWindow()
            self.amino_acid_window.show()
            self.hide()
        if text == "Utilities":
            self.utilities_window = utilityWindow.UtilityWindow()
            self.utilities_window.show()
            self.hide()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        #MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.comboBox.setItemText(1, _translate("MainWindow", "Custom"))
        #self.comboBox.setItemText(2, _translate("MainWindow", "X-Ray"))
        self.help.setText(_translate("MainWindow", "Help"))
        self.comboBox.setItemText(4, _translate("MainWindow", "Space Filling"))
        self.comboBox.setItemText(5, _translate("MainWindow", "Ribbon"))
        self.comboBox.setItemText(6, _translate("MainWindow", "Amino Acid"))
        self.label_2.setText(_translate("MainWindow", "Select Mode:"))
        #self.label_3.setText(_translate("MainWindow", "Welcome to PDB2MC"))



if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()