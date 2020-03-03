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
from mock import Mock

# Patch sgtk to se can use Qt in the tests.
import sgtk

importer = sgtk.util.qt_importer.QtImporter()
sgtk.platform.qt.QtGui = importer.QtGui
sgtk.platform.qt.QtCore = importer.QtCore

from prj_commands import CommandsView


@pytest.fixture(scope="session", autouse=True)
def qapplication():
    yield sgtk.platform.qt.QtGui.QApplication([])


@pytest.fixture
def simple_test_view():
    view = CommandsView(None, Settings())
    view.set_project({"type": "Project", "id": 3}, ["Creative Tools", "Editorial"])
    return view


class Settings(dict):
    def __init__(self, values=None):
        if values:
            self.update(values)

    def load(self, key):
        return self.get(key)

    def save(self, key, value):
        self[key] = value


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
    """
    Ensure groups are inserted in the order they have been declared and
    that the recent list does not cause issues with that ordering.
    """
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


def test_sections_are_reused(simple_test_view):
    """
    Ensure a section is only created once.
    """
    commands = [
        ("Maya 2020", "Creative Tools"),
        ("3ds Max 2019", "Creative Tools"),
        ("Hiero 11", "Editorial"),
        ("Hiero 12", "Editorial"),
        ("3ds Max 2020", "Creative Tools"),
    ]
    for idx, (name, group) in enumerate(commands):
        simple_test_view.add_command("command %s" % idx, name, name, "", "", [group])

    assert [section.name for section in simple_test_view.sections] == [
        "Creative Tools",
        "Editorial",
    ]


def test_clear_deletes_all_but_stretcher(simple_test_view):
    """
    Ensure clearing removes all widget except for the stretcher
    """
    commands = [
        ("Maya 2020", "Creative Tools"),
        ("3ds Max 2019", "Creative Tools"),
        ("Hiero 11", "Editorial"),
        ("Hiero 12", "Editorial"),
        ("3ds Max 2020", "Creative Tools"),
    ]
    for idx, (name, group) in enumerate(commands):
        simple_test_view.add_command("command %s" % idx, name, name, "", "", [group])
    simple_test_view.clear()
    # Ensure only one item is left and it's the stretcher, not a widget.
    assert simple_test_view.layout().count() == 1
    assert simple_test_view.layout().itemAt(0).widget() is None


def test_unknown_sections_are_detected(simple_test_view):
    """
    Ensure an unknown section is caught.
    """
    with pytest.raises(RuntimeError) as exc_info:
        simple_test_view.add_command(
            "command", "button_name", "menu_name", "", "tooltip", ["Something"]
        )
    assert str(exc_info.value).startswith("Unknown group Something.")


@pytest.mark.parametrize(
    "actions", itertools.permutations(["Maya 2018", "NukeX 12.0", "3ds Max 2019"])
)
def test_button_sorting_in_section(actions, simple_test_view):
    """
    Ensure buttons are sorted properly in the list, no matter the order.
    """
    products_seen = True
    _register_commands(simple_test_view, actions)

    creative_tools = list(simple_test_view.sections)[0]
    assert [button.name for button in creative_tools.buttons] == [
        "3ds Max",
        "Maya",
        "NukeX",
    ]


def test_button_reuse_in_section(simple_test_view):
    """
    Ensure buttons are reused and not duplicated.
    """
    commands = [
        "Maya 2018",
        "Maya 2019",
        "Maya 2017",
        "Nuke 12.0",
        "Nuke 12.5",
        "NukeAssist 12.5",
    ]
    _register_commands(simple_test_view, commands)
    section = list(simple_test_view.sections)[0]
    assert [button.name for button in section.buttons] == ["Maya", "Nuke", "NukeAssist"]


@pytest.mark.parametrize(
    "commands", itertools.permutations(["Maya 2017", "Maya 2018*", "Maya 2019",])
)
def test_versions_sorted_in_menu(simple_test_view, commands):
    _register_commands(simple_test_view, commands)
    maya_button = list(list(simple_test_view.sections)[0].buttons)[0]

    assert list(
        six.ensure_str(item.text()) for item in maya_button.menu().actions()
    ) == ["Maya 2017", "Maya 2018*", "Maya 2019"]


@pytest.mark.parametrize(
    "action,expected_signal",
    [("button", "maya_2019"), ("0", "maya_2018"), ("1", "maya_2019")],
)
def test_command_actions_get_triggered(simple_test_view, action, expected_signal):
    commands = ["Maya 2018", "Maya 2019*"]
    _register_commands(simple_test_view, commands)

    mock = Mock()
    simple_test_view.command_triggered.connect(mock)
    button = list(list(simple_test_view.sections)[0].buttons)[0]

    if action == "button":
        button.click()
    else:
        button.menu().actions()[int(action)].trigger()

    mock.assert_called_with(expected_signal)


def _register_commands(view, names):
    """
    Adds a bunch of commands to the view.

    The names are expected to be of the form "Software VersionString"
    """
    defaults = {}
    for name in names:
        # Strip the start indicating a default menu entry.
        if "*" in name:
            name = name.replace("*", "")
            is_menu_default = True
        else:
            is_menu_default = False
        print(name, is_menu_default)
        # Turns "NukeX 12.5" into "nukex_125"
        command_name = name.lower().replace(" ", "_").replace(".", "")
        button_name = name.rsplit(" ", 1)[0]

        # Keep everything but the version.
        button_name = name.rsplit(" ", 1)[0]
        # Add each button.
        view.add_command(
            command_name,
            button_name,
            name,
            None,
            "",
            ["Creative Tools"],
            is_menu_default,
        )
