# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'wait_screen.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from sgtk.platform.qt import QtCore
for name, cls in QtCore.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls

from sgtk.platform.qt import QtGui
for name, cls in QtGui.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls


from  . import resources_rc

class Ui_WaitScreen(object):
    def setupUi(self, WaitScreen):
        if not WaitScreen.objectName():
            WaitScreen.setObjectName(u"WaitScreen")
        WaitScreen.resize(295, 81)
        WaitScreen.setStyleSheet(u"QDialog {\n"
"	border: 1px solid rgb(39, 167, 223);\n"
"}")
        self.horizontalLayout = QHBoxLayout(WaitScreen)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(20, 5, -1, 5)
        self.icon = QLabel(WaitScreen)
        self.icon.setObjectName(u"icon")
        self.icon.setMinimumSize(QSize(62, 62))
        self.icon.setMaximumSize(QSize(62, 62))
        self.icon.setPixmap(QPixmap(u":/tk-desktop/wait_screen_icon.png"))

        self.horizontalLayout.addWidget(self.icon)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 0, -1, 0)
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.header = QLabel(WaitScreen)
        self.header.setObjectName(u"header")
        self.header.setStyleSheet(u"color: rgb(39, 167, 223);")

        self.verticalLayout.addWidget(self.header)

        self.subheader = QLabel(WaitScreen)
        self.subheader.setObjectName(u"subheader")
        self.subheader.setStyleSheet(u"border: none;\n"
"background-color: transparent;")

        self.verticalLayout.addWidget(self.subheader)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(WaitScreen)

        QMetaObject.connectSlotsByName(WaitScreen)
    # setupUi

    def retranslateUi(self, WaitScreen):
        WaitScreen.setWindowTitle(QCoreApplication.translate("WaitScreen", u"Working on it", None))
        self.icon.setText("")
        self.header.setText(QCoreApplication.translate("WaitScreen", u"Header", None))
        self.subheader.setText(QCoreApplication.translate("WaitScreen", u"subheader", None))
    # retranslateUi
