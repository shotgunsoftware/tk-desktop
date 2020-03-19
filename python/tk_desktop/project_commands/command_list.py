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
from .command_button import CommandButton


class CommandList(BaseIconList):

    command_triggered = QtCore.Signal(str)

    def __init__(self, parent):
        super(CommandList, self).__init__(parent, QtGui.QGridLayout())
        self._filler = QtGui.QWidget(self)
        self._buttons = {}

    def add_command(
        self, command_name, button_name, menu_name, icon, tooltip, is_menu_default
    ):
        if button_name not in self._buttons:

            for btn in self._buttons:
                self._layout.removeWidget(self._buttons[btn])
            self._layout.removeWidget(self._filler)

            self._layout.update()
            self._buttons[button_name] = CommandButton(
                self, command_name, button_name, icon, tooltip
            )
            self._buttons[button_name].command_triggered.connect(self.command_triggered)

            for idx, name in enumerate(sorted(self._buttons)):
                column = idx % 2
                row = idx // 2
                self._layout.addWidget(self._buttons[name], row, column)

            # if last column inserted was the first one, then add a filler so the grid
            # doesn't space the button.
            if column == 0:
                self._layout.addWidget(self._filler, row, column + 1)

        if menu_name is not None:
            self._buttons[button_name].add_command(
                command_name, menu_name, icon, tooltip, is_menu_default
            )

    @property
    def buttons(self):
        for i in range(len(self._buttons)):
            yield self._layout.itemAt(i).widget()
