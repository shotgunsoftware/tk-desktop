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
from .command_button import CommandButton


class CommandList(BaseIconList):
    """
    Display and manage a list of commands that are grouped under one or more CommandButtons.
    """

    def __init__(self, parent):
        """
        :param QtGui.QWidget: Parent widget.
        """
        # The Commands are displayed on a grid.
        super(CommandList, self).__init__(parent, QtGui.QGridLayout())
        # The filler is a widget that prevents the button on the last row
        # from taking up the whole row if there is only one.
        self._filler = QtGui.QWidget(self)
        # This will hold the CommandButton instances index by the button name.
        self._buttons = {}

    def add_command(
        self, command_name, button_name, menu_name, icon, tooltip, is_menu_default
    ):
        """
        Add a command to the list of command.

        :param str command_name: Name of the toolkit command to run when this
            command is selected.
        :param str button_name: Name of the button to put this command under.
        :param str menu_name: Name of the menu item in the dropdown.
        :param str icon: Path to the icon file.
        :param str tooltip: Tooltip for the button.
        :param bool: If ``True``, clicking on the button will run this action.
        """

        # If this button does not currently exist.
        if button_name not in self._buttons:
            # Remove all buttons from the grid since we can't insert and move things
            # around in such a layout.
            for btn in self._buttons:
                self._layout.removeWidget(self._buttons[btn])
            self._layout.removeWidget(self._filler)

            self._layout.update()
            # Create and hook up the button so clicks are propagated.
            self._buttons[button_name] = CommandButton(
                self, command_name, button_name, icon, tooltip
            )
            self._buttons[button_name].command_triggered.connect(self.command_triggered)

            # Adds two button per rows, use as many rows as needed.
            for idx, name in enumerate(sorted(self._buttons)):
                column = idx % 2
                row = idx // 2
                self._layout.addWidget(self._buttons[name], row, column)

            # If the last row had only one button, insert the filler so the
            # button does not occupy the whole row.
            if column == 0:
                self._layout.addWidget(self._filler, row, column + 1)

        self._buttons[button_name].add_command(
            command_name, menu_name, icon, tooltip, is_menu_default
        )

    @property
    def buttons(self):
        """
        An iterator over the buttons in the list.
        """
        for i in range(len(self._buttons)):
            yield self._layout.itemAt(i).widget()
