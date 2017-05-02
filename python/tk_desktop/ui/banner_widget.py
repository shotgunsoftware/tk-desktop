# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'banner_widget.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_BannerWidget(object):
    def setupUi(self, BannerWidget):
        BannerWidget.setObjectName("BannerWidget")
        BannerWidget.resize(567, 35)
        self.verticalLayout = QtGui.QVBoxLayout(BannerWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(6, -1, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.message = QtGui.QLabel(BannerWidget)
        self.message.setWordWrap(True)
        self.message.setOpenExternalLinks(False)
        self.message.setObjectName("message")
        self.horizontalLayout.addWidget(self.message)
        self.close_button = QtGui.QToolButton(BannerWidget)
        self.close_button.setStyleSheet("border: none;")
        self.close_button.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/tk-desktop/cross.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.close_button.setIcon(icon)
        self.close_button.setIconSize(QtCore.QSize(30, 30))
        self.close_button.setObjectName("close_button")
        self.horizontalLayout.addWidget(self.close_button)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.line = QtGui.QFrame(BannerWidget)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)

        self.retranslateUi(BannerWidget)
        QtCore.QMetaObject.connectSlotsByName(BannerWidget)

    def retranslateUi(self, BannerWidget):
        BannerWidget.setWindowTitle(QtGui.QApplication.translate("BannerWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.message.setText(QtGui.QApplication.translate("BannerWidget", "Welcome to the Shotgun Desktop. Please <u>click here</u> to learn more about this app!", None, QtGui.QApplication.UnicodeUTF8))
        self.close_button.setToolTip(QtGui.QApplication.translate("BannerWidget", "Close", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
