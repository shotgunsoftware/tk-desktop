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
        LoadingProjectWidget.resize(722, 632)
        self.verticalLayout = QtGui.QVBoxLayout(LoadingProjectWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.shotgun_spinning_widget = ShotgunSpinningWidget(LoadingProjectWidget)
        self.shotgun_spinning_widget.setMinimumSize(QtCore.QSize(0, 90))
        self.shotgun_spinning_widget.setMaximumSize(QtCore.QSize(16777215, 80))
        self.shotgun_spinning_widget.setObjectName("shotgun_spinning_widget")
        self.verticalLayout.addWidget(self.shotgun_spinning_widget)
        self.bottom = QtGui.QWidget(LoadingProjectWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bottom.sizePolicy().hasHeightForWidth())
        self.bottom.setSizePolicy(sizePolicy)
        self.bottom.setObjectName("bottom")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.bottom)
        self.verticalLayout_2.setSpacing(-1)
        self.verticalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.widget = QtGui.QWidget(self.bottom)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.widget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.progress_output = QtGui.QPlainTextEdit(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progress_output.sizePolicy().hasHeightForWidth())
        self.progress_output.setSizePolicy(sizePolicy)
        self.progress_output.setObjectName("progress_output")
        self.verticalLayout_3.addWidget(self.progress_output)
        self.verticalLayout_2.addWidget(self.widget)
        self.more_or_less_label = QtGui.QLabel(self.bottom)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.more_or_less_label.sizePolicy().hasHeightForWidth())
        self.more_or_less_label.setSizePolicy(sizePolicy)
        self.more_or_less_label.setTextFormat(QtCore.Qt.AutoText)
        self.more_or_less_label.setAlignment(QtCore.Qt.AlignCenter)
        self.more_or_less_label.setObjectName("more_or_less_label")
        self.verticalLayout_2.addWidget(self.more_or_less_label)
        self.verticalLayout.addWidget(self.bottom)

        self.retranslateUi(LoadingProjectWidget)
        QtCore.QMetaObject.connectSlotsByName(LoadingProjectWidget)

    def retranslateUi(self, LoadingProjectWidget):
        LoadingProjectWidget.setWindowTitle(QtGui.QApplication.translate("LoadingProjectWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.more_or_less_label.setText(QtGui.QApplication.translate("LoadingProjectWidget", "<a href=\"#\">more details...</a>", None, QtGui.QApplication.UnicodeUTF8))

from ..qtwidgets import ShotgunSpinningWidget
