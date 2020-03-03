# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import time
import six
import pytest
import itertools
import datetime

# Patch sgtk to se can use Qt in the tests.
import sgtk

importer = sgtk.util.qt_importer.QtImporter()
sgtk.platform.qt.QtGui = importer.QtGui
sgtk.platform.qt.QtCore = importer.QtCore

from prj_commands import CommandsView


@pytest.fixture(scope="session", autouse=True)
def qapplication():
    yield sgtk.platform.qt.QtGui.QApplication([])


class Settings(dict):
    def __init__(self, values):
        self.update(values)

    def load(self, key):
        return self.get(key)

    def save(self, key, value):
        self[key] = value


# Make sure group insertion works and does not cause issue with recent list.
@pytest.mark.parametrize("show_recents", [True, False])
@pytest.mark.parametrize(
    "commands",
    itertools.permutations(
        [
            ("Hiero", "Editorial"),
            ("Maya", "Creative Tools"),
            ("VRED", "Automotive Tools"),
            ("Publish...", "Studio"),
        ]
    ),
)
def test_sections_sorted(show_recents, commands):
    groups = ["Studio", "Creative Tools", "Editorial", "Automotive Tools"]
    # Create a view with some recents.
    view = CommandsView(
        None,
        Settings(
            {
                "project_recent_apps.3": {
                    "command 0": {"timestamp": datetime.datetime.utcnow()}
                }
            }
        ),
    )
    view.set_project({"type": "Project", "id": 3}, groups, show_recents=show_recents)

    for idx, (name, group) in enumerate(commands):
        view.add_command("command %s" % idx, name, name, "", "", [group])

    assert [section.name for section in view.sections] == groups
    assert view.recents_visible == show_recents
