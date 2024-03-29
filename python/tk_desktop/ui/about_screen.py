# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'about_screen.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_AboutScreen(object):
    def setupUi(self, AboutScreen):
        AboutScreen.setObjectName("AboutScreen")
        AboutScreen.resize(325, 385)
        AboutScreen.setMinimumSize(QtCore.QSize(320, 327))
        self.verticalLayout = QtGui.QVBoxLayout(AboutScreen)
        self.verticalLayout.setSpacing(15)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.icon = QtGui.QLabel(AboutScreen)
        self.icon.setMinimumSize(QtCore.QSize(100, 100))
        self.icon.setMaximumSize(QtCore.QSize(100, 100))
        self.icon.setText("")
        self.icon.setPixmap(QtGui.QPixmap(":/tk-desktop/shotgun_logo.png"))
        self.icon.setScaledContents(True)
        self.icon.setObjectName("icon")
        self.horizontalLayout.addWidget(self.icon)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.header = QtGui.QLabel(AboutScreen)
        self.header.setStyleSheet("font-size: 16px;")
        self.header.setAlignment(QtCore.Qt.AlignCenter)
        self.header.setWordWrap(True)
        self.header.setObjectName("header")
        self.verticalLayout.addWidget(self.header)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.body = QtGui.QLabel(AboutScreen)
        self.body.setAlignment(QtCore.Qt.AlignCenter)
        self.body.setWordWrap(True)
        self.body.setObjectName("body")
        self.verticalLayout.addWidget(self.body)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.copyright = QtGui.QLabel(AboutScreen)
        self.copyright.setStyleSheet("font-size: 10px;")
        self.copyright.setAlignment(QtCore.Qt.AlignCenter)
        self.copyright.setWordWrap(True)
        self.copyright.setObjectName("copyright")
        self.verticalLayout.addWidget(self.copyright)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.buttonBox = QtGui.QDialogButtonBox(AboutScreen)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout_2.addWidget(self.buttonBox)
        self.licensesButton = QtGui.QPushButton(AboutScreen)
        self.licensesButton.setObjectName("licensesButton")
        self.horizontalLayout_2.addWidget(self.licensesButton)
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(AboutScreen)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), AboutScreen.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), AboutScreen.reject)
        QtCore.QMetaObject.connectSlotsByName(AboutScreen)

    def retranslateUi(self, AboutScreen):
        AboutScreen.setWindowTitle(QtGui.QApplication.translate("AboutScreen", "About Flow Production Tracking", None, QtGui.QApplication.UnicodeUTF8))
        self.header.setText(QtGui.QApplication.translate("AboutScreen", "<b><big>Flow Production Tracking</big></b>", None, QtGui.QApplication.UnicodeUTF8))
        self.body.setText(QtGui.QApplication.translate("AboutScreen", "Body", None, QtGui.QApplication.UnicodeUTF8))
        self.copyright.setText(QtGui.QApplication.translate("AboutScreen", "Copyright ©2024 Autodesk, Inc. All rights reserved.", None, QtGui.QApplication.UnicodeUTF8))
        self.licensesButton.setText(QtGui.QApplication.translate("AboutScreen", "Licenses...", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
