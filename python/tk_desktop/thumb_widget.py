# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank.platform.qt import QtCore, QtGui

from .ui import thumb_widget


class ThumbWidget(QtGui.QWidget):
    """Thumbnail widget to poplulate the projects list view """
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.setVisible(False)

        self.ui = thumb_widget.Ui_ThumbWidget()
        self.ui.setupUi(self)

    def set_thumbnail(self, pixmap):
        """ Set a thumbnail given the current pixmap. """
        # resize to a fixed size preserving aspect ratio
        preserved_aspect = pixmap.scaled(120, 90, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.ui.thumbnail.setPixmap(preserved_aspect)

    def set_text(self, label):
        """Populate the line of text in the widget """
        self.ui.label.setText(label)
        self.setToolTip(label)

    def set_selected(self, selected):
        """Adjust the style sheet to indicate selection or not"""
        if selected:
            # set the background color
            self.ui.widget_frame.setStyleSheet(
                """#widget_frame {background-color: rgb(65, 65, 65);}""")
        else:
            self.ui.widget_frame.setStyleSheet("")
