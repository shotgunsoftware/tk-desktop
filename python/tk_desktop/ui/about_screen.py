# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about_screen.ui'
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

class Ui_AboutScreen(object):
    def setupUi(self, AboutScreen):
        if not AboutScreen.objectName():
            AboutScreen.setObjectName(u"AboutScreen")
        AboutScreen.resize(325, 385)
        AboutScreen.setMinimumSize(QSize(320, 327))
        self.verticalLayout = QVBoxLayout(AboutScreen)
        self.verticalLayout.setSpacing(15)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.icon = QLabel(AboutScreen)
        self.icon.setObjectName(u"icon")
        self.icon.setMinimumSize(QSize(100, 100))
        self.icon.setMaximumSize(QSize(100, 100))
        self.icon.setPixmap(QPixmap(u":/tk-desktop/shotgun_logo.png"))
        self.icon.setScaledContents(True)

        self.horizontalLayout.addWidget(self.icon)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.header = QLabel(AboutScreen)
        self.header.setObjectName(u"header")
        self.header.setStyleSheet(u"font-size: 16px;")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setWordWrap(True)

        self.verticalLayout.addWidget(self.header)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.body = QLabel(AboutScreen)
        self.body.setObjectName(u"body")
        self.body.setAlignment(Qt.AlignCenter)
        self.body.setWordWrap(True)

        self.verticalLayout.addWidget(self.body)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.copyright = QLabel(AboutScreen)
        self.copyright.setObjectName(u"copyright")
        self.copyright.setStyleSheet(u"font-size: 10px;")
        self.copyright.setAlignment(Qt.AlignCenter)
        self.copyright.setWordWrap(True)

        self.verticalLayout.addWidget(self.copyright)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.buttonBox = QDialogButtonBox(AboutScreen)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)

        self.horizontalLayout_2.addWidget(self.buttonBox)

        self.licensesButton = QPushButton(AboutScreen)
        self.licensesButton.setObjectName(u"licensesButton")

        self.horizontalLayout_2.addWidget(self.licensesButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(AboutScreen)
        self.buttonBox.accepted.connect(AboutScreen.accept)
        self.buttonBox.rejected.connect(AboutScreen.reject)

        QMetaObject.connectSlotsByName(AboutScreen)
    # setupUi

    def retranslateUi(self, AboutScreen):
        AboutScreen.setWindowTitle(QCoreApplication.translate("AboutScreen", u"About Flow Production Tracking", None))
        self.icon.setText("")
        self.header.setText(QCoreApplication.translate("AboutScreen", u"<b><big>Flow Production Tracking</big></b>", None))
        self.body.setText(QCoreApplication.translate("AboutScreen", u"Body", None))
        self.copyright.setText(QCoreApplication.translate("AboutScreen", u"Copyright \u00a92024 Autodesk. All rights reserved.", None))
        self.licensesButton.setText(QCoreApplication.translate("AboutScreen", u"Licenses...", None))
    # retranslateUi
