# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import datetime
from sgtk.platform.qt import QtGui, QtCore


from .recent_section import RecentSection
from .commands_section import CommandsSection


class ProjectCommands(QtGui.QWidget):

    command_triggered = QtCore.Signal(str)

    def __init__(self, parent, settings):
        super(ProjectCommands, self).__init__(parent)
        self.setObjectName("project_commands")
        self._layout = QtGui.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        # If we want the background color to apply to the entire surface of the widget
        # in PySide instead of just under its children we need to set this flag.
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setLayout(self._layout)
        self._layout.addStretch(1)
        self._recents_widget = None
        self._recents = {}
        self._groups = []
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self._show_recents = False

        self._layout.setContentsMargins(0, 10, 0, 0)

        self.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)

        filter = ResizeEventFilter(parent)
        filter.resized.connect(self._on_parent_resized)
        parent.installEventFilter(filter)

        self._main_window = parent

        self.command_triggered.connect(self._update_recents_list)

        # Caches the information about all commands so we can
        # retrieve it when updating recents
        self._recent_commands_cache = {}

        self._settings = settings

    def _on_parent_resized(self):
        """
        Special slot hooked up to the event filter.
        When associated widget is resized this slot is being called.
        """
        # resize overlay

        self.resize(self.parentWidget().size())
        self._restrict_children()

    def _restrict_children(self):
        width = self._main_window.width()
        if self._main_window.verticalScrollBar().isVisible():
            width -= self._main_window.verticalScrollBar().width()

        if self._recents_widget:
            self._recents_widget.setMaximumWidth(width)

        for section in self.sections:
            section.setMaximumWidth(width)

    def sizeHint(self):
        return QtCore.QSize(self._main_window.viewport().width(), 30)

    @property
    def recents(self):
        return self._recents_widget

    def set_project(self, current_project, groups, show_recents=True):
        self._current_project = current_project
        self._show_recents = show_recents
        self._groups = groups
        self._load_recents()
        self._load_expanded()

    def clear(self):
        if self._recents_widget:
            self.layout().removeWidget(self._recents_widget)
            self._recents_widget.deleteLater()
            self._recents_widget = None

        # Remove all the sections. Create a copy of the list
        # buttons so we don't iterate and modify the list at the
        # same time.
        for section in list(self.sections):
            self.layout().removeWidget(section)
            section.deleteLater()

        # There should be only one item left, the stretcher.
        assert self.layout().count() == 1

        self._recent_commands_cache = {}
        self._recents = {}

    def _update_recents_list(self, command_name):
        self._recents[command_name] = {
            "timestamp": datetime.datetime.utcnow(),
            # This is present for backwards compatibility with
            # previous version of desktop. we do not actually use this
            # value for this implementation.
            "added": False,
        }
        self._store_recents()
        self._refresh_recent_list(command_name)

    def _refresh_recent_list(self, command_name):
        # if action in recent list.
        if self._recents_widget is None:
            self._recents_widget = RecentSection()
            self._recents_widget.set_expanded(self._expanded_state.get("RECENT", True))
            self._recents_widget.command_triggered.connect(self.command_triggered)
            self._recents_widget.expand_toggled.connect(self._update_expanded_state)
            self._layout.insertWidget(0, self._recents_widget)

        timestamp = self._recents[command_name]["timestamp"]
        command = self._recent_commands_cache[command_name]

        self._recents_widget.add_command(
            command_name,
            command["menu_name"],
            command["icon"],
            command["tooltip"],
            timestamp,
        )

    def add_command(
        self,
        command_name,
        button_name,
        menu_name,
        icon,
        tooltip,
        groups,
        is_menu_default=False,
    ):
        for group_name in groups:
            # Search for the requested group.
            current_group = self._find_or_insert_section(group_name)
            current_group.add_command(
                command_name, button_name, menu_name, icon, tooltip, is_menu_default
            )
            # Caches information about the command so that if it is a recent
            self._recent_commands_cache[command_name] = {
                # Single action buttons, like the Publish button, do not have a menu,
                # so use the name of the button directly.
                "menu_name": menu_name or button_name,
                "icon": icon,
                "tooltip": tooltip,
            }
        if self._show_recents and command_name in self._recents:
            self._refresh_recent_list(command_name)

        self._restrict_children()

    @property
    def recents_visible(self):
        return bool(self._recents_widget)

    @property
    def sections(self):
        if self._recents_widget:
            first_section = 1
        else:
            first_section = 0

        for i in range(first_section, self._layout.count() - 1):
            yield self._layout.itemAt(i).widget()

    def _find_or_insert_section(self, group_name):
        if group_name not in self._groups:
            raise RuntimeError(
                "Unknown group %s. Expecting one of %s" % (group_name, self._groups)
            )
        # Due to visual glitches in PySide1, we're inserting sections as we need them
        # instead of creating them all hidden up front.
        # Skip over the recent widgets.
        if self._recents_widget:
            first_group_index = 1
        else:
            first_group_index = 0

        # First, generate a collection of sections and their indices
        name_to_pos = {section.name: idx for idx, section in enumerate(self.sections)}

        # If the section already exists.
        if group_name in name_to_pos:
            return self._layout.itemAt(
                first_group_index + name_to_pos[group_name]
            ).widget()

        # The section does not exist!

        # Let's the following groups are configured: A, B, C and D.
        # We currently have groups C and D and we now want to insert B.
        # Since we'll be using insertWidget, which inserts a widget right
        # before another, we'll look for the first that we know that comes
        # after B.

        # Find the groups after the one we're searching for (B in the above example).
        idx = self._groups.index(group_name)
        groups_after = self._groups[idx + 1 :]

        # Loop over the remaining groups (C and D in the above example)
        for group_after in groups_after:
            # If that group exists, we've found where we'll insert the group!
            if group_after in name_to_pos:
                insert_position = name_to_pos[group_after]
                break
        else:
            # We haven't found any of the groups that come after the one
            # we want to insert, which means we'll have to insert right before
            # the stretch item.
            insert_position = len(name_to_pos)

        new_group = CommandsSection(group_name)
        new_group.set_expanded(self._expanded_state.get(new_group.name.upper(), True))
        new_group.command_triggered.connect(self.command_triggered)
        new_group.expand_toggled.connect(self._update_expanded_state)
        self._layout.insertWidget(
            insert_position + first_group_index, new_group, alignment=QtCore.Qt.AlignTop
        )

        return new_group

    def _store_recents(self):
        """
        Stores a list of recently launched apps in the user settings. Resets the "added" key so
        when the settings are loaded again, each item will be added to the list. They are stored as
        a dictionary in the following format::

            self._recents = {
                'launch_nuke': {
                    'timestamp': datetime.datetime(2016, 5, 20, 21, 48, 17, 495234),
                    'added': False},
                ...
            }
        """
        recents = {}
        for name, details in self._recents.items():
            recents[name] = {"timestamp": details["timestamp"], "added": False}
        key = "project_recent_apps.%d" % self._current_project["id"]
        self._settings.save(key, recents)

    def _load_recents(self):
        """
        Loads recently launched apps from the user settings and returns them in a dict. See above
        for the format.
        """
        key = "project_recent_apps.%d" % self._current_project["id"]
        self._recents = self._settings.load(key) or {}

    def _update_expanded_state(self, section_name, is_expanded):
        self._expanded_state[section_name.upper()] = is_expanded
        self._save_expanded()

    def _load_expanded(self):
        key = "project_expanded_state.%d" % self._current_project["id"]
        self._expanded_state = self._settings.load(key) or {}

    def _save_expanded(self):
        key = "project_expanded_state.%d" % self._current_project["id"]
        self._settings.save(key, self._expanded_state)


class ResizeEventFilter(QtCore.QObject):
    """
    Event filter which emits a resized signal whenever
    the monitored widget resizes. This is so that the overlay wrapper
    class can be informed whenever the Widget gets a resize event.
    """

    resized = QtCore.Signal()

    def eventFilter(self, obj, event):
        # peek at the message
        if event.type() == QtCore.QEvent.Resize:
            # re-broadcast any resize events
            self.resized.emit()
        # pass it on!
        return False
