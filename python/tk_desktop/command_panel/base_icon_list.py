# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from sgtk.platform.qt import QtGui, QtCore


class BaseIconList(QtGui.QWidget):
    """
    Base class for a list of icons inside a section.

    It provides the command_triggered signal and customizes the layout.
    """

    command_triggered = QtCore.Signal(str)

    def __init__(self, parent, layout):
        """
        :param parent: Parent widget.
        :param layout: Qt layout for this widget.
        """
        super(BaseIconList, self).__init__(parent)
        self._layout = layout
        self.setLayout(layout)
        self._layout.setContentsMargins(0, 0, 0, 0)
