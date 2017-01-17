# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'loading_project_widget.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_LoadingProjectWidget(object):
    def setupUi(self, LoadingProjectWidget):
        LoadingProjectWidget.setObjectName("LoadingProjectWidget")
        LoadingProjectWidget.resize(686, 683)
        self.verticalLayout = QtGui.QVBoxLayout(LoadingProjectWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.shotgun_overlay_widget = ShotgunOverlayWidget(LoadingProjectWidget)
        self.shotgun_overlay_widget.setMinimumSize(QtCore.QSize(0, 90))
        self.shotgun_overlay_widget.setMaximumSize(QtCore.QSize(16777215, 80))
        self.shotgun_overlay_widget.setObjectName("shotgun_overlay_widget")
        self.verticalLayout.addWidget(self.shotgun_overlay_widget)
        self.bottom = QtGui.QWidget(LoadingProjectWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bottom.sizePolicy().hasHeightForWidth())
        self.bottom.setSizePolicy(sizePolicy)
        self.bottom.setObjectName("bottom")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.bottom)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.progress = QtGui.QPlainTextEdit(self.bottom)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progress.sizePolicy().hasHeightForWidth())
        self.progress.setSizePolicy(sizePolicy)
        self.progress.setObjectName("progress")
        self.verticalLayout_2.addWidget(self.progress)
        self.more_less_btn = QtGui.QPushButton(self.bottom)
        self.more_less_btn.setFlat(True)
        self.more_less_btn.setObjectName("more_less_btn")
        self.verticalLayout_2.addWidget(self.more_less_btn)
        self.verticalLayout.addWidget(self.bottom)

        self.retranslateUi(LoadingProjectWidget)
        QtCore.QMetaObject.connectSlotsByName(LoadingProjectWidget)

    def retranslateUi(self, LoadingProjectWidget):
        LoadingProjectWidget.setWindowTitle(QtGui.QApplication.translate("LoadingProjectWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.more_less_btn.setText(QtGui.QApplication.translate("LoadingProjectWidget", "more details...", None, QtGui.QApplication.UnicodeUTF8))

from ..qtwidgets import ShotgunOverlayWidget
