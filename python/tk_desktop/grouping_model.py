# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank.platform.qt import QtCore, QtGui


class GroupingProxyModel(QtGui.QSortFilterProxyModel):
    """
    A proxy model designed to layer on top of a GroupingModel.

    This implements sorting items by groups and keeps groups in order with items
    representing the headers and footers.  This proxy is also responsible for
    hiding items in collapsed groups.
    """
    def setSourceModel(self, src_model):
        """ Overridden from the base class in order to react to toggling groups """
        # connect up signal to react to groups being toggled expanded or collapsed
        old_model = self.sourceModel()
        if old_model is not None:
            old_model.group_toggled.disconnect(self.__handle_group_toggled)
            old_model.groups_modified.disconnect(self.__handle_groups_modified)
        src_model.group_toggled.connect(self.__handle_group_toggled)
        src_model.groups_modified.connect(self.__handle_groups_modified)

        QtGui.QSortFilterProxyModel.setSourceModel(self, src_model)

    def lessThan(self, left, right):
        """ Sorting overridden to order groups by rank and keep items in their group """
        # grab needed info
        left_type = left.data(GroupingModel.ITEM_TYPE_ROLE)
        right_type = right.data(GroupingModel.ITEM_TYPE_ROLE)
        left_group_rank = left.data(GroupingModel.GROUP_RANK_ROLE)
        right_group_rank = right.data(GroupingModel.GROUP_RANK_ROLE)

        # if both items are in the same group, group_headers first, else by row
        if left_group_rank == right_group_rank:
            if left_type == GroupingModel.ITEM_TYPE_HEADER or \
               right_type == GroupingModel.ITEM_TYPE_FOOTER:
                return True
            if right_type == GroupingModel.ITEM_TYPE_FOOTER or \
               left_type == GroupingModel.ITEM_TYPE_HEADER:
                return False
            return left.row() < right.row()

        # different groups, sort by group index
        return left_group_rank < right_group_rank

    def filterAcceptsRow(self, src_row, src_parent):
        """ Filter to enable groups being collapsed """
        if src_parent.isValid():
            # visibility is inherited if this item is not at the root of a hierarchy
            return self.filterAcceptsRow(src_parent.row(), src_parent.parent())

        src_model = self.sourceModel()
        index = src_model.index(src_row, 0, src_parent)

        # items that are not content are always visible if not empty
        if not src_model.is_content(index):
            group = src_model.get_item_group_key(index)
            content = src_model.get_items_in_group(group)
            return len(content) > 0

        # content items are only shown if the group is expanded
        group_key = src_model.get_item_group_key(index)
        if src_model.is_group_expanded(group_key):
            return True
        return False

    def __handle_groups_modified(self):
        # trigger to re-filter if grouping changes
        self.invalidate()

    def __handle_group_toggled(self, group_key, expanded):
        # trigger to re-filter if a group is collapsed or expanded
        self.invalidateFilter()


class GroupingModel(QtGui.QStandardItemModel):
    """ A model that manages items in collapsible groups. """
    GROUP_ROLE = QtCore.Qt.UserRole + 1001  # stores the group an item is in
    GROUP_RANK_ROLE = QtCore.Qt.UserRole + 1002  # stores the ordering for a group
    GROUP_VISIBLE_ROLE = QtCore.Qt.UserRole + 1003  # store whether a group is collapsed
    ITEM_TYPE_ROLE = QtCore.Qt.UserRole + 1004  # store the type of an item (header, footer, content)

    # the types for non-content items
    ITEM_TYPE_HEADER = "group_header"
    ITEM_TYPE_FOOTER = "group_footer"

    # a signal that is emitted when a group is expanded or collapsed
    group_toggled = QtCore.Signal(str, bool)

    # a signal that is emitted when groups are modified
    groups_modified = QtCore.Signal()

    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, parent)

        # key for the default group
        self.__groups = {}
        self.__default_group = None

        # keep track of changes that could effect grouping
        self.rowsRemoved.connect(self.__handle_rows_removed)

    def clear(self):
        # clear groups and default group in addition to the model
        QtGui.QStandardItemModel.clear(self)
        if self.__groups:
            self.__groups = {}
            self.__default_group = None
            self.groups_modified.emit()

    # manage groups
    def create_group(self, group_key, expanded=True):
        """
        Create a group for group_key

        Returns a tuple of the header and footer model items created for the group.
        """
        if group_key in self.__groups:
            raise ValueError("group already exists '%s'" % group_key)

        # create the header item, defaults to expanded
        header = QtGui.QStandardItem()
        header.setData(self.ITEM_TYPE_HEADER, self.ITEM_TYPE_ROLE)
        header.setData(group_key, self.GROUP_ROLE)
        header.setData(expanded, self.GROUP_VISIBLE_ROLE)

        # create the footer item
        footer = QtGui.QStandardItem()
        footer.setData(self.ITEM_TYPE_FOOTER, self.ITEM_TYPE_ROLE)
        footer.setData(group_key, self.GROUP_ROLE)

        # set flags so clicks flow through to these items
        header.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)
        footer.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)

        # track the header and the footer
        self.__groups[group_key] = {
            "header": header,
            "footer": footer,
        }

        # and add to the model
        self.appendRow(header)
        self.appendRow(footer)

        self.groups_modified.emit()
        return (header, footer)

    def set_default_group(self, group_key):
        """ Set the group that an item if there is no explicit assignment """
        if group_key not in self.__groups:
            raise KeyError("no group '%s'" % group_key)
        if self.__default_group != group_key:
            self.groups_modified.emit()
            self.__default_group = group_key

    def get_header_items(self):
        """ Returns all the header items """
        self.__get_items_of_type(self.ITEM_TYPE_HEADER)

    def get_footer_items(self):
        """ Returns all the footer items """
        self.__get_items_of_type(self.ITEM_TYPE_FOOTER)

    def get_group_header(self, group_key):
        """ Returns the header item for the given group """
        if group_key not in self.__groups:
            raise KeyError("no group '%s'" % group_key)
        return self.__groups[group_key]["header"]

    def get_group_footer(self, group_key):
        """ Returns the footer item for the given group """
        if group_key not in self.__groups:
            raise KeyError("no group '%s'" % group_key)
        return self.__groups[group_key].get("footer")

    def get_items_in_group(self, group):
        """ Returns all the content items for the given group """
        start = self.index(0, 0)
        match_flags = QtCore.Qt.MatchExactly
        matching_indexes = self.match(start, self.GROUP_ROLE, group, -1, match_flags)
        return [index for index in matching_indexes if index.data(self.ITEM_TYPE_ROLE) is None]

    def set_group_rank(self, group_key, rank):
        """ Set the rank for the given group.  Groups are ordered by rank. """
        # get all items with matching group_key
        start = self.index(0, 0)
        match_flags = QtCore.Qt.MatchExactly
        matching_indexes = self.match(start, self.GROUP_ROLE, group_key, -1, match_flags)

        if len(matching_indexes) == 0:
            raise KeyError("no group '%s'" % group_key)

        # and update the rank on all of them
        for index in matching_indexes:
            item = self.itemFromIndex(index)
            item.setData(rank, self.GROUP_RANK_ROLE)

        self.groups_modified.emit()

    def is_group_expanded(self, group_key):
        """ Returns true of the given group is expanded """
        if group_key not in self.__groups:
            raise KeyError("no group '%s'" % group_key)

        # expanded/collapsed is stored in the header
        header = self.__groups[group_key]["header"]
        if header.data(self.GROUP_VISIBLE_ROLE):
            return True
        return False

    def set_group_expanded(self, group_key, expanded):
        """ Set the given group to be expanded or not """
        if group_key not in self.__groups:
            raise KeyError("no group '%s'" % group_key)

        # store the expanded state in the header of the group
        header = self.__groups[group_key]["header"]
        header.setData(expanded, self.GROUP_VISIBLE_ROLE)

        # let listeners know that the state has changed
        self.group_toggled.emit(group_key, expanded)

    def get_expanded_state(self):
        state = {}
        for group_key in self.__groups.keys():
            header = self.__groups[group_key]["header"]
            state[group_key] = header.data(self.GROUP_VISIBLE_ROLE)
        return state

    def set_expanded_state(self, state):
        for (group_key, expanded) in state.iteritems():
            if group_key in self.__groups:
                self.set_group_expanded(group_key, expanded)

    # manage items
    def set_item_group(self, item, group_key):
        """ Put the given item in the given group """
        if group_key not in self.__groups:
            raise KeyError("no group '%s'" % group_key)

        # update the group and rank of the item
        rank = self.__groups[group_key]["header"].data(self.GROUP_RANK_ROLE)
        item.setData(group_key, self.GROUP_ROLE)
        item.setData(rank, self.GROUP_RANK_ROLE)

        self.groups_modified.emit()

    def get_item_group_key(self, item):
        """
        Get the group for the given item.
        If none has been set, return the default.
        """
        group_key = item.data(self.GROUP_ROLE)
        if group_key is None:
            return self.__default_group
        return group_key

    def is_content(self, item_or_index):
        """ Returns true if the given item or index is a content item """
        return self.__check_type(item_or_index, None)

    def is_header(self, item_or_index):
        """ Returns true if the given item or index is a header item """
        return self.__check_type(item_or_index, self.ITEM_TYPE_HEADER)

    def is_footer(self, item_or_index):
        """ Returns true if the given item or index is a footer item """
        return self.__check_type(item_or_index, self.ITEM_TYPE_FOOTER)

    def __get_items_of_type(self, row_type):
        # returns all items of a given type
        start = self.index(0, 0)
        match_flags = QtCore.Qt.MatchExactly
        return self.match(start, self.ITEM_TYPE_ROLE, row_type, -1, match_flags)

    def __check_type(self, item_or_index, check_type):
        # check the type of the given item or index
        parent = item_or_index.parent()

        if isinstance(item_or_index, QtGui.QStandardItem) and parent is not None:
            # item that is not top level
            item_type = None
        elif isinstance(item_or_index, QtCore.QModelIndex) and parent.isValid():
            # index that is not top level
            item_type = None
        else:
            # top level item or index, type is stored directly
            item_type = item_or_index.data(self.ITEM_TYPE_ROLE)

        # return true if check_type matches
        if check_type is None:
            return item_type is None
        return item_type == check_type

    # react to data changes
    def __handle_rows_removed(self, parent, start, end):
        # if this is not a top level item there is nothing to do
        if not parent.isValid():
            return

        for row in xrange(start, end+1):
            item = self.item(row, 0)
            group_key = item.data(self.GROUP_ROLE)
            item_type = item.data(self.ITEM_TYPE_ROLE)

            # if a header item is removed then remove the group
            if item_type == self.ITEM_TYPE_HEADER:
                del self.__groups[group_key]

            # if item is a footer then just remove the footer
            if item_type == self.ITEM_TYPE_FOOTER:
                del self.__groups[group_key]["footer"]

        self.groups_modified.emit()
