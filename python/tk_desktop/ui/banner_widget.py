# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'banner_widget.ui'
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

class Ui_BannerWidget(object):
    def setupUi(self, BannerWidget):
        if not BannerWidget.objectName():
            BannerWidget.setObjectName(u"BannerWidget")
        BannerWidget.resize(618, 71)
        self.horizontalLayout = QHBoxLayout(BannerWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, 0, 0, 0)
        self.message = QLabel(BannerWidget)
        self.message.setObjectName(u"message")
        self.message.setStyleSheet(u"border-style: outset;\n"
"border-color: rgb(0, 0, 0);")
        self.message.setWordWrap(True)
        self.message.setOpenExternalLinks(False)

        self.horizontalLayout.addWidget(self.message)

        self.close_button = QToolButton(BannerWidget)
        self.close_button.setObjectName(u"close_button")
        self.close_button.setStyleSheet(u"border: none;")
        icon = QIcon()
        icon.addFile(u":/tk-desktop/cross.png", QSize(), QIcon.Normal, QIcon.Off)
        self.close_button.setIcon(icon)
        self.close_button.setIconSize(QSize(30, 30))

        self.horizontalLayout.addWidget(self.close_button)

        self.retranslateUi(BannerWidget)

        QMetaObject.connectSlotsByName(BannerWidget)
    # setupUi

    def retranslateUi(self, BannerWidget):
        BannerWidget.setWindowTitle(QCoreApplication.translate("BannerWidget", u"Form", None))
        self.message.setText(QCoreApplication.translate("BannerWidget", u"Welcome to Flow Production Tracking. Please <u>click here</u> to learn more about this app!", None))
#if QT_CONFIG(tooltip)
        self.close_button.setToolTip(QCoreApplication.translate("BannerWidget", u"Close", None))
#endif // QT_CONFIG(tooltip)
        self.close_button.setText("")
    # retranslateUi
