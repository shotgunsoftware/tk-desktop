# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'setup_new_os.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_SetupNewOS(object):
    def setupUi(self, SetupNewOS):
        SetupNewOS.setObjectName("SetupNewOS")
        SetupNewOS.resize(304, 550)
        self.horizontalLayout = QtGui.QHBoxLayout(SetupNewOS)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSpacing(20)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.icon = QtGui.QLabel(SetupNewOS)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.icon.sizePolicy().hasHeightForWidth())
        self.icon.setSizePolicy(sizePolicy)
        self.icon.setMaximumSize(QtCore.QSize(40, 40))
        self.icon.setText("")
        self.icon.setPixmap(QtGui.QPixmap(":/tk-desktop/shotgun_logo.png"))
        self.icon.setScaledContents(True)
        self.icon.setAlignment(QtCore.Qt.AlignCenter)
        self.icon.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.icon.setObjectName("icon")
        self.horizontalLayout_2.addWidget(self.icon)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.text = QtGui.QLabel(SetupNewOS)
        self.text.setStyleSheet("font-size: 26px;")
        self.text.setAlignment(QtCore.Qt.AlignCenter)
        self.text.setWordWrap(True)
        self.text.setObjectName("text")
        self.verticalLayout.addWidget(self.text)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.button = QtGui.QPushButton(SetupNewOS)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button.sizePolicy().hasHeightForWidth())
        self.button.setSizePolicy(sizePolicy)
        self.button.setStyleSheet("QPushButton {\n"
"    background-color: rgb(81, 153, 255);\n"
"}\n"
"\n"
"QPushButton::disabled {\n"
"    background-color: rgb(172, 176, 211);\n"
"}")
        self.button.setFlat(False)
        self.button.setObjectName("button")
        self.horizontalLayout_3.addWidget(self.button)
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem3)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.label = QtGui.QLabel(SetupNewOS)
        self.label.setStyleSheet("font-size: 14px;")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        spacerItem4 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem4)
        self.horizontalLayout.addLayout(self.verticalLayout)
        spacerItem5 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem5)

        self.retranslateUi(SetupNewOS)
        QtCore.QMetaObject.connectSlotsByName(SetupNewOS)

    def retranslateUi(self, SetupNewOS):
        SetupNewOS.setWindowTitle(QtGui.QApplication.translate("SetupNewOS", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.text.setText(QtGui.QApplication.translate("SetupNewOS", "Python not found", None, QtGui.QApplication.UnicodeUTF8))
        self.button.setText(QtGui.QApplication.translate("SetupNewOS", "Learn More", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("SetupNewOS", "You need to configure the location of Python for this project and operating system.\n"
"\n"
"Click to view the docs on how to update your configuration.", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
