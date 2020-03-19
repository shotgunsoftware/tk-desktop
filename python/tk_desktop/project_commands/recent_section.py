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
    def __init__(self, name):
        super(RecentSection, self).__init__(name, RecentList)

    def add_command(self, command_name, button_name, icon, tooltip, timestamp):
        self._list.add_command(command_name, button_name, icon, tooltip, timestamp)
