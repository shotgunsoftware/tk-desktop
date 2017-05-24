# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


import abc

from sgtk.platform.qt import QtCore, QtGui

from .ui import resources_rc

import sgtk

from .project_commands_model import ProjectCommandModel

views = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")

HOVER_STYLE = """
QPushButton, QToolButton {
    border: 1px solid %s;
    background-color: %s;
}
QToolButton {
    font-size: 15px;
}
QToolButton::menu-button  {
    border: none;
    width: 30px;
}
QPushButton:pressed, QToolButton:pressed {
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);
}
"""

REGULAR_STYLE = """
QPushButton, QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
}
QToolButton {
    font-size: 15px;
}
QToolButton::menu-arrow { image:none; }
QToolButton::menu-button  {
    border: none;
    width: 30px;
}
"""


class AbstractCommandDelegate(views.EditSelectedWidgetDelegate):
    def __init__(self, view):
        view.entered.connect(self._handle_entered)
        views.EditSelectedWidgetDelegate.__init__(self, view)

    def _handle_entered(self, index):
        if index is None:
            self.view.selectionModel().clear()
        else:
            self.view.selectionModel().setCurrentIndex(
                index,
                QtGui.QItemSelectionModel.SelectCurrent)

    def _create_widget(self, parent):
        w = self._create_button(parent)
        w.setVisible(False)
        w.clicked.connect(self._handle_clicked)
        return w

    def _on_before_paint(self, widget, model_index, style_options, selected=False):
        (source_index, item, model) = self._source_for_index(model_index)
        self._configure_widget(widget, item, style_options)
        stylesheet = self._stylesheet_for_options(style_options, selected)
        if stylesheet is not None:
            widget.setStyleSheet(stylesheet)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def _on_before_selection(self, widget, model_index, style_options):
        self._on_before_paint(widget, model_index, style_options, selected=True)

    @abc.abstractmethod
    def _configure_widget(self, widget, item, style_options):
        pass

    @abc.abstractmethod
    def _stylesheet_for_options(self, style_options, selected):
        return None

    def _source_for_index(self, model_index):
        # get the original model item for the index
        model = model_index.model()
        source_index = model_index
        while hasattr(model, "sourceModel"):
            source_index = model.mapToSource(source_index)
            model = model.sourceModel()
        item = model.itemFromIndex(source_index)
        return (source_index, item, model)

    def _handle_clicked(self, action=None):
        # figure out current index
        index = self.view.selectionModel().currentIndex()
        (_, item, model) = self._source_for_index(index)

        # need to clear the selection to avoid artifacts upon editor closing
        self.view.selectionModel().clear()

        if action is None:
            model._handle_command_triggered(item)
        else:
            model._handle_command_triggered(
                item,
                command_name=action.data()["command"],
                button_name=action.data()["button"],
                menu_name=action.text(),
                icon=action.icon(),
                tooltip=action.toolTip(),
            )

        # and this can change the filtering and sorting, so invalidate
        self.view.model().invalidate()


class RecentCommandDelegate(AbstractCommandDelegate):
    ICON_SIZE = QtCore.QSize(50, 50)
    MARGIN = 5
    SPACING = 5
    SIZER_LABEL = None

    def _create_button(self, parent):
        button = QtGui.QPushButton(parent)
        button.setFlat(True)

        layout = QtGui.QVBoxLayout(button)
        layout.setAlignment(QtCore.Qt.AlignHCenter)
        layout.setSpacing(self.SPACING)
        layout.setContentsMargins(self.SPACING, self.SPACING, self.SPACING, self.SPACING)

        button.icon_label = QtGui.QLabel(button)
        button.icon_label.setAlignment(QtCore.Qt.AlignHCenter)
        button.layout().addWidget(button.icon_label, QtCore.Qt.AlignHCenter)

        button.text_label = QtGui.QLabel(parent)
        button.text_label.setWordWrap(True)
        button.text_label.setAlignment(QtCore.Qt.AlignHCenter)
        button.layout().addWidget(button.text_label, QtCore.Qt.AlignHCenter)

        button.setFocusPolicy(QtCore.Qt.NoFocus)

        return button

    def _text_for_item(self, item):
        button_name = item.data(ProjectCommandModel.BUTTON_NAME_ROLE)
        menu_name = item.data(ProjectCommandModel.MENU_NAME_ROLE)
        if menu_name is None:
            return button_name
        else:
            return menu_name

    def _configure_widget(self, widget, item, style_options):
        widget.text_label.setText(self._text_for_item(item))

        icon = item.data(QtCore.Qt.DecorationRole)
        if icon is None:
            widget.icon_label.setPixmap(QtGui.QIcon().pixmap(self.ICON_SIZE))
        else:
            widget.icon_label.setPixmap(icon.pixmap(self.ICON_SIZE))

        widget.setToolTip(item.toolTip())

    def _stylesheet_for_options(self, style_options, selected):
        # borrowed from qtwidgets framework's thumb_widget
        p = QtGui.QPalette()
        highlight_col = p.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight)

        border = "rgb(%s, %s, %s)" % (highlight_col.red(), highlight_col.green(), highlight_col.blue())
        background = "rgba(%s, %s, %s, 25%%)" % (highlight_col.red(), highlight_col.green(), highlight_col.blue())

        if selected:
            return HOVER_STYLE % (border, background)
        return REGULAR_STYLE

    @classmethod
    def size_for_text(cls, text):
        # setup a label that we will use to get height
        if cls.SIZER_LABEL is None:
            cls.SIZER_LABEL = QtGui.QLabel()
            cls.SIZER_LABEL.setWordWrap(True)
            cls.SIZER_LABEL.setScaledContents(True)
            cls.SIZER_LABEL.setAlignment(QtCore.Qt.AlignHCenter)

        cls.SIZER_LABEL.setText(text)
        text_width = cls.SIZER_LABEL.fontMetrics().boundingRect(text).width()
        text_height = cls.SIZER_LABEL.heightForWidth(cls.ICON_SIZE.width())

        # height is icon + text + top spacing + bottom spacing + space between
        width = max(cls.ICON_SIZE.width(), text_width)
        height = cls.ICON_SIZE.height() + text_height + (3 * cls.SPACING)
        return QtCore.QSize(width + 2*cls.MARGIN, height)

    def sizeHint(self, style_options, model_index):
        # get the text size from the sizer label
        (_, item, _) = self._source_for_index(model_index)
        text = self._text_for_item(item)
        full_size = self.size_for_text(text)

        # see if the model has a limit on recents
        model = self.view.model()
        if hasattr(model, "get_recents_limit"):
            limit = model.get_recents_limit()
            if limit is not None:
                # limiting the number of recents, each one gets equal spacing
                # the spacing is the width of the view, without the spacing
                # divided up equally
                space_to_divide = self.view.width() - (self.SPACING * (limit + 1)) - self.MARGIN
                width = space_to_divide / limit
                return QtCore.QSize(width, full_size.height())

        # no limit, ask for full size
        return full_size


class ProjectCommandDelegate(AbstractCommandDelegate):
    ICON_SIZE = QtCore.QSize(50, 50)

    def __init__(self, view):
        AbstractCommandDelegate.__init__(self, view)

        # register a different delegate for the Recent group
        view.set_group_delegate(
            ProjectCommandModel.RECENT_GROUP_NAME,
            RecentCommandDelegate(view))

    def _create_button(self, parent):
        widget = QtGui.QToolButton(parent)
        widget.setSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding,
            QtGui.QSizePolicy.MinimumExpanding)
        widget.setFocusPolicy(QtCore.Qt.NoFocus)
        return widget

    def _configure_widget(self, widget, item, style_options):
        # defaults if no children
        menu = None
        popup_mode = widget.DelayedPopup
        button_icon = item.data(QtCore.Qt.DecorationRole)
        button_tooltip = item.toolTip()

        # gather list of actions if the button has multiple commands
        children = ProjectCommandModel.get_item_children_in_order(item)
        first_child = True
        if children:
            # create the menu when we have children
            menu = QtGui.QMenu()
            for child in children:
                icon = child.data(QtCore.Qt.DecorationRole)
                menu_name = child.data(ProjectCommandModel.MENU_NAME_ROLE)
                if first_child:
                    button_icon = icon
                    button_tooltip = child.toolTip()
                    if len(children) > 1:
                        menu_name = "%s*" % menu_name

                action = menu.addAction(menu_name)
                action.setData({
                    "command": child.data(ProjectCommandModel.COMMAND_ROLE),
                    "button": child.data(ProjectCommandModel.BUTTON_NAME_ROLE),
                })
                action.setToolTip(child.toolTip())
                action.setIconVisibleInMenu(False)

                if icon is not None:
                    action.setIcon(icon)

                first_child = False

            widget.setMenu(menu)

            # setup the widget to handle the menu click
            popup_mode = widget.MenuButtonPopup
            menu.triggered.connect(self._handle_clicked)

        # update button
        widget.setMenu(menu)
        widget.setPopupMode(popup_mode)
        if button_icon is None:
            widget.setIcon(QtGui.QIcon())
        else:
            widget.setIcon(button_icon)
        widget.setToolTip(button_tooltip)
        widget.setText(" %s" % item.data(ProjectCommandModel.BUTTON_NAME_ROLE))

        widget.setIconSize(self.ICON_SIZE)
        widget.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

    def _stylesheet_for_options(self, style_options, selected):
        # borrowed from qtwidgets framework's thumb_widget
        p = QtGui.QPalette()
        highlight_col = p.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight)

        border = "rgb(%s, %s, %s)" % (highlight_col.red(), highlight_col.green(), highlight_col.blue())
        background = "rgba(%s, %s, %s, 25%%)" % (highlight_col.red(), highlight_col.green(), highlight_col.blue())

        if selected:
            return HOVER_STYLE % (border, background)
        return REGULAR_STYLE

    def sizeHint(self, style_options, model_index):
        return QtCore.QSize((self.view.width() / 2) - 20, self.ICON_SIZE.height() + 8)
