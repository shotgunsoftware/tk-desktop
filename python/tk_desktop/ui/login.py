# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'login.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_LoginDialog(object):
    def setupUi(self, LoginDialog):
        LoginDialog.setObjectName("LoginDialog")
        LoginDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        LoginDialog.resize(437, 387)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/sg_badge"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        LoginDialog.setWindowIcon(icon)
        LoginDialog.setStyleSheet("QWidget\n"
"{\n"
"    background-color:  rgb(43, 46, 48);\n"
"    color: rgb(185, 185, 185);\n"
"    border-radius: 2px;\n"
"    selection-background-color: rgb(167, 167, 167);\n"
"    selection-color: rgb(26, 26, 26);\n"
"    font-size: 11px;\n"
"}\n"
"\n"
"QPushButton\n"
"{\n"
"    background-color: rgb(83, 83, 83);\n"
"    border: none;\n"
"    padding: 5px;\n"
"    padding-left: 35px;\n"
"    padding-right: 35px;\n"
"}\n"
"\n"
"QPushButton:focus\n"
"{\n"
"    border: 1px solid rgb(185, 185, 185);\n"
"}\n"
"\n"
"QLineEdit\n"
"{\n"
"    border: 1px solid rgb(180, 180, 180);\n"
"    padding: 5px;\n"
"}")
        LoginDialog.setModal(True)
        self.verticalLayout_2 = QtGui.QVBoxLayout(LoginDialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.logo = QtGui.QLabel(LoginDialog)
        self.logo.setMaximumSize(QtCore.QSize(250, 32))
        self.logo.setText("")
        self.logo.setPixmap(QtGui.QPixmap(":/res/shotgun_logo_light_medium.png"))
        self.logo.setScaledContents(True)
        self.logo.setAlignment(QtCore.Qt.AlignCenter)
        self.logo.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.logo.setObjectName("logo")
        self.horizontalLayout.addWidget(self.logo)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        spacerItem1 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.verticalLayout_2.addItem(spacerItem1)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSpacing(15)
        self.verticalLayout.setObjectName("verticalLayout")
        self.site = QtGui.QLineEdit(LoginDialog)
        self.site.setMinimumSize(QtCore.QSize(308, 0))
        self.site.setObjectName("site")
        self.verticalLayout.addWidget(self.site)
        self.login = QtGui.QLineEdit(LoginDialog)
        self.login.setMinimumSize(QtCore.QSize(308, 0))
        self.login.setObjectName("login")
        self.verticalLayout.addWidget(self.login)
        self.password = QtGui.QLineEdit(LoginDialog)
        self.password.setMinimumSize(QtCore.QSize(308, 0))
        self.password.setEchoMode(QtGui.QLineEdit.Password)
        self.password.setObjectName("password")
        self.verticalLayout.addWidget(self.password)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.sign_in = QtGui.QPushButton(LoginDialog)
        self.sign_in.setStyleSheet("")
        self.sign_in.setAutoDefault(False)
        self.sign_in.setDefault(True)
        self.sign_in.setFlat(True)
        self.sign_in.setObjectName("sign_in")
        self.horizontalLayout_2.addWidget(self.sign_in)
        self.cancel = QtGui.QPushButton(LoginDialog)
        self.cancel.setStyleSheet("")
        self.cancel.setAutoDefault(False)
        self.cancel.setFlat(True)
        self.cancel.setObjectName("cancel")
        self.horizontalLayout_2.addWidget(self.cancel)
        spacerItem4 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3.addLayout(self.verticalLayout)
        spacerItem5 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem5)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        spacerItem6 = QtGui.QSpacerItem(20, 70, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem6)
        self.message = QtGui.QLabel(LoginDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.message.sizePolicy().hasHeightForWidth())
        self.message.setSizePolicy(sizePolicy)
        self.message.setText("")
        self.message.setAlignment(QtCore.Qt.AlignCenter)
        self.message.setObjectName("message")
        self.verticalLayout_2.addWidget(self.message)

        self.retranslateUi(LoginDialog)
        QtCore.QMetaObject.connectSlotsByName(LoginDialog)

    def retranslateUi(self, LoginDialog):
        LoginDialog.setWindowTitle(QtGui.QApplication.translate("LoginDialog", "Shotgun Login", None, QtGui.QApplication.UnicodeUTF8))
        self.site.setPlaceholderText(QtGui.QApplication.translate("LoginDialog", "example.shotgunstudio.com", None, QtGui.QApplication.UnicodeUTF8))
        self.login.setPlaceholderText(QtGui.QApplication.translate("LoginDialog", "login", None, QtGui.QApplication.UnicodeUTF8))
        self.password.setPlaceholderText(QtGui.QApplication.translate("LoginDialog", "password", None, QtGui.QApplication.UnicodeUTF8))
        self.sign_in.setText(QtGui.QApplication.translate("LoginDialog", "Sign In", None, QtGui.QApplication.UnicodeUTF8))
        self.cancel.setText(QtGui.QApplication.translate("LoginDialog", "Cancel", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
