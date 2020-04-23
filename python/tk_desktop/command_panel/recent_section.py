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
from .recent_list import RecentList


class RecentSection(Section):
    """
    Manage a list of recent icons.
    """

    def __init__(self):
        super(RecentSection, self).__init__("Recent", RecentList)

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
        self._list.add_command(command_name, button_name, icon, tooltip, timestamp)
