# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from sgtk.platform.qt import QtGui
from sgtk.platform.qt import QtCore


class ActionListView(QtGui.QListView):
    """Subclass of QListView that handles special logic when the items launch actions on select"""

    def mousePressEvent(self, event):
        # Ignore right click events
        if event.button() == QtCore.Qt.RightButton:
            return

        # pass through to QListView for all other mouse events
        QtGui.QListView.mousePressEvent(self, event)
