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

import sgtk

from .ui import resources_rc

from .grouping_model import GroupingModel
from .action_list_view import ActionListView

views = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")


class DefaultGroupingHeader(QtGui.QPushButton):
    """ Default widget for a group header """
    def __init__(self, parent=None):
        QtGui.QPushButton.__init__(self, parent)

        # cache the icons for collapsed/expanded
        self.down_arrow = QtGui.QIcon(":tk-desktop/down_arrow.png")
        self.right_arrow = QtGui.QIcon(":tk-desktop/right_arrow.png")

        # adjust the button look
        self.setFlat(True)
        self.setStyleSheet("""
            text-align: left;
            font-size: 14px;
            background-color: transparent;
            border: none;
        """)

        # default is to be expanded
        self.setIcon(self.down_arrow)

    def set_expanded(self, expanded):
        """ Set the widget to be expanded or collapsed """
        if expanded:
            self.setIcon(self.down_arrow)
        else:
            self.setIcon(self.right_arrow)


class DefaultGroupingHeaderDelegate(views.WidgetDelegate):
    """ Default delegate for header items """
    def _create_widget(self, parent):
        widget = DefaultGroupingHeader(parent)
        widget.setVisible(False)
        return widget

    def _on_before_paint(self, widget, model_index, style_options):
        # map back to the source model through any proxies
        model = model_index.model()
        source_index = model_index
        while hasattr(model, "sourceModel"):
            source_index = model.mapToSource(source_index)
            model = model.sourceModel()

        # update expanded to reflect the state of the item
        group_key = model.get_item_group_key(source_index)
        expanded = model.is_group_expanded(group_key)
        widget.set_expanded(expanded)

        # update the text to be the group name
        widget.setText(model_index.data(GroupingModel.GROUP_ROLE))

    def _on_before_selection(self, widget, model_index, style_options):
        # nothing special for when a group is selected
        self._on_before_paint(widget, model_index, style_options)

    def sizeHint(self, style_options, model_index):
        # width is the width of the whole parent
        return QtCore.QSize(self.parent().viewport().width(), 30)


class DefaultGroupingFooterDelegate(views.WidgetDelegate):
    """ Default delegate for footer items """
    MARGIN = 10

    def _create_widget(self, parent):
        # footer is a simple horizontal line
        self.line = QtGui.QFrame(parent)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setStyleSheet("background-color: transparent; color: rgb(30, 30, 30);")
        self.line.setMidLineWidth(2)
        self.line.setVisible(False)
        return self.line

    def _on_before_paint(self, widget, model_index, style_options):
        # no configuration needed for the line
        return

    def _on_before_selection(self, widget, model_index, style_options):
        # nothing special for when a group is selected
        self._on_before_paint(widget, model_index, style_options)

    def sizeHint(self, style_options, model_index):
        # size is the parent width and height fixed to the margins
        return QtCore.QSize(self.parent().viewport().width(), self.MARGIN)


class GroupingListView(ActionListView):
    """ A list view that handles grouping its items """
    # expanded_changed(group_key, expanded)
    expanded_changed = QtCore.Signal(str, bool)

    def __init__(self, parent=None):
        ActionListView.__init__(self, parent)

        # keep around the delegates that should be used for the various items
        self.__group_delegates = {}
        self.__header_delegate = DefaultGroupingHeaderDelegate(self)
        self.__footer_delegate = DefaultGroupingFooterDelegate(self)

        # handle clicks
        self.clicked.connect(self.__handle_clicked)

    def set_header_delegate(self, delegate):
        """ Set the delegate to use for header items """
        self.__header_delegate = delegate

        # set the item delegates for all header items
        (source_model, _) = self.__get_source_model()
        source_items = source_model.get_header_items()
        mapped_items = self.__map_from_source_model(source_model, source_items)
        for item in mapped_items:
            self.setItemDelegateForRow(item.row(), delegate)

    def set_footer_delegate(self, delegate):
        """ Set the delegate to use for footer items """
        self.__footer_delegate = delegate

        # set the item delegates for all footer items
        (source_model, _) = self.__get_source_model()
        source_items = source_model.get_footer_items()
        mapped_items = self.__map_from_source_model(source_model, source_items)
        for item in mapped_items:
            self.setItemDelegateForRow(item.row(), delegate)

    def set_group_delegate(self, group, delegate):
        """ Set the delegate to use for content items in the given group """
        self.__group_delegates[group] = delegate

        # set the item delegates for all content items in the given group
        (source_model, _) = self.__get_source_model()
        source_items = source_model.get_items_in_group(group)
        mapped_items = self.__map_from_source_model(source_model, source_items)
        for item in mapped_items:
            self.setItemDelegateForRow(item.row(), delegate)

    def setModel(self, model):
        # override setModel to track changes to the model

        old_model = self.model()
        if old_model is not None:
            # disconnect from the current model
            old_model.rowsInserted.disconnect(self.__handle_rows_inserted)
            old_model.layoutChanged.disconnect(self.__handle_layout_changed)
            old_model.rowsMoved.disconnect(self.__handle_rows_moved)
            old_model.rowsRemoved.disconnect(self.__handle_rows_removed)

        # connect to the new model
        model.rowsInserted.connect(self.__handle_rows_inserted)
        model.layoutChanged.connect(self.__handle_layout_changed)
        model.rowsMoved.connect(self.__handle_rows_moved)
        model.rowsRemoved.connect(self.__handle_rows_removed)

        # and call the superclass
        QtGui.QListView.setModel(self, model)

    def __map_from_source_model(self, source_model, source_indexes):
        # map all the indexes from the source model into indexes for our model

        # build up a list of proxies in the order they will be used to map the indexes
        path_to_source = []
        current = self.model()
        while hasattr(current, "sourceModel") and current is not source_model:
            path_to_source.insert(0, current)
            current = current.sourceModel()

        # map all the source indexes
        mapped_indexes = []
        for index in source_indexes:
            for model in path_to_source:
                index = model.mapFromSource(index)
            mapped_indexes.append(index)

        return mapped_indexes

    def __get_source_model(self, index=None):
        # return the original source model behind any layers of proxies
        source_model = self.model()
        if source_model is None:
            return (None, None)

        # keep going through proxy layers until we find a model without a source model
        source_index = index
        while hasattr(source_model, "sourceModel"):
            if source_index is not None:
                source_index = source_model.mapToSource(source_index)
            source_model = source_model.sourceModel()

        return (source_model, source_index)

    def __handle_clicked(self, index):
        # map back to the source model
        (source_model, source_index) = self.__get_source_model(index)
        if source_model is None:
            return

        # toggle collapsed/expanded for header items
        if source_model.is_header(source_index):
            group_key = source_model.get_item_group_key(source_index)
            expanded = source_model.is_group_expanded(group_key)
            source_model.set_group_expanded(group_key, not expanded)
            self.expanded_changed.emit(group_key, not expanded)

    # handlers for anything that could effect the row delegates
    def __handle_rows_inserted(self, parent, start, end):
        self.__recalculate_delegates()

    def __handle_layout_changed(self):
        self.__recalculate_delegates()

    def __handle_rows_moved(self, src_parent, src_start, src_end, dst_parent, dst_row):
        self.__recalculate_delegates()

    def __handle_rows_removed(self, parent, start, end):
        self.__recalculate_delegates()

    def __recalculate_delegates(self):
        # reset all the item delegates to make sure all items are properly displayed
        source_model = self.model()
        if source_model is None:
            return

        # figure out the model behind any proxies
        proxy_models = []
        while hasattr(source_model, "sourceModel"):
            proxy_models.append(source_model)
            source_model = source_model.sourceModel()

        # go through each top level row to assign an appropriate delegate
        invalidIndex = QtCore.QModelIndex()
        for row in xrange(0, self.model().rowCount()):
            # map the row back to source model
            source_index = self.model().index(row, 0, invalidIndex)
            for proxy in proxy_models:
                source_index = proxy.mapToSource(source_index)

            # assign header, footer, or group specific delegates
            if source_model.is_header(source_index):
                self.setItemDelegateForRow(row, self.__header_delegate)
            if source_model.is_footer(source_index):
                self.setItemDelegateForRow(row, self.__footer_delegate)
            if source_model.is_content(source_index):
                group_key = source_model.get_item_group_key(source_index)
                self.setItemDelegateForRow(row, self.__group_delegates.get(group_key))
