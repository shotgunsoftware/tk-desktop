# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'browser_integration_user_switch_dialog.ui'
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


class Ui_BrowserIntegrationUserSwitchDialog(object):
    def setupUi(self, BrowserIntegrationUserSwitchDialog):
        if not BrowserIntegrationUserSwitchDialog.objectName():
            BrowserIntegrationUserSwitchDialog.setObjectName(u"BrowserIntegrationUserSwitchDialog")
        BrowserIntegrationUserSwitchDialog.resize(430, 141)
        self.verticalLayout = QVBoxLayout(BrowserIntegrationUserSwitchDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.reason_label = QLabel(BrowserIntegrationUserSwitchDialog)
        self.reason_label.setObjectName(u"reason_label")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.reason_label.sizePolicy().hasHeightForWidth())
        self.reason_label.setSizePolicy(sizePolicy)
        self.reason_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.reason_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.reason_label)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.ignore_checkbox = QCheckBox(BrowserIntegrationUserSwitchDialog)
        self.ignore_checkbox.setObjectName(u"ignore_checkbox")

        self.horizontalLayout_2.addWidget(self.ignore_checkbox)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.restart_button = QPushButton(BrowserIntegrationUserSwitchDialog)
        self.restart_button.setObjectName(u"restart_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.restart_button.sizePolicy().hasHeightForWidth())
        self.restart_button.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.restart_button)

        self.ignore_button = QPushButton(BrowserIntegrationUserSwitchDialog)
        self.ignore_button.setObjectName(u"ignore_button")
        sizePolicy1.setHeightForWidth(self.ignore_button.sizePolicy().hasHeightForWidth())
        self.ignore_button.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.ignore_button)

        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.label_2 = QLabel(BrowserIntegrationUserSwitchDialog)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignCenter)
        self.label_2.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.label_2)

        self.retranslateUi(BrowserIntegrationUserSwitchDialog)

        self.ignore_button.setDefault(True)

        QMetaObject.connectSlotsByName(BrowserIntegrationUserSwitchDialog)
    # setupUi

    def retranslateUi(self, BrowserIntegrationUserSwitchDialog):
        BrowserIntegrationUserSwitchDialog.setWindowTitle(QCoreApplication.translate("BrowserIntegrationUserSwitchDialog", u"Flow Production Tracking browser integration", None))
        self.reason_label.setText(QCoreApplication.translate("BrowserIntegrationUserSwitchDialog", u"TextLabel", None))
        self.ignore_checkbox.setText(QCoreApplication.translate("BrowserIntegrationUserSwitchDialog", u"Ignore requests from this site until the next restart", None))
        self.restart_button.setText(QCoreApplication.translate("BrowserIntegrationUserSwitchDialog", u"Restart", None))
        self.ignore_button.setText(QCoreApplication.translate("BrowserIntegrationUserSwitchDialog", u"Ignore", None))
        self.label_2.setText(QCoreApplication.translate("BrowserIntegrationUserSwitchDialog", u"<a href=\"https://help.autodesk.com/view/SGSUB/ENU/?guid=SG_Supervisor_Artist_sa_integrations_sa_integrations_user_guide_html#Authentication%20and%20browser%20integration\">Why is a restart required?</a>", None))
    # retranslateUi
