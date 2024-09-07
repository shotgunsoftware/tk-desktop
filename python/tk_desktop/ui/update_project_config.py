# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'update_project_config.ui'
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

class Ui_UpdateProjectConfig(object):
    def setupUi(self, UpdateProjectConfig):
        if not UpdateProjectConfig.objectName():
            UpdateProjectConfig.setObjectName(u"UpdateProjectConfig")
        UpdateProjectConfig.resize(432, 644)
        self.horizontalLayout = QHBoxLayout(UpdateProjectConfig)
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
        self.icon = QLabel(UpdateProjectConfig)
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

        self.text = QLabel(UpdateProjectConfig)
        self.text.setObjectName(u"text")
        self.text.setStyleSheet(u"font-size: 26px;")
        self.text.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.text)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.button = QPushButton(UpdateProjectConfig)
        self.button.setObjectName(u"button")
        self.button.setEnabled(True)
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

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(UpdateProjectConfig)
        self.label.setObjectName(u"label")
        self.label.setStyleSheet(u"font-size: 14px;")
        self.label.setScaledContents(False)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setMargin(0)

        self.verticalLayout_2.addWidget(self.label)

        self.success = QLabel(UpdateProjectConfig)
        self.success.setObjectName(u"success")
        self.success.setStyleSheet(u"font-size: 14px;")
        self.success.setAlignment(Qt.AlignCenter)
        self.success.setWordWrap(True)
        self.success.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.verticalLayout_2.addWidget(self.success)

        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.retranslateUi(UpdateProjectConfig)

        QMetaObject.connectSlotsByName(UpdateProjectConfig)
    # setupUi

    def retranslateUi(self, UpdateProjectConfig):
        UpdateProjectConfig.setWindowTitle(QCoreApplication.translate("UpdateProjectConfig", u"Form", None))
        self.icon.setText("")
        self.text.setText(QCoreApplication.translate("UpdateProjectConfig", u"Add Flow Production Tracking", None))
        self.button.setText(QCoreApplication.translate("UpdateProjectConfig", u"Add", None))
        self.label.setText(QCoreApplication.translate("UpdateProjectConfig", u"Click here to upgrade your\n"
"Pipeline Configuration", None))
        self.success.setText(QCoreApplication.translate("UpdateProjectConfig", u"The project has been set up.", None))
    # retranslateUi
