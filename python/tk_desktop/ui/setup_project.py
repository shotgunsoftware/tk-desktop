# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'setup_project.ui'
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

class Ui_SetupProject(object):
    def setupUi(self, SetupProject):
        if not SetupProject.objectName():
            SetupProject.setObjectName(u"SetupProject")
        SetupProject.resize(417, 644)
        self.horizontalLayout = QHBoxLayout(SetupProject)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(20)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.icon = QLabel(SetupProject)
        self.icon.setObjectName(u"icon")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.icon.sizePolicy().hasHeightForWidth())
        self.icon.setSizePolicy(sizePolicy)
        self.icon.setMaximumSize(QSize(40, 40))
        self.icon.setPixmap(QPixmap(u":/tk-desktop/shotgun_logo.png"))
        self.icon.setScaledContents(True)
        self.icon.setAlignment(Qt.AlignCenter)
        self.icon.setTextInteractionFlags(Qt.NoTextInteraction)

        self.horizontalLayout_2.addWidget(self.icon)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.text = QLabel(SetupProject)
        self.text.setObjectName(u"text")
        self.text.setStyleSheet(u"font-size: 26px;")

        self.verticalLayout.addWidget(self.text)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.button = QPushButton(SetupProject)
        self.button.setObjectName(u"button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.button.sizePolicy().hasHeightForWidth())
        self.button.setSizePolicy(sizePolicy1)
        self.button.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(81, 153, 255);\n"
"}\n"
"\n"
"QPushButton::disabled {\n"
"	background-color: rgb(172, 176, 211);\n"
"}")
        self.button.setFlat(False)

        self.horizontalLayout_3.addWidget(self.button)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_4)

        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.retranslateUi(SetupProject)

        QMetaObject.connectSlotsByName(SetupProject)
    # setupUi

    def retranslateUi(self, SetupProject):
        SetupProject.setWindowTitle(QCoreApplication.translate("SetupProject", u"Form", None))
        self.icon.setText("")
        self.text.setText(QCoreApplication.translate("SetupProject", u"Set Up Toolkit Project", None))
        self.button.setText(QCoreApplication.translate("SetupProject", u"Set up Project", None))
    # retranslateUi
