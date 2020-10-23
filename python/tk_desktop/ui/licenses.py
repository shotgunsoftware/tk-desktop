# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'licenses.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_Licenses(object):
    def setupUi(self, Licenses):
        Licenses.setObjectName("Licenses")
        Licenses.resize(500, 400)
        Licenses.setMinimumSize(QtCore.QSize(500, 400))
        self.verticalLayout_2 = QtGui.QVBoxLayout(Licenses)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.licenseText = QtGui.QTextBrowser(Licenses)
        self.licenseText.setOpenExternalLinks(True)
        self.licenseText.setObjectName("licenseText")
        self.verticalLayout_2.addWidget(self.licenseText)
        self.buttonBox = QtGui.QDialogButtonBox(Licenses)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(Licenses)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Licenses.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Licenses.reject)
        QtCore.QMetaObject.connectSlotsByName(Licenses)

    def retranslateUi(self, Licenses):
        Licenses.setWindowTitle(QtGui.QApplication.translate("Licenses", "Licenses", None, QtGui.QApplication.UnicodeUTF8))

