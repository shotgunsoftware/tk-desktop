# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'preferences.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_Preferences(object):
    def setupUi(self, Preferences):
        Preferences.setObjectName("Preferences")
        Preferences.resize(328, 80)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Preferences.sizePolicy().hasHeightForWidth())
        Preferences.setSizePolicy(sizePolicy)
        Preferences.setMinimumSize(QtCore.QSize(328, 80))
        Preferences.setMaximumSize(QtCore.QSize(328, 80))
        Preferences.setModal(True)
        self.gridLayout = QtGui.QGridLayout(Preferences)
        self.gridLayout.setObjectName("gridLayout")
        self.auto_start_label = QtGui.QLabel(Preferences)
        self.auto_start_label.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.auto_start_label.sizePolicy().hasHeightForWidth())
        self.auto_start_label.setSizePolicy(sizePolicy)
        self.auto_start_label.setMaximumSize(QtCore.QSize(16777215, 18))
        self.auto_start_label.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.auto_start_label.setObjectName("auto_start_label")
        self.gridLayout.addWidget(self.auto_start_label, 0, 1, 1, 3)
        self.auto_start_checkbox = QtGui.QCheckBox(Preferences)
        self.auto_start_checkbox.setEnabled(True)
        self.auto_start_checkbox.setText("")
        self.auto_start_checkbox.setObjectName("auto_start_checkbox")
        self.gridLayout.addWidget(self.auto_start_checkbox, 0, 0, 1, 1)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(3)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.hotkey = HotKeyEditor(Preferences)
        self.hotkey.setText("")
        self.hotkey.setFrame(False)
        self.hotkey.setObjectName("hotkey")
        self.horizontalLayout_3.addWidget(self.hotkey)
        self.hotkey_clear = QtGui.QPushButton(Preferences)
        self.hotkey_clear.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hotkey_clear.sizePolicy().hasHeightForWidth())
        self.hotkey_clear.setSizePolicy(sizePolicy)
        self.hotkey_clear.setMaximumSize(QtCore.QSize(16, 16))
        self.hotkey_clear.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/tk-desktop/x.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.hotkey_clear.setIcon(icon)
        self.hotkey_clear.setIconSize(QtCore.QSize(8, 8))
        self.hotkey_clear.setAutoDefault(False)
        self.hotkey_clear.setObjectName("hotkey_clear")
        self.horizontalLayout_3.addWidget(self.hotkey_clear)
        self.gridLayout.addLayout(self.horizontalLayout_3, 1, 2, 1, 2)
        self.hotkey_label = QtGui.QLabel(Preferences)
        self.hotkey_label.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hotkey_label.sizePolicy().hasHeightForWidth())
        self.hotkey_label.setSizePolicy(sizePolicy)
        self.hotkey_label.setMaximumSize(QtCore.QSize(16777215, 18))
        self.hotkey_label.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.hotkey_label.setObjectName("hotkey_label")
        self.gridLayout.addWidget(self.hotkey_label, 1, 1, 1, 1)
        self.gridLayout.setColumnStretch(3, 1)

        self.retranslateUi(Preferences)
        QtCore.QMetaObject.connectSlotsByName(Preferences)

    def retranslateUi(self, Preferences):
        Preferences.setWindowTitle(QtGui.QApplication.translate("Preferences", "Preferences", None, QtGui.QApplication.UnicodeUTF8))
        self.auto_start_label.setToolTip(QtGui.QApplication.translate("Preferences", "When checked Shotgun Desktop will startup automatically when you log in.", None, QtGui.QApplication.UnicodeUTF8))
        self.auto_start_label.setText(QtGui.QApplication.translate("Preferences", "Start at login", None, QtGui.QApplication.UnicodeUTF8))
        self.auto_start_checkbox.setToolTip(QtGui.QApplication.translate("Preferences", "When checked Shotgun Desktop will startup automatically when you log in.", None, QtGui.QApplication.UnicodeUTF8))
        self.hotkey.setToolTip(QtGui.QApplication.translate("Preferences", "Enter a hotkey that will auto-raise Shotgun Desktop when pressed.", None, QtGui.QApplication.UnicodeUTF8))
        self.hotkey.setPlaceholderText(QtGui.QApplication.translate("Preferences", "Enter hotkey shortcut", None, QtGui.QApplication.UnicodeUTF8))
        self.hotkey_clear.setToolTip(QtGui.QApplication.translate("Preferences", "Click to clear the hotkey.", None, QtGui.QApplication.UnicodeUTF8))
        self.hotkey_label.setToolTip(QtGui.QApplication.translate("Preferences", "Enter a hotkey that will auto-raise Shotgun Desktop when pressed.", None, QtGui.QApplication.UnicodeUTF8))
        self.hotkey_label.setText(QtGui.QApplication.translate("Preferences", "Hotkey to activate", None, QtGui.QApplication.UnicodeUTF8))

from ..hotkey import HotKeyEditor
from . import resources_rc
