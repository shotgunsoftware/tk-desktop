# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'thumb_widget.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_ThumbWidget(object):
    def setupUi(self, ThumbWidget):
        ThumbWidget.setObjectName("ThumbWidget")
        ThumbWidget.resize(542, 453)
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
        self.widget_frame_layout = QtGui.QVBoxLayout(self.widget_frame)
        self.widget_frame_layout.setSpacing(10)
        self.widget_frame_layout.setContentsMargins(15, 15, 15, 15)
        self.widget_frame_layout.setObjectName("widget_frame_layout")
        self.thumbnail = QtGui.QLabel(self.widget_frame)
        self.thumbnail.setMouseTracking(True)
        self.thumbnail.setPixmap(QtGui.QPixmap(":/tk-desktop/loading_512x400.png"))
        self.thumbnail.setScaledContents(False)
        self.thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnail.setObjectName("thumbnail")
        self.widget_frame_layout.addWidget(self.thumbnail)
        self.label = QtGui.QLabel(self.widget_frame)
        self.label.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label.setObjectName("label")
        self.widget_frame_layout.addWidget(self.label)
        self.verticalLayout_2.addWidget(self.widget_frame)

        self.retranslateUi(ThumbWidget)
        QtCore.QMetaObject.connectSlotsByName(ThumbWidget)

    def retranslateUi(self, ThumbWidget):
        ThumbWidget.setWindowTitle(QtGui.QApplication.translate("ThumbWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        ThumbWidget.setProperty("label", QtGui.QApplication.translate("ThumbWidget", "project_thumbnail", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
