# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wait_screen.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_WaitScreen(object):
    def setupUi(self, WaitScreen):
        WaitScreen.setObjectName("WaitScreen")
        WaitScreen.resize(295, 81)
        WaitScreen.setStyleSheet("QDialog {\n"
"    border: 1px solid rgb(39, 167, 223);\n"
"}")
        self.horizontalLayout = QtGui.QHBoxLayout(WaitScreen)
        self.horizontalLayout.setContentsMargins(20, 5, -1, 5)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.icon = QtGui.QLabel(WaitScreen)
        self.icon.setMinimumSize(QtCore.QSize(62, 62))
        self.icon.setMaximumSize(QtCore.QSize(62, 62))
        self.icon.setText("")
        self.icon.setPixmap(QtGui.QPixmap(":/tk-desktop/wait_screen_icon.png"))
        self.icon.setObjectName("icon")
        self.horizontalLayout.addWidget(self.icon)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setContentsMargins(-1, 0, -1, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.header = QtGui.QLabel(WaitScreen)
        self.header.setStyleSheet("color: rgb(39, 167, 223);")
        self.header.setObjectName("header")
        self.verticalLayout.addWidget(self.header)
        self.subheader = QtGui.QLabel(WaitScreen)
        self.subheader.setStyleSheet("border: none;\n"
"background-color: transparent;")
        self.subheader.setObjectName("subheader")
        self.verticalLayout.addWidget(self.subheader)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(WaitScreen)
        QtCore.QMetaObject.connectSlotsByName(WaitScreen)

    def retranslateUi(self, WaitScreen):
        WaitScreen.setWindowTitle(QtGui.QApplication.translate("WaitScreen", "Working on it", None, QtGui.QApplication.UnicodeUTF8))
        self.header.setText(QtGui.QApplication.translate("WaitScreen", "Header", None, QtGui.QApplication.UnicodeUTF8))
        self.subheader.setText(QtGui.QApplication.translate("WaitScreen", "subheader", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
