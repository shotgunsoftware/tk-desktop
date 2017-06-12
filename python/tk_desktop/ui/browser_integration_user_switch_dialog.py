# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'browser_integration_user_switch_dialog.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_BrowserIntegrationUserSwitchDialog(object):
    def setupUi(self, BrowserIntegrationUserSwitchDialog):
        BrowserIntegrationUserSwitchDialog.setObjectName("BrowserIntegrationUserSwitchDialog")
        BrowserIntegrationUserSwitchDialog.resize(430, 141)
        self.verticalLayout = QtGui.QVBoxLayout(BrowserIntegrationUserSwitchDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.reason_label = QtGui.QLabel(BrowserIntegrationUserSwitchDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.reason_label.sizePolicy().hasHeightForWidth())
        self.reason_label.setSizePolicy(sizePolicy)
        self.reason_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.reason_label.setWordWrap(True)
        self.reason_label.setObjectName("reason_label")
        self.verticalLayout.addWidget(self.reason_label)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.ignore_checkbox = QtGui.QCheckBox(BrowserIntegrationUserSwitchDialog)
        self.ignore_checkbox.setObjectName("ignore_checkbox")
        self.horizontalLayout_2.addWidget(self.ignore_checkbox)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.restart_button = QtGui.QPushButton(BrowserIntegrationUserSwitchDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.restart_button.sizePolicy().hasHeightForWidth())
        self.restart_button.setSizePolicy(sizePolicy)
        self.restart_button.setObjectName("restart_button")
        self.horizontalLayout.addWidget(self.restart_button)
        self.ignore_button = QtGui.QPushButton(BrowserIntegrationUserSwitchDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ignore_button.sizePolicy().hasHeightForWidth())
        self.ignore_button.setSizePolicy(sizePolicy)
        self.ignore_button.setDefault(True)
        self.ignore_button.setObjectName("ignore_button")
        self.horizontalLayout.addWidget(self.ignore_button)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.label_2 = QtGui.QLabel(BrowserIntegrationUserSwitchDialog)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setOpenExternalLinks(True)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)

        self.retranslateUi(BrowserIntegrationUserSwitchDialog)
        QtCore.QMetaObject.connectSlotsByName(BrowserIntegrationUserSwitchDialog)

    def retranslateUi(self, BrowserIntegrationUserSwitchDialog):
        BrowserIntegrationUserSwitchDialog.setWindowTitle(QtGui.QApplication.translate("BrowserIntegrationUserSwitchDialog", "Shotgun browser integration", None, QtGui.QApplication.UnicodeUTF8))
        self.reason_label.setText(QtGui.QApplication.translate("BrowserIntegrationUserSwitchDialog", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.ignore_checkbox.setText(QtGui.QApplication.translate("BrowserIntegrationUserSwitchDialog", "Ignore requests from this site until the next restart", None, QtGui.QApplication.UnicodeUTF8))
        self.restart_button.setText(QtGui.QApplication.translate("BrowserIntegrationUserSwitchDialog", "Restart", None, QtGui.QApplication.UnicodeUTF8))
        self.ignore_button.setText(QtGui.QApplication.translate("BrowserIntegrationUserSwitchDialog", "Ignore", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("BrowserIntegrationUserSwitchDialog", "<a href=\"https://support.shotgunsoftware.com/hc/en-us/articles/115000068574#Authentication%20and%20browser%20integration\">Why is a restart required?</a>", None, QtGui.QApplication.UnicodeUTF8))

