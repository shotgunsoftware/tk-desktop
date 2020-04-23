# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from .section import Section
from .command_list import CommandList


class CommandSection(Section):
    """
    Implement the section that contains a list of "CommandButton"s.
    """

    def __init__(self, name):
        """
        :param str name: Name of the section.
        """
        super(CommandSection, self).__init__(name, CommandList)

    def add_command(
        self, command_name, button_name, menu_name, icon, tooltip, is_menu_default
    ):
        """
        Add a command to the panel.

        :param str command_name: Name of the command.
        :param str button_name: Name of the button for the group.
        :param str menu_name: Name of the menu entry for the command.
        :param str icon: Path to the icon for this command.
        :param str tooltip: Toolkit for this command.
        :param list(str) groups: List of groups this command should be added to.
        :param bool is_menu_default: If True, this command will be the default
            command of it's group.
        """
        self._list.add_command(
            command_name, button_name, menu_name, icon, tooltip, is_menu_default
        )
