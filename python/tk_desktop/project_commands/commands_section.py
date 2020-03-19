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


class CommandsSection(Section):
    def __init__(self, name):
        super(CommandsSection, self).__init__(name, CommandList)

    def add_command(
        self, command_name, button_name, menu_name, icon, tooltip, is_menu_default
    ):
        self._list.add_command(
            command_name, button_name, menu_name, icon, tooltip, is_menu_default
        )
