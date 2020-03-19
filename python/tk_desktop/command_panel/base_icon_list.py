# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from sgtk.platform.qt import QtGui


class BaseIconList(QtGui.QWidget):
    def __init__(self, parent, layout):
        super(BaseIconList, self).__init__(parent)
        self._layout = layout
        self.setLayout(layout)
        self._layout.setContentsMargins(0, 0, 0, 0)
