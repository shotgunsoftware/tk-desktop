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
    def __init__(self, size=120, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setVisible(False)

        self.size = size
        self.ui = thumb_widget.Ui_ThumbWidget()
        self.ui.setupUi(self)

    def set_thumbnail(self, pixmap):
        """ Set a thumbnail given the current pixmap. """
        # zoom to fit height, then crop to center
        pixmap = pixmap.scaledToHeight(self.size, QtCore.Qt.SmoothTransformation)
        if pixmap.width() > self.size:
            extra = pixmap.width() - self.size
            pixmap = pixmap.copy(extra/2, 0, self.size, self.size)
        self.ui.thumbnail.setPixmap(pixmap)

    def set_text(self, label):
        """Populate the line of text in the widget """
        self.ui.label.setText(label)

    def set_selected(self, selected):
        """Adjust the style sheet to indicate selection or not"""
        if selected:
            p = QtGui.QPalette()
            highlight_col = p.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight)

            border = "rgb(%s, %s, %s)" % (highlight_col.red(), highlight_col.green(), highlight_col.blue())
            background = "rgba(%s, %s, %s, 25%%)" % (highlight_col.red(), highlight_col.green(), highlight_col.blue())
            self.ui.widget_frame.setStyleSheet("""
                #widget_frame {
                    border: 1px solid %s;
                    background-color: %s;
                }
            """ % (border, background))
        else:
            self.ui.widget_frame.setStyleSheet("""
                #widget_frame {
                    border: 1px solid transparent;
                }
            """)

        # force a refresh of the stylesheet
        self.ui.widget_frame.style().unpolish(self.ui.widget_frame)
        self.ui.widget_frame.style().polish(self.ui.widget_frame)
        self.ui.widget_frame.update()
