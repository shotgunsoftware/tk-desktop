# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'loading_project_widget.ui'
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


from ..qtwidgets import ShotgunSpinningWidget

class Ui_LoadingProjectWidget(object):
    def setupUi(self, LoadingProjectWidget):
        if not LoadingProjectWidget.objectName():
            LoadingProjectWidget.setObjectName(u"LoadingProjectWidget")
        LoadingProjectWidget.resize(736, 755)
        self.verticalLayout = QVBoxLayout(LoadingProjectWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 12)
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.shotgun_spinning_widget = ShotgunSpinningWidget(LoadingProjectWidget)
        self.shotgun_spinning_widget.setObjectName(u"shotgun_spinning_widget")
        self.shotgun_spinning_widget.setMinimumSize(QSize(0, 90))
        self.shotgun_spinning_widget.setMaximumSize(QSize(16777215, 80))

        self.verticalLayout.addWidget(self.shotgun_spinning_widget)

        self.bottom = QWidget(LoadingProjectWidget)
        self.bottom.setObjectName(u"bottom")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bottom.sizePolicy().hasHeightForWidth())
        self.bottom.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QVBoxLayout(self.bottom)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.widget = QWidget(self.bottom)
        self.widget.setObjectName(u"widget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy1)
        self.verticalLayout_3 = QVBoxLayout(self.widget)
        self.verticalLayout_3.setSpacing(5)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.progress_output = QPlainTextEdit(self.widget)
        self.progress_output.setObjectName(u"progress_output")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.progress_output.sizePolicy().hasHeightForWidth())
        self.progress_output.setSizePolicy(sizePolicy2)
        self.progress_output.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.progress_output)

        self.verticalLayout_2.addWidget(self.widget)

        self.horizontalLayout = QHBoxLayout()
#ifndef Q_OS_MAC
        self.horizontalLayout.setSpacing(-1)
#endif
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.show_hide_details = QPushButton(self.bottom)
        self.show_hide_details.setObjectName(u"show_hide_details")
        sizePolicy3 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.show_hide_details.sizePolicy().hasHeightForWidth())
        self.show_hide_details.setSizePolicy(sizePolicy3)
        self.show_hide_details.setFlat(True)

        self.horizontalLayout.addWidget(self.show_hide_details)

        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.verticalLayout.addWidget(self.bottom)

        self.retranslateUi(LoadingProjectWidget)

        QMetaObject.connectSlotsByName(LoadingProjectWidget)
    # setupUi

    def retranslateUi(self, LoadingProjectWidget):
        LoadingProjectWidget.setWindowTitle(QCoreApplication.translate("LoadingProjectWidget", u"Form", None))
        self.show_hide_details.setText(QCoreApplication.translate("LoadingProjectWidget", u"show details", None))
    # retranslateUi
