# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'error_dialog.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_ErrorDialog(object):
    def setupUi(self, ErrorDialog):
        ErrorDialog.setObjectName("ErrorDialog")
        ErrorDialog.resize(572, 443)
        ErrorDialog.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(ErrorDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(20)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.icon = QtGui.QLabel(ErrorDialog)
        self.icon.setObjectName("icon")
        self.horizontalLayout.addWidget(self.icon)
        self.title = QtGui.QLabel(ErrorDialog)
        self.title.setStyleSheet("font-size: 20px;")
        self.title.setWordWrap(True)
        self.title.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.title.setObjectName("title")
        self.horizontalLayout.addWidget(self.title)
        self.horizontalLayout.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.message = QtGui.QTextEdit(ErrorDialog)
        self.message.setUndoRedoEnabled(False)
        self.message.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.message.setReadOnly(True)
        self.message.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.message.setObjectName("message")
        self.verticalLayout.addWidget(self.message)
        self.buttonBox = QtGui.QDialogButtonBox(ErrorDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ErrorDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), ErrorDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), ErrorDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ErrorDialog)

    def retranslateUi(self, ErrorDialog):
        ErrorDialog.setWindowTitle(QtGui.QApplication.translate("ErrorDialog", "Toolkit Error", None, QtGui.QApplication.UnicodeUTF8))
        self.icon.setText(QtGui.QApplication.translate("ErrorDialog", "Error Icon", None, QtGui.QApplication.UnicodeUTF8))
        self.title.setText(QtGui.QApplication.translate("ErrorDialog", "Title", None, QtGui.QApplication.UnicodeUTF8))

