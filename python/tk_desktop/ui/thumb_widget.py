# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'thumb_widget.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_ThumbWidget(object):
    def setupUi(self, ThumbWidget):
        ThumbWidget.setObjectName("ThumbWidget")
        ThumbWidget.resize(120, 130)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ThumbWidget.sizePolicy().hasHeightForWidth())
        ThumbWidget.setSizePolicy(sizePolicy)
        ThumbWidget.setMaximumSize(QtCore.QSize(120, 130))
        self.verticalLayout_2 = QtGui.QVBoxLayout(ThumbWidget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.widget_frame = QtGui.QFrame(ThumbWidget)
        self.widget_frame.setMouseTracking(True)
        self.widget_frame.setFrameShape(QtGui.QFrame.NoFrame)
        self.widget_frame.setFrameShadow(QtGui.QFrame.Plain)
        self.widget_frame.setLineWidth(0)
        self.widget_frame.setObjectName("widget_frame")
        self.verticalLayout = QtGui.QVBoxLayout(self.widget_frame)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.thumbnail = QtGui.QLabel(self.widget_frame)
        self.thumbnail.setMouseTracking(True)
        self.thumbnail.setText("")
        self.thumbnail.setPixmap(QtGui.QPixmap(":/tk-desktop/loading_512x400.png"))
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnail.setObjectName("thumbnail")
        self.verticalLayout.addWidget(self.thumbnail)
        self.label = QtGui.QLabel(self.widget_frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMaximumSize(QtCore.QSize(16777215, 30))
        font = QtGui.QFont()
        font.setFamily("Helvetica")
        font.setPointSize(14)
        font.setWeight(50)
        font.setBold(False)
        self.label.setFont(font)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.verticalLayout_2.addWidget(self.widget_frame)

        self.retranslateUi(ThumbWidget)
        QtCore.QMetaObject.connectSlotsByName(ThumbWidget)

    def retranslateUi(self, ThumbWidget):
        ThumbWidget.setWindowTitle(QtGui.QApplication.translate("ThumbWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        ThumbWidget.setProperty("label", QtGui.QApplication.translate("ThumbWidget", "project_thumbnail", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ThumbWidget", "This is a two line\n"
"text label\n"
"with overflow.", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
