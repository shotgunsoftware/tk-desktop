# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import datetime
import time
import re

from sgtk.platform.qt import QtCore, QtGui

import sgtk
from sgtk.deploy import util

from .grouping_model import GroupingModel
from .grouping_model import GroupingProxyModel


class ProjectCommandProxyModel(GroupingProxyModel):
    def __init__(self, parent=None):
        GroupingProxyModel.__init__(self, parent)
        self.setDynamicSortFilter(True)

        self.__recents_limit = None

    def set_recents_limit(self, limit):
        self.__recents_limit = limit
        self.invalidate()

    def get_recents_limit(self):
        return self.__recents_limit

    def filterAcceptsRow(self, source_row, source_parent):
        # check to see if filter is valid
        # we will only filter if we have a restriction on the number of recents set
        # and if the model is set to show recents
        src_model = self.sourceModel()
        if self.__recents_limit is None or src_model.show_recents is False:
            return GroupingProxyModel.filterAcceptsRow(self, source_row, source_parent)

        # now only filter if the row is content in the recents group
        index = src_model.index(source_row, 0, source_parent)
        item = src_model.itemFromIndex(index)
        group = src_model.get_item_group_key(item)
        if group != ProjectCommandModel.RECENT_GROUP_NAME or not src_model.is_content(item):
            return GroupingProxyModel.filterAcceptsRow(self, source_row, source_parent)

        # now we are going to get all the recent items in proper order
        recents = src_model.get_items_in_group(ProjectCommandModel.RECENT_GROUP_NAME)

        def recent_item_cmp(left, right):
            if self.lessThan(left, right):
                return -1
            if self.lessThan(right, left):
                return 1
            return 0
        recents.sort(cmp=recent_item_cmp)

        # see if the index of this item in that list is within our restriction
        rows_in_order = [r.row() for r in recents]
        current_index = rows_in_order.index(item.row())
        if current_index < self.__recents_limit:
            return GroupingProxyModel.filterAcceptsRow(self, source_row, source_parent)

        # item is outside of our limit
        return False

    def lessThan(self, left, right):
        # Order recents then pass through to default grouping order
        src_model = self.sourceModel()

        if not src_model.is_content(left) or not src_model.is_content(right):
            # let grouping model handle sorting non-content
            return GroupingProxyModel.lessThan(self, left, right)

        left_group = src_model.get_item_group_key(left)
        right_group = src_model.get_item_group_key(right)

        if left_group != right_group:
            # let grouping model handle sorting across groups
            return GroupingProxyModel.lessThan(self, left, right)

        if left_group == ProjectCommandModel.RECENT_GROUP_NAME:
            # sort recents by launch time
            left_launch = left.data(ProjectCommandModel.LAST_LAUNCH_ROLE)
            if left_launch is None:
                return True

            right_launch = right.data(ProjectCommandModel.LAST_LAUNCH_ROLE)
            if right_launch is None:
                return False

            return left_launch > right_launch
        else:
            # sort alphabetically for commands
            left_name = left.data(ProjectCommandModel.BUTTON_NAME_ROLE)
            right_name = right.data(ProjectCommandModel.BUTTON_NAME_ROLE)
            return left_name < right_name


class ProjectCommandModel(GroupingModel):
    APP_LAUNCH_EVENT_TYPE = "Toolkit_Desktop_AppLaunch"

    RECENT_GROUP_NAME = "RECENT"

    BUTTON_NAME_ROLE = QtCore.Qt.UserRole + 1
    MENU_NAME_ROLE = QtCore.Qt.UserRole + 2
    COMMAND_ROLE = QtCore.Qt.UserRole + 3
    LAST_LAUNCH_ROLE = QtCore.Qt.UserRole + 4

    # signal emitted when a command is triggered
    # arguments are the group and the command_name of the triggered command
    command_triggered = QtCore.Signal(str, str)

    def __init__(self, parent=None):
        GroupingModel.__init__(self, parent)

        self.__project = None
        self.__recents = {}
        self.show_recents = True

    def set_project(self, project, groups, show_recents=True):
        self.clear()
        self.__project = project
        self.show_recents = show_recents

        for (i, group) in enumerate(groups):
            group = group.upper()
            (header, _) = self.create_group(group)
            self.set_group_rank(group, i+1)

        if self.show_recents:
            (header, _) = self.create_group(self.RECENT_GROUP_NAME)
            self.set_group_rank(self.RECENT_GROUP_NAME, 0)
            self.__load_recents()

    def add_command(self, name, button_name, menu_name, icon, command_tooltip, groups):
        if self.show_recents and name in self.__recents and not self.__recents[name]["added"]:
            item = QtGui.QStandardItem()
            item.setData(button_name, self.BUTTON_NAME_ROLE)
            item.setData(menu_name, self.MENU_NAME_ROLE)
            item.setData(name, self.COMMAND_ROLE)
            item.setToolTip(command_tooltip)
            item.setData(self.__recents[name]["timestamp"], self.LAST_LAUNCH_ROLE)
            if icon is not None:
                item.setIcon(icon)

            self.set_item_group(item, self.RECENT_GROUP_NAME)
            self.appendRow(item)
            self.__recents[name]["added"] = True

        for group in groups:
            group = group.upper()

            # Has this command already been added?
            start = self.index(0, 0)
            match_flags = QtCore.Qt.MatchExactly
            indexes_in_group = self.match(start, self.GROUP_ROLE, group, -1, match_flags)

            item = None
            for index in indexes_in_group:
                if index.data(self.BUTTON_NAME_ROLE) == button_name:
                    # button already exists in this group, reuse item
                    item = self.itemFromIndex(index)
                    break

            if item is None:
                item = QtGui.QStandardItem()
                item.setData(button_name, self.BUTTON_NAME_ROLE)
                item.setData(menu_name, self.MENU_NAME_ROLE)
                item.setData(name, self.COMMAND_ROLE)
                item.setToolTip(command_tooltip)

                if icon is not None:
                    item.setIcon(icon)
                self.set_item_group(item, group)
                self.appendRow(item)

            if menu_name is not None:
                menu_item = QtGui.QStandardItem()
                menu_item.setData(button_name, self.BUTTON_NAME_ROLE)
                menu_item.setData(menu_name, self.MENU_NAME_ROLE)
                menu_item.setData(name, self.COMMAND_ROLE)
                menu_item.setToolTip(command_tooltip)
                if icon is not None:
                    menu_item.setIcon(icon)
                item.appendRow(menu_item)

    @classmethod
    def get_item_children_in_order(cls, item):
        i = 0
        children = []
        while True:
            child = item.child(i, 0)
            i += 1
            if child is None:
                break

            children.append(child)

        # sort children in reverse version order
        def child_cmp(left, right):
            left_version = left.data(cls.MENU_NAME_ROLE)
            right_version = right.data(cls.MENU_NAME_ROLE)
            if util.is_version_newer(left_version, right_version):
                return -1
            if util.is_version_older(left_version, right_version):
                return 1
            return 0
        children.sort(cmp=child_cmp)
        return children

    def _handle_command_triggered(self, item, command_name=None, button_name=None,
                                  menu_name=None, icon=None, tooltip=None):
        # get the info for the command
        # if the info was explicit use that, otherwise if the item has children
        # use the info from the first one after sorting, otherwise use the item's
        # data directly
        children = self.get_item_children_in_order(item)
        group_name = item.data(self.GROUP_ROLE)
        if command_name is None:
            if children:
                command_name = children[0].data(self.COMMAND_ROLE)
            else:
                command_name = item.data(self.COMMAND_ROLE)
        if button_name is None:
            if children:
                button_name = children[0].data(self.BUTTON_NAME_ROLE)
            else:
                button_name = item.data(self.BUTTON_NAME_ROLE)
        if menu_name is None:
            if children:
                menu_name = children[0].data(self.MENU_NAME_ROLE)
            else:
                menu_name = item.data(self.MENU_NAME_ROLE)
        if icon is None:
            if children:
                icon = children[0].data(QtCore.Qt.DecorationRole)
            else:
                icon = item.data(QtCore.Qt.DecorationRole)
        if tooltip is None:
            if children:
                tooltip = children[0].toolTip()
            else:
                tooltip = item.toolTip()

        # save app launch in recent settings
        self.__recents[command_name] = {"timestamp": datetime.datetime.utcnow(), "added": False}
        self.__store_recents()

        if self.show_recents:
            # find the corresponding recent if it exists
            start = self.index(0, 0)
            match_flags = QtCore.Qt.MatchExactly
            indexes_in_recent = self.match(start, self.GROUP_ROLE, self.RECENT_GROUP_NAME, -1,
                                           match_flags)

            recent_item = None
            for index in indexes_in_recent:
                if index.data(self.COMMAND_ROLE) == command_name:
                    recent_item = self.itemFromIndex(index)
                    break

            # create it if it doesn't
            if recent_item is None:
                recent_item = QtGui.QStandardItem()
                recent_item.setData(button_name, self.BUTTON_NAME_ROLE)
                recent_item.setData(menu_name, self.MENU_NAME_ROLE)
                recent_item.setData(command_name, self.COMMAND_ROLE)
                recent_item.setToolTip(tooltip)
                if icon is not None:
                    recent_item.setIcon(icon)

                self.set_item_group(recent_item, self.RECENT_GROUP_NAME)
                self.appendRow(recent_item)

            # update its timestamp, keep everything in utc which is what shotgun does
            recent_item.setData(datetime.datetime.utcnow(), self.LAST_LAUNCH_ROLE)

        # and notify that the command was triggered
        self.command_triggered.emit(group_name, command_name)

    def __store_recents(self):
        """
        Stores a list of recently launched apps in the user settings. Resets the "added" key so
        when the settings are loaded again, each item will be added to the list. They are stored as
        a dictionary in the following format::

            self.__recents = {
                'launch_nuke': {
                    'timestamp': datetime.datetime(2016, 5, 20, 21, 48, 17, 495234),
                    'added': False},
                ...
            }
        """
        recents = {}
        for name, details in self.__recents.iteritems():
            recents[name] = {"timestamp": details["timestamp"], "added": False}
        key = "project_recent_apps.%d" % self.__project["id"]
        self.parent()._save_setting(key, recents, site_specific=True)

    def __load_recents(self):
        """
        Loads recently launched apps from the user settings and returns them in a dict. See above
        for the format.
        """
        key = "project_recent_apps.%d" % self.__project["id"]
        self.__recents = self.parent()._load_setting(key, None, True) or {}
