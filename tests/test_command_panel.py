# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import pytest
import itertools
import datetime
from mock import Mock
import sys, os
import pkgutil

try:
    from tank_vendor import sgutils
except ImportError:
    from tank_vendor import six as sgutils

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "tk-core", "python")
)

# Patch sgtk to se can use Qt in the tests.
import sgtk

importer = sgtk.util.qt_importer.QtImporter()
sgtk.platform.qt.QtGui = importer.QtGui
sgtk.platform.qt.QtCore = importer.QtCore


from command_panel import CommandPanel
from command_panel import recent_list
from tk_desktop.desktop_engine_project_implementation import (
    DesktopEngineProjectImplementation,
)

PROJECT = {"type": "Project", "id": 3}
PROJECT_KEY = "project_recent_apps.3"


@pytest.fixture(scope="session", autouse=True)
def qapplication():
    yield sgtk.platform.qt.QtGui.QApplication([])


@pytest.fixture
def simple_test_view():
    view = CommandPanel(sgtk.platform.qt.QtGui.QScrollArea(), Settings())
    view.configure(PROJECT, ["Creative Tools", "Editorial"])
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
    view = CommandPanel(
        sgtk.platform.qt.QtGui.QScrollArea(),
        Settings(
            {PROJECT_KEY: {"command 0": {"timestamp": datetime.datetime.utcnow()}}}
        ),
    )
    view.configure(PROJECT, groups, show_recents=show_recents)

    for idx, (name, group) in enumerate(commands):
        view.add_command("command %s" % idx, name, name, "", "", [group])

    assert [section.name for section in view.sections] == groups
    if show_recents:
        assert view.recents is not None
    else:
        assert view.recents is None


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


def test_clear_deletes_all_but_stretcher():
    """
    Ensure clearing removes all widget except for the stretcher
    """
    view = CommandPanel(
        sgtk.platform.qt.QtGui.QScrollArea(),
        Settings(
            {PROJECT_KEY: {"maya_2020": {"timestamp": datetime.datetime.utcnow()}}}
        ),
    )
    view.configure(PROJECT, ["Creative Tools", "Editorial"], show_recents=True)
    commands = [
        ("Maya 2020", "Creative Tools"),
        ("3ds Max 2019", "Creative Tools"),
        ("Hiero 11", "Editorial"),
        ("Hiero 12", "Editorial"),
        ("3ds Max 2020", "Creative Tools"),
    ]
    for name, group in commands:
        view.add_command(_name_to_command(name), name, name, "", "", [group])
    assert len(list(view.sections)) == 2
    assert view.recents is not None

    view.clear()
    # Ensure only one item is left and it's the stretcher, not a widget.
    assert view.layout().count() == 1
    assert view.layout().itemAt(0).widget() is None

    assert len(list(view.sections)) == 0
    assert view.recents is None


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
    "commands",
    itertools.permutations(["Maya 2017", "Maya 2018*", "Maya 2019", "Maya 4.5"]),
)
def test_versions_sorted_in_menu(simple_test_view, commands):
    _register_commands(simple_test_view, commands)
    maya_button = list(list(simple_test_view.sections)[0].buttons)[0]

    assert list(
        sgutils.ensure_str(item.text()) for item in maya_button.menu().actions()
    ) == ["Maya 2018*", "Maya 2019", "Maya 2017", "Maya 4.5"]


@pytest.mark.parametrize(
    "action,expected_signal",
    [("button", "maya_2019"), ("0", "maya_2019"), ("1", "maya_2018")],
)
def test_command_actions_get_triggered(
    simple_test_view, action, expected_signal, qapplication
):
    """
    Ensure command_triggered is called for the command button click or menu
    selection.
    """
    commands = ["Maya 2018", "Maya 2019*"]
    _register_commands(simple_test_view, commands)

    mock = Mock()
    simple_test_view.command_triggered.connect(mock)
    button = list(list(simple_test_view.sections)[0].buttons)[0]

    if action == "button":
        button.click()
    else:
        button.menu().actions()[int(action)].trigger()

    qapplication.processEvents()
    mock.assert_called_with(expected_signal)


@pytest.mark.parametrize(
    "recents",
    itertools.permutations(
        [
            # This will mix the maya entries based on their date time.
            # Having the year of the last launch not match the
            # version also means we're not likely to be sorting by
            # menu name by mistake.
            ("Maya 2017", datetime.datetime(2020, 1, 1)),
            ("Maya 2018", datetime.datetime(2016, 1, 1)),
            ("Maya 2019", datetime.datetime(2012, 1, 1)),
            ("Maya 2020", datetime.datetime(2017, 1, 1)),
        ]
    ),
)
def test_recent_sorted_properly(recents, monkeypatch):
    """
    Ensure recent commands are sorted from most recently used to last.
    """
    commands = [recent[0] for recent in recents]
    settings = Settings(
        {
            PROJECT_KEY: {
                _name_to_command(recent[0]): {"timestamp": recent[1]}
                for recent in recents
            }
        }
    )
    monkeypatch.setattr(recent_list, "MAX_RECENTS", 3)
    view = CommandPanel(sgtk.platform.qt.QtGui.QScrollArea(), settings)
    view.configure(PROJECT, ["Creative Tools"], show_recents=True)
    _register_commands(view, commands)
    assert _get_recents_title(view) == [
        "Maya 2017",
        "Maya 2020",
        "Maya 2018",
    ]


def _get_recents_title(view):
    """
    Get the name of each button in the recent's tab.

    :param view: The command panel.

    :returns: List of names of each button from most recent to last.
    """
    return [button.name for button in view.recents.buttons]


def _get_nth(iterator, position):
    """
    Retrieves the n-th item of a collection for which we have an iterator.
    :param int position: Position of the item to retrieve.

    :returns: The n-th item.
    """
    return list(iterator)[position]


def test_recent_time_update_when_clicking():
    """
    Make sure the list of recents get updated accordingly when you
    click on the command buttons.
    """
    settings = Settings()
    view = CommandPanel(sgtk.platform.qt.QtGui.QScrollArea(), settings)
    view.configure(PROJECT, ["Creative Tools"], show_recents=True)
    _register_commands(view, ["Maya 2017", "Maya 2018*", "Maya 2019"])

    # There should be no recents tab for now.
    assert view.recents is None

    creative_tools = _get_nth(view.sections, 0)
    maya_button = _get_nth(creative_tools.buttons, 0)
    maya_button.click()
    # But when we click a button, one should appear
    assert view.recents is not None
    # The button should have triggered a Maya 2018 launch since it
    # is the default.
    assert _get_nth(view.recents.buttons, 0).name == "Maya 2018"
    actions = list(maya_button.menu().actions())
    # The first action is the default one, so clicking it shouldn't change anything.
    actions[0].trigger()  # This is Maya 2018
    assert _get_recents_title(view) == ["Maya 2018"]
    actions[2].trigger()  # This is Maya 2017.
    assert _get_recents_title(view) == ["Maya 2017", "Maya 2018"]
    actions[0].trigger()  # This is Maya 2018
    assert _get_recents_title(view) == ["Maya 2018", "Maya 2017"]
    actions[1].trigger()  # This is Maya 2019
    assert _get_recents_title(view) == ["Maya 2019", "Maya 2018", "Maya 2017"]


def test_recents_not_added_when_disabled(qapplication):
    """
    Ensure recent buttons are not added when show_recents is false.
    """
    settings = Settings()
    view = CommandPanel(sgtk.platform.qt.QtGui.QScrollArea(), settings)
    view.configure(PROJECT, ["Creative Tools"], show_recents=False)

    _register_commands(view, ["Maya 2017", "Maya 2018*", "Maya 2019"])

    assert view.recents is None

    creative_tools = _get_nth(view.sections, 0)
    maya_button = _get_nth(creative_tools.buttons, 0)
    maya_button.click()

    qapplication.processEvents()

    assert view.recents is None


def _name_to_command(name):
    """
    Converts a product name into a command string.
    """
    # e.g. turns "NukeX 12.5" into "nukex_125"
    return name.lower().replace(" ", "_").replace(".", "")


def _register_commands(view, names):
    """
    Adds a bunch of commands to the view.

    The names are expected to be of the form "Software VersionString"

    This will yield a list of values that make each of those unique
    commands.

    For example, "Maya 2019.5*" would yield the following:
        command name: maya_20195
        button name: Maya
        name: Maya 2019
        icon: None
        groups: ["Creative Tools"]
        tooltip: ""
        is_menu_defaut: True (would have been false if * wasn't included)
    """
    for name in names:
        # Strip the start indicating a default menu entry.
        if "*" in name:
            name = name.replace("*", "")
            is_menu_default = True
        else:
            is_menu_default = False

        command_name = _name_to_command(name)

        # e.g. extracts "Nuke Studio" out of "Nuke Studio 10.2"
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


def test_appkit():
    """
    Test the _set_appkit method by forcing an AttributeError
    exception.
    """
    appkit_inst = DesktopEngineProjectImplementation(engine=None)
    try:
        # Forcing an AttributeError exception
        # by passing a None type argument to the method.
        appkit_inst._set_appkit(None)
        assert True
    except ImportError:
        assert False
    except AttributeError:
        assert False
