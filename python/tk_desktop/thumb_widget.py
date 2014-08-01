# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank.platform.qt import QtGui
from tank.platform.qt import QtCore

from .ui import thumb_widget


class ThumbWidget(QtGui.QWidget):
    """Thumbnail widget to poplulate the projects list view """
    SIZER_WIDGET = None

    def __init__(self, width=120, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setVisible(False)

        self.ui = thumb_widget.Ui_ThumbWidget()
        self.ui.setupUi(self)

        # fix thumbnail size to full width minus margins
        margins = self.ui.widget_frame_layout.contentsMargins()
        self.thumb_size = width - margins.left() - margins.right()
        self.ui.thumbnail.setFixedSize(self.thumb_size, self.thumb_size)

    def set_thumbnail(self, pixmap):
        """ Set a thumbnail given the current pixmap. """
        # zoom to fit height, then crop to center
        pixmap = pixmap.scaledToHeight(self.thumb_size, QtCore.Qt.SmoothTransformation)
        if pixmap.width() > self.thumb_size:
            extra = pixmap.width() - self.thumb_size
            pixmap = pixmap.copy(extra/2, 0, self.thumb_size, self.thumb_size)
        self.ui.thumbnail.setPixmap(pixmap)

    @classmethod
    def height_for_width(cls, width, text):
        if cls.SIZER_WIDGET is None:
            cls.SIZER_WIDGET = cls(width)

        # figure out height for the given width
        # top/bottom margins + thumbnail + spacing + label height
        margins = cls.SIZER_WIDGET.ui.widget_frame_layout.contentsMargins()
        spacing = cls.SIZER_WIDGET.ui.widget_frame_layout.spacing()
        thumb_height = cls.SIZER_WIDGET.thumb_size

        cls.SIZER_WIDGET.set_text(text)
        label_height = cls.SIZER_WIDGET.ui.label.heightForWidth(width - margins.left() - margins.right())

        return margins.top() + margins.bottom() + spacing + thumb_height + label_height

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
