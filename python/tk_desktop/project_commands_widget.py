# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import re
import sgtk
import datetime

from PySide import QtGui
from PySide import QtCore

from .login import ShotgunLogin
from .command_group_widget import GroupWidget
from .command_group_widget import CommandGroupWidget


class ProjectCommandsWidget(QtGui.QFrame):
    """
    Class that registers commands into collapsible groups and keeps track
    of app launches via events in Shotgun.  Those events are used to
    populate a recent group where buttons are created to make launching
    recently used commands easy.
    """
    APP_LAUNCH_EVENT_TYPE = "Toolkit_Desktop_AppLaunch"

    # signal emitted when a command is triggered
    # arguments are the group and the command_name of the triggered command
    command_triggered = QtCore.Signal(str, str)

    def __init__(self, parent=None):
        QtGui.QFrame.__init__(self, parent)

        self.__project = None
        self.__groups_map = {}
        self.__groups_list = []
        self.__recent_group = None
        self.__recent_layout = None

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.setStyleSheet("""
            background-color: transparent;
            border: none;
        """)

    def set_project(self, project, groups):
        """ Reset the widget to register commands for the given project """
        self.clear()
        self.__project = project
        self.__groups_list = groups
        self.__initialize_recents()

    def finalize(self):
        """
        Must be called once all the commands have been registered.

        Takes care of any setup that depends on the apps that have been
        registered, such as which commands to show in the recents area.
        """
        # fill out the recent widget
        self.__populate_recents()

        # add the groups that have had commands registered in the correct order
        for group_name in self.__groups_list:
            group_widget = self.__groups_map.get(group_name)

            if group_widget is None:
                # Did not get a command registered for that group
                continue

            # let each group know that all commands have been registered
            group_widget.finalize()

            # leave stretch at the end
            self.layout().insertWidget(self.layout().count()-1, group_widget)

    def __initialize_recents(self):
        """
        Pull down the information from Shotgun for what the recent command
        launches have been.  Needed to track which ones are still registered.
        """

        # dictionary to keep track of the commands launched with recency information
        # each command name keeps track of a timestamp of when it was last launched
        # and a boolean saying whether the corresponding command has been registered
        self.__recents = {}

        # need to know what login to find events for
        login = ShotgunLogin.get_login()

        # pull down matching invents for the current project for the current user
        filters = [
            ['user', 'is', login],
            ['project', 'is', self.__project],
            ['event_type', 'is', self.APP_LAUNCH_EVENT_TYPE],
        ]

        # execute the Shotgun summarize command
        # get one group per description with a summary of the latest created_at
        connection = sgtk.platform.current_engine().shotgun
        summary = connection.summarize(
            entity_type='EventLogEntry',
            filters=filters,
            summary_fields=[{'field': 'created_at', 'type': 'latest'}],
            grouping=[{'field': 'description', 'type': 'exact', 'direction': 'desc'}],
        )

        # parse the results
        for group in summary["groups"]:
            # convert the text representation of created_at to a datetime
            text_stamp = group["summaries"]["created_at"]
            time_stamp = datetime.datetime.strptime(text_stamp, "%Y-%m-%d %H:%M:%S %Z")

            # pull the command name from the description
            description = group["group_name"]
            match = re.search("'(?P<name>.+)'", description)
            if match is not None:
                name = match.group("name")

                # if multiple descriptions end up with the same name use the most recent one
                existing_info = self.__recents.setdefault(name,
                    {'timestamp': time_stamp, 'registered': False})
                if existing_info['timestamp'] < time_stamp:
                    self.__recents[name]['timestamp'] = time_stamp

    def __populate_recents(self):
        """
        Populate the recents area with the commands that have been registered in
        the order of most to least recent.
        """
        # get a list of all the registered command names in the the correct order
        recents = sorted(
            [r for r in self.__recents if self.__recents[r]['registered']],
            key=lambda key: self.__recents[key]["timestamp"],
            reverse=True
        )

        # initialize the recents list
        recents_list = QtGui.QListWidget()
        recents_list.setViewMode(recents_list.IconMode)
        recents_list.setWrapping(True)
        recents_list.setUniformItemSizes(True)
        recents_list.setWordWrap(True)
        recents_list.setIconSize(QtCore.QSize(50, 50))
        recents_list.setSelectionMode(recents_list.NoSelection)
        recents_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                font-size: 12px;
            }

            QListWidget::item {
                border: none;
                padding: 5px;
                height: 80px;
            }

            QListWidget::item:hover {
                background-color: rgb(32, 32, 32);
            }
        """)

        for (i, recent) in enumerate(recents):
            icon = self.__recents[recent].get("icon")
            menu_name = self.__recents[recent]["menu_name"]
            button_name = self.__recents[recent]["button_name"]
            command_name = self.__recents[recent]["command_name"]
            tooltip = self.__recents[recent]["tooltip"]

            if menu_name is None:
                title = button_name
            else:
                title = "%s %s" % (button_name, menu_name)

            if icon is None:
                item = QtGui.QListWidgetItem(title, recents_list)
            else:
                item = QtGui.QListWidgetItem(icon, title, recents_list)

            if tooltip is not None:
                item.setToolTip(tooltip)

            item.setData(QtCore.Qt.UserRole, command_name)

        def item_clicked(index):
            item = recents_list.itemFromIndex(index)
            command_name = item.data(QtCore.Qt.UserRole)
            self.command_triggered.emit("Recent", command_name)

        recents_list.clicked.connect(item_clicked)

        recents_list.setMaximumHeight(recents_list.sizeHintForRow(0))
        self.__recent_layout.addWidget(recents_list, 0)

    def clear(self):
        """ remove all the groups from the widget """
        # no updates while we clear
        self.setUpdatesEnabled(False)

        # remove every item from the layout
        item = self.layout().takeAt(0)
        while item is not None:
            widget = item.widget()
            if widget is not None:
                # hide the widget so everything looks good until cleanup
                widget.hide()
            self.layout().removeItem(item)
            item = self.layout().takeAt(0)

        # add the Recent group
        self.__recent_group = GroupWidget("Recent", self)
        self.layout().addWidget(self.__recent_group)

        self.__recent_layout = QtGui.QVBoxLayout()
        self.__recent_layout.setContentsMargins(0, 0, 0, 0)
        self.__recent_group.widget.setLayout(self.__recent_layout)

        # add the stretch back in
        self.layout().addStretch()

        # and get updates going again
        self.layout().invalidate()
        self.setUpdatesEnabled(True)

        # reset internal state
        self.__groups_map = {}
        self.__groups_list = []

    def add_command(self, command_name, button_name, menu_name, icon, tooltip, groups):
        # command will show up in the recent group
        if command_name in self.__recents:
            self.__recents[command_name].update({
                "icon": icon,
                "registered": True,
                "menu_name": menu_name,
                "button_name": button_name,
                "command_name": command_name,
                "tooltip": tooltip,
            })

        # add command to each group it has requested
        for group_name in groups:
            group_widget = self.__groups_map.get(group_name)
            if group_widget is None:
                # create the group widget if it doesn't exist
                group_widget = CommandGroupWidget(group_name, self)
                self.__groups_map[group_name] = group_widget

                # listen for commands triggered
                group_widget.command_triggered.connect(
                    lambda command_name: self.__handle_command_triggered(group_name, command_name))

            # and add the command
            group_widget.add_command(command_name, button_name, menu_name, icon, tooltip)

    def __handle_command_triggered(self, group_name, command_name):
        # Create an event log entry to track app launches
        engine = sgtk.platform.current_engine()
        connection = engine.shotgun

        login = ShotgunLogin.get_login()
        data = {
            # recent is populated by grouping on description, so it needs
            # to be the same for each event created for a given name, but
            # different for different names
            #
            # this is parsed when populating the recents menu
            "description": "App '%s' launched from tk-desktop-engine" % command_name,
            "event_type": self.APP_LAUNCH_EVENT_TYPE,
            "project": self.__project,
            "meta": {"name": command_name, "group": group_name},
            "user": login,
        }

        engine.log_debug("Registering app launch event: %s" % data)

        # use toolkit connection to get ApiUser permissions for event creation
        connection.create("EventLogEntry", data)

        # and notify that the command was triggered
        self.command_triggered.emit(group_name, command_name)
