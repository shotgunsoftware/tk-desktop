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

from .base_icon_list import BaseIconList
from .recent_button import RecentButton


class RecentList(BaseIconList):

    command_triggered = QtCore.Signal(str)
    MAX_RECENTS = 6

    def __init__(self, parent):
        super(RecentList, self).__init__(parent, QtGui.QHBoxLayout())
        self.setLayout(self._layout)
        self._layout.setSpacing(0)

    def add_command(self, command_name, button_name, icon, tooltip, timestamp):
        buttons = list(self.buttons)

        # First seach if this button is already present. If it is, move it
        # to the front.
        for button in buttons:
            # This button already exist. Make it the first button!
            if button.command_name == command_name:
                self._layout.removeWidget(button)
                self._layout.insertWidget(0, button)
                return

        # If the button didn't exist, then we need to figure where to
        # insert it.
        for idx, button in enumerate(buttons):
            # The timestamp of this command is earlier that the current
            # button, so we'll insert here.
            if timestamp >= button.timestamp:
                insert_pos = idx
                break
        else:
            # We haven't found anything, so we'll insert one past the
            # last button in the UI.
            insert_pos = len(buttons)

        if insert_pos >= self.MAX_RECENTS:
            return

        button = RecentButton(self, command_name, button_name, icon, tooltip, timestamp)
        button.command_triggered.connect(self.command_triggered)
        self._layout.insertWidget(insert_pos, button)

        if (self._layout.count()) > self.MAX_RECENTS:
            self._layout.takeAt(self.MAX_RECENTS).widget().deleteLater()

    @property
    def buttons(self):
        for i in range(self._layout.count()):
            yield self._layout.itemAt(i).widget()
