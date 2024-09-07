# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'no_apps_installed_overlay.ui'
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

class Ui_NoAppsInstalledOverlay(object):
    def setupUi(self, NoAppsInstalledOverlay):
        if not NoAppsInstalledOverlay.objectName():
            NoAppsInstalledOverlay.setObjectName(u"NoAppsInstalledOverlay")
        NoAppsInstalledOverlay.resize(425, 540)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(NoAppsInstalledOverlay.sizePolicy().hasHeightForWidth())
        NoAppsInstalledOverlay.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(NoAppsInstalledOverlay)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(20)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.icon_rows = QVBoxLayout()
        self.icon_rows.setObjectName(u"icon_rows")

        self.verticalLayout.addLayout(self.icon_rows)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_3)

        self.main_label = QLabel(NoAppsInstalledOverlay)
        self.main_label.setObjectName(u"main_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.main_label.sizePolicy().hasHeightForWidth())
        self.main_label.setSizePolicy(sizePolicy1)
        self.main_label.setStyleSheet(u"font-size: 20px;")
        self.main_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.main_label)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.sub_label_1 = QLabel(NoAppsInstalledOverlay)
        self.sub_label_1.setObjectName(u"sub_label_1")
        sizePolicy1.setHeightForWidth(self.sub_label_1.sizePolicy().hasHeightForWidth())
        self.sub_label_1.setSizePolicy(sizePolicy1)
        self.sub_label_1.setStyleSheet(u"font-size: 18px; color: #888888")
        self.sub_label_1.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.sub_label_1)

        self.sub_label_2 = QLabel(NoAppsInstalledOverlay)
        self.sub_label_2.setObjectName(u"sub_label_2")
        sizePolicy1.setHeightForWidth(self.sub_label_2.sizePolicy().hasHeightForWidth())
        self.sub_label_2.setSizePolicy(sizePolicy1)
        self.sub_label_2.setStyleSheet(u"font-size: 18px; color: #888888")
        self.sub_label_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.sub_label_2)

        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.verticalSpacer_2 = QSpacerItem(20, 200, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.link_label = QLabel(NoAppsInstalledOverlay)
        self.link_label.setObjectName(u"link_label")
        sizePolicy1.setHeightForWidth(self.link_label.sizePolicy().hasHeightForWidth())
        self.link_label.setSizePolicy(sizePolicy1)
        self.link_label.setStyleSheet(u"color: #888888")
        self.link_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.link_label)

        self.verticalLayout.addLayout(self.verticalLayout_3)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.retranslateUi(NoAppsInstalledOverlay)

        QMetaObject.connectSlotsByName(NoAppsInstalledOverlay)
    # setupUi

    def retranslateUi(self, NoAppsInstalledOverlay):
        NoAppsInstalledOverlay.setWindowTitle(QCoreApplication.translate("NoAppsInstalledOverlay", u"Form", None))
        self.main_label.setText(QCoreApplication.translate("NoAppsInstalledOverlay", u"We couldn't find anything to launch.", None))
        self.sub_label_1.setText(QCoreApplication.translate("NoAppsInstalledOverlay", u"Install a supported", None))
        self.sub_label_2.setText(QCoreApplication.translate("NoAppsInstalledOverlay", u"application to start using it with FPTR.", None))
        self.link_label.setText(QCoreApplication.translate("NoAppsInstalledOverlay", u"Click here to find out how to configure this screen.", None))
    # retranslateUi
