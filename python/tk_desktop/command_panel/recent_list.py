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

from .base_icon_list import BaseIconList
from .recent_button import RecentButton
from .shared import MAX_RECENTS


class RecentList(BaseIconList):
    """
    Display and manage a list of RecentButton.
    """

    def __init__(self, parent):
        super(RecentList, self).__init__(parent, QtGui.QHBoxLayout())
        self._layout.setSpacing(3)

        # Fill the recents list with invisible stretchers to start with.
        # Then as the actual recent items start to get populated the
        # stretchers will be replaced.
        for _ in range(MAX_RECENTS):
            self._layout.addStretch()

    def add_command(self, command_name, button_name, icon, tooltip, timestamp):
        """
        Add a command to the recent list of commands.

        :param str command_name: Name of the toolkit command to run when this
            command is selected.
        :param str button_name: Name of the recent button.
        :param str icon: Path to the icon file.
        :param str tooltip: Tooltip for the button.
        :param datetime.datetime timestamp: When the command was last executed.
        """

        buttons = list(self.buttons)
        # First search if this button is already present. If it is, move it
        # to the front.
        for button in buttons:
            # If this button already exists. Make it the first button!
            if button.command_name == command_name:
                self._layout.removeWidget(button)
                self._layout.insertWidget(0, button)
                return

        # If the button didn't exist, then we need to figure where to
        # insert it.
        for idx, button in enumerate(buttons):
            # The timestamp of the command we're inserting is more recent
            # than the current command, so we're inserting the command before.
            if timestamp >= button.timestamp:
                insert_pos = idx
                break
        else:
            # We haven't found anything, so we'll insert one past the
            # last button in the UI.
            insert_pos = len(buttons)

        # Since all the launches are tracked, but only the most recent are displayed,
        # it's possible we're going to try to insert commands that are older than the
        # MAX_RECENTS ones. When that happens, we can simply quit.
        if insert_pos >= MAX_RECENTS:
            return

        button = RecentButton(self, command_name, button_name, icon, tooltip, timestamp)
        button.command_triggered.connect(self.command_triggered)
        self._layout.insertWidget(insert_pos, button)

        # If there are now more recents than we should have in the GUI,
        # drop the last one.
        if self._layout.count() > MAX_RECENTS:
            widget = self._layout.takeAt(MAX_RECENTS).widget()
            # The widget maybe None if it is a stretcher object.
            if widget:
                widget.deleteLater()

    @property
    def buttons(self):
        """
        An iterator over the buttons in the list.
        """
        for i in range(self._layout.count()):
            widget = self._layout.itemAt(i).widget()
            # The widget will be None if the layout item was a spacer.
            # If it is a spacer we can skip that as it is not technically a button.
            if widget:
                yield widget
