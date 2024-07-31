# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'setup_new_os.ui'
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

class Ui_SetupNewOS(object):
    def setupUi(self, SetupNewOS):
        if not SetupNewOS.objectName():
            SetupNewOS.setObjectName(u"SetupNewOS")
        SetupNewOS.resize(304, 550)
        self.horizontalLayout = QHBoxLayout(SetupNewOS)
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
        self.icon = QLabel(SetupNewOS)
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

        self.text = QLabel(SetupNewOS)
        self.text.setObjectName(u"text")
        self.text.setStyleSheet(u"font-size: 26px;")
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setWordWrap(True)

        self.verticalLayout.addWidget(self.text)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.button = QPushButton(SetupNewOS)
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

        self.label = QLabel(SetupNewOS)
        self.label.setObjectName(u"label")
        self.label.setStyleSheet(u"font-size: 14px;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)

        self.verticalLayout.addWidget(self.label)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.retranslateUi(SetupNewOS)

        QMetaObject.connectSlotsByName(SetupNewOS)
    # setupUi

    def retranslateUi(self, SetupNewOS):
        SetupNewOS.setWindowTitle(QCoreApplication.translate("SetupNewOS", u"Form", None))
        self.icon.setText("")
        self.text.setText(QCoreApplication.translate("SetupNewOS", u"Python not found", None))
        self.button.setText(QCoreApplication.translate("SetupNewOS", u"Learn More", None))
        self.label.setText(QCoreApplication.translate("SetupNewOS", u"You need to configure the location of Python for this project and operating system.\n"
"\n"
"Click to view the docs on how to update your configuration.", None))
    # retranslateUi
