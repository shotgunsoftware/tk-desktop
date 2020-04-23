# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from sgtk.platform.qt import QtCore, QtGui


class SectionHeader(QtGui.QPushButton):
    """
    Group header widget.

    It displays the name of a section with a arrow that can be clicked on to
    expand and collapse the section.
    """

    def __init__(self, parent=None):
        QtGui.QPushButton.__init__(self, parent)

        # cache the icons for collapsed/expanded
        self.down_arrow = QtGui.QIcon(":tk-desktop/down_arrow.png")
        self.right_arrow = QtGui.QIcon(":tk-desktop/right_arrow.png")

        # adjust the button look
        self.setFlat(True)
        self.setCheckable(True)
        self.setChecked(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet(
            """
            text-align: left;
            font-size: 14px;
            background-color: transparent;
            border: none;
        """
        )

    def is_expanded(self):
        """
        :returns: ``True`` if the widget displays the expanded state, ``False`` otherwise.
        """
        return self.isChecked()

    def set_expanded(self, is_expanded):
        """
        Set to the expanded or collapsed display state.

        :param bool is_expanded: If set to ``True``, the widget will display
            the expanded state, the collapsed state otherwise.
        """
        self.setChecked(is_expanded)
        if is_expanded:
            self.setIcon(self.down_arrow)
        else:
            self.setIcon(self.right_arrow)
