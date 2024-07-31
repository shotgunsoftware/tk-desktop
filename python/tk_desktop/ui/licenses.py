# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'licenses.ui'
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


class Ui_Licenses(object):
    def setupUi(self, Licenses):
        if not Licenses.objectName():
            Licenses.setObjectName(u"Licenses")
        Licenses.resize(500, 400)
        Licenses.setMinimumSize(QSize(500, 400))
        self.verticalLayout_2 = QVBoxLayout(Licenses)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.licenseText = QTextBrowser(Licenses)
        self.licenseText.setObjectName(u"licenseText")
        self.licenseText.setOpenExternalLinks(True)

        self.verticalLayout_2.addWidget(self.licenseText)

        self.buttonBox = QDialogButtonBox(Licenses)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)

        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(Licenses)
        self.buttonBox.accepted.connect(Licenses.accept)
        self.buttonBox.rejected.connect(Licenses.reject)

        QMetaObject.connectSlotsByName(Licenses)
    # setupUi

    def retranslateUi(self, Licenses):
        Licenses.setWindowTitle(QCoreApplication.translate("Licenses", u"Licenses", None))
    # retranslateUi
