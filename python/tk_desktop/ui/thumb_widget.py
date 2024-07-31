# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'thumb_widget.ui'
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

class Ui_ThumbWidget(object):
    def setupUi(self, ThumbWidget):
        if not ThumbWidget.objectName():
            ThumbWidget.setObjectName(u"ThumbWidget")
        ThumbWidget.resize(542, 453)
        self.verticalLayout_2 = QVBoxLayout(ThumbWidget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.widget_frame = QFrame(ThumbWidget)
        self.widget_frame.setObjectName(u"widget_frame")
        self.widget_frame.setMouseTracking(True)
        self.widget_frame.setFrameShape(QFrame.NoFrame)
        self.widget_frame.setFrameShadow(QFrame.Plain)
        self.widget_frame.setLineWidth(0)
        self.widget_frame_layout = QVBoxLayout(self.widget_frame)
        self.widget_frame_layout.setSpacing(10)
        self.widget_frame_layout.setContentsMargins(15, 15, 15, 15)
        self.widget_frame_layout.setObjectName(u"widget_frame_layout")
        self.thumbnail = QLabel(self.widget_frame)
        self.thumbnail.setObjectName(u"thumbnail")
        self.thumbnail.setMouseTracking(True)
        self.thumbnail.setPixmap(QPixmap(u":/tk-desktop/loading_512x400.png"))
        self.thumbnail.setScaledContents(False)
        self.thumbnail.setAlignment(Qt.AlignCenter)

        self.widget_frame_layout.addWidget(self.thumbnail)

        self.label = QLabel(self.widget_frame)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.NoTextInteraction)

        self.widget_frame_layout.addWidget(self.label)

        self.verticalLayout_2.addWidget(self.widget_frame)

        self.retranslateUi(ThumbWidget)

        QMetaObject.connectSlotsByName(ThumbWidget)
    # setupUi

    def retranslateUi(self, ThumbWidget):
        ThumbWidget.setWindowTitle(QCoreApplication.translate("ThumbWidget", u"Form", None))
        ThumbWidget.setProperty("label", QCoreApplication.translate("ThumbWidget", u"project_thumbnail", None))
    # retranslateUi
