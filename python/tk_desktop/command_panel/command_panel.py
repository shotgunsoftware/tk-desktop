# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from datetime import datetime
from sgtk.platform.qt import QtGui, QtCore
from tank_vendor import six

from .shared import MAX_RECENTS
from .recent_section import RecentSection
from .command_section import CommandSection

TIME_STAMP_FORMAT = "%m/%d/%Y, %H:%M:%S"


class CommandPanel(QtGui.QWidget):
    """
    Panel of buttons that is used to launch Toolkit commands. The panel itself
    is not aware of Toolkit and simply emits command_triggered signals with the name
    of the Toolkit command to execute.

    The buttons are grouped into sections, which can be collapsed by the user.

    There is an optional recent section that show the most recently launched commands.

    The recent commands and the expanded or collapsed state of the sections is persisted
    between used by the settings object passed in on creation.
    """

    # Emits the command name to execute.
    command_triggered = QtCore.Signal(str)

    def __init__(self, parent, settings):
        """
        :param parent: Parent widget.
        :param settings: Settings object to persist and restore state.
        """
        super(CommandPanel, self).__init__(parent)
        # The app style sheet styles this widget so give it the proper name.
        self.setObjectName("command_panel")
        self._layout = QtGui.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 10, 0, 0)
        self._layout.addStretch(1)
        self.setLayout(self._layout)

        # We want the background color to apply to the entire surface of the widget
        # in PySide instead of just under its children
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)

        filter = ResizeEventFilter(parent)
        filter.resized.connect(self._on_parent_resized)
        parent.installEventFilter(filter)

        self.command_triggered.connect(self._update_recents_list)

        # Settings object allowing to read and write settings.
        self._settings = settings
        # The widget for the recently launched command. Will be None if
        # the recent list is disabled or if there are no recent commands.
        self._recents_widget = None
        # Dictionary of the commands that were executed recently.
        # Follows this structure:
        # self._recents = {
        #     'launch_nuke': {
        #         'timestamp': datetime.datetime(2016, 5, 20, 21, 48, 17, 495234),
        #         'added': False},
        #     ...
        # }
        self._recents = {}
        # Keeps track of all the command information so we can easily build the recent
        # command list.
        self._command_info = {}
        # List of section names that the widget knows about. The sections
        # will be displayed in that order.
        self._section_names = []
        # If True, the recent list will be displayed.
        self._show_recents = False
        # Keeps a reference to scroll view that owns this widget.
        self._scroll_view_owner = parent

    def _on_parent_resized(self):
        """
        Called when the parent widget is resized.
        """
        # This widget always completely covers it's parent.
        self.resize(self.parentWidget().size())
        # The children widgets need to be resized appropriately so they expand
        # appropriately
        self._restrict_children()

    def _restrict_children(self):
        """
        Ensure each section is as wide as possible.
        """
        width = self._get_optimal_width()

        for section in self.sections:
            section.setMaximumWidth(width)

        self._restrict_recent_buttons(width)

    def _restrict_recent_buttons(self, width):
        """
        Restrict the size of recent buttons so that we can fit up to
        MAX_RECENTS buttons on the dialog.

        :param int width: Size of a button.
        """
        if self._recents_widget:
            self._recents_widget.setMaximumWidth(width)

    def _get_optimal_width(self):
        """
        Compute the optimal width for the widget.
        """
        # The optimal width is the width of the scroll view minus the
        # scroll bar width, if visible.
        width = self._scroll_view_owner.width()
        if self._scroll_view_owner.verticalScrollBar().isVisible():
            width -= self._scroll_view_owner.verticalScrollBar().width()
        return width

    def sizeHint(self):
        """
        Hint Qt to the size we want.
        """
        return QtCore.QSize(self._get_optimal_width(), 30)

    @property
    def recents(self):
        """
        The RecentList widget. Will be None if there are no recent commands
        or if the RecentList was disabled.
        """
        return self._recents_widget

    def configure(self, current_project, groups, show_recents=True):
        """
        Configure the widget.

        :param dict current_project: The project we're displaying commands for.
        :param list(str) groups: List of groups names to display.
        :param bool show_recents: If True, recently launched commands will be displayed.
        """
        self._current_project = current_project
        self._show_recents = show_recents
        self._section_names = groups
        self._load_recents()
        self._load_expanded()

    def clear(self):
        """
        Clear the widget.
        """
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

        self._command_info = {}
        self._recents = {}

    def _update_recents_list(self, command_name):
        """
        Called when a command is launched from the panel.

        This is used to keep the recent list updated.
        """
        if self._show_recents is False:
            return

        # Make sure the string is a str and not unicode. This happens in
        # Python 2.7.
        command_name = six.ensure_str(command_name)

        self._recents[command_name] = {"timestamp": datetime.utcnow()}
        self._store_recents()
        self._refresh_recent_list(command_name)
        self._restrict_recent_buttons(self._get_optimal_width())

    def _refresh_recent_list(self, command_name):
        """
        Update the recent list by adding the given command.

        :param str command_name: Name of the command to add.
        """
        # If RecentSection has not been created yet, it's time to create one!
        # This will happen when the first command is launched or when
        # a previously launched command is added to the panel for the first time.
        if self._recents_widget is None:
            self._recents_widget = RecentSection()
            self._recents_widget.set_expanded(self._expanded_state.get("RECENT", True))
            self._recents_widget.command_triggered.connect(self.command_triggered)
            self._recents_widget.expand_toggled.connect(self._update_expanded_state)
            self._layout.insertWidget(0, self._recents_widget)

        # Get all the information for this command so we can create a recent
        # button.
        timestamp = self._recents[command_name]["timestamp"]
        command = self._command_info[command_name]

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
        for group_name in groups:
            # Search for the requested group.
            current_group = self._find_or_insert_section(group_name)
            current_group.add_command(
                command_name, button_name, menu_name, icon, tooltip, is_menu_default
            )
            # Caches information about the command so that if we need to show a recent
            # button for it we have it at the ready instead of retrieving it from the
            # button itself.
            self._command_info[command_name] = {
                # Single command buttons, like the Publish button, do not have a menu,
                # so use the name of the button directly.
                "menu_name": menu_name or button_name,
                "icon": icon,
                "tooltip": tooltip,
            }
        if self._show_recents and command_name in self._recents:
            self._refresh_recent_list(command_name)

        self._restrict_children()

    @property
    def sections(self):
        """
        An iterator over the different sections.

        This does not include the Recent list.
        """
        if self._recents_widget:
            first_section = 1
        else:
            first_section = 0

        # The last widget is the spacer, so we stop iterating before it.
        for i in range(first_section, self._layout.count() - 1):
            yield self._layout.itemAt(i).widget()

    def _find_or_insert_section(self, group_name):
        """
        Search for a section with the given name. If the section is not found,
        it is inserted at the expected position.
        """
        # Do not create a group if it is not supported.
        if group_name not in self._section_names:
            raise RuntimeError(
                "Unknown group %s. Expecting one of %s"
                % (group_name, self._section_names)
            )

        # Due to visual glitches in PySide1, we're inserting sections as we need them
        # instead of creating them all hidden up front.

        # Skip over the recent widget when looking for where to insert the
        # new section.
        if self._recents_widget:
            first_group_index = 1
        else:
            first_group_index = 0

        # First, generate a collection of sections and their indices
        name_to_pos = {section.name: idx for idx, section in enumerate(self.sections)}

        # If the section already exists, then return it.
        if group_name in name_to_pos:
            return self._layout.itemAt(
                first_group_index + name_to_pos[group_name]
            ).widget()

        # The section does not exist!

        # Let's pretend the following groups are configured: A, B, C and D.
        # We currently have groups C and D and we now want to insert B.
        # Since we'll be using insertWidget, which inserts a widget right
        # before another, we'll look for the first widget that we know that comes
        # after B.

        # Find the groups after the one we're searching for (B in the above example).
        idx = self._section_names.index(group_name)
        groups_after = self._section_names[idx + 1 :]

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

        new_group = CommandSection(group_name)
        new_group.set_expanded(self._expanded_state.get(new_group.name.upper(), True))
        new_group.command_triggered.connect(self.command_triggered)
        new_group.expand_toggled.connect(self._update_expanded_state)
        self._layout.insertWidget(
            insert_position + first_group_index, new_group, alignment=QtCore.Qt.AlignTop
        )

        return new_group

    def _store_recents(self):
        """
        Store a list of recently launched apps in the user settings.

        They are stored as a dictionary in the following format::

            {
                'launch_nuke': {
                    'timestamp': datetime.datetime(2016, 5, 20, 21, 48, 17, 495234),
                    'added': False},
                ...
            }

        Do not edit this format. We're keeping it to be backwards compatible with
        previous versions of the engine.
        """
        recents = {}
        for name, details in self._recents.items():
            # Convert the datetime object to a string to make serialization across Python versions easier.
            recents[name] = {
                "timestamp": details["timestamp"].strftime(TIME_STAMP_FORMAT),
                "added": False,
            }
        key = "project_recent_apps.%d" % self._current_project["id"]
        self._settings.save(key, recents)

    def _load_recents(self):
        """
        Loads recently launched apps from the user settings and returns them in a dict. See above
        for the format.
        """
        key = "project_recent_apps.%d" % self._current_project["id"]
        recents = self._settings.load(key) or {}

        # convert the serialized datetime strings to datetime objects
        for recent in recents.values():
            # We used to store persistently the datetime object directly, rather than converting it
            # to a string, so we must first check if the setting is a string before converting it.
            if type(recent["timestamp"]) == str:
                recent["timestamp"] = datetime.strptime(
                    recent["timestamp"], TIME_STAMP_FORMAT
                )

        self._recents = recents

    def _update_expanded_state(self, section_name, is_expanded):
        """
        Update the state of the expanded flag for the given section and store the
        new state in the settings.

        They are stored as a dictionary in the following format::
            {
                'RECENT': True,
                'CREATIVE TOOLS': False,
                ...
            }

        Do not edit this format. We're keeping it to be backwards compatible with
        previous versions of the engine.

        :param str section_name: Name of the section.
        :param bool is_expanded: True if the section is expanded, False otherwise.
        """
        self._expanded_state[section_name.upper()] = is_expanded
        key = "project_expanded_state.%d" % self._current_project["id"]
        self._settings.save(key, self._expanded_state)

    def _load_expanded(self):
        """
        Load the expanded state for all the sections.
        """
        key = "project_expanded_state.%d" % self._current_project["id"]
        self._expanded_state = self._settings.load(key) or {}


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
