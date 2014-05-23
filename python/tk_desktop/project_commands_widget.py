# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk

from PySide import QtGui
from PySide import QtCore

from .ui import resources_rc

from .project_commands_model import ProjectCommandModel

shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "shotgun_view")

TOOLBUTTON_STYLE = """
QToolButton {
    text-align: left;
    font-size: 16px;
    margin-left: 10px;
    margin-right: 10px;
    padding: 6px;
    border: 1px solid transparent;
    background-color: transparent;
}

QToolButton::menu-arrow {
    image:none;
}

QToolButton::menu-button  {
    border: none;
    width: 30px;
}
"""

TOOLBUTTON_HOVER_STYLE = """
QToolButton {
    text-align: left;
    font-size: 16px;
    margin-left: 10px;
    margin-right: 10px;
    padding: 6px;
    border: 1px solid transparent;
    background-color: rgb(32, 32, 32);
}

QToolButton:pressed {
    border: 1px solid orange;
}

QToolButton::menu-button  {
    border: none;
    width: 30px;
}
"""

PUSHBUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    border-width: 1px;
    border-color: transparent;
    border-style: solid;
}

QLabel {
    font-size: 12px;
}
"""

PUSHBUTTON_HOVER_STYLE = """
QPushButton {
    background-color: rgb(32, 32, 32);
    border-width: 1px;
    border-color: transparent;
    border-style: solid;
}

QPushButton:pressed {
    border: 1px solid orange;
}

QLabel {
    font-size: 12px;
}
"""


class AbstractCommandDelegate(shotgun_view.WidgetDelegate):
    def __init__(self, view):
        shotgun_view.WidgetDelegate.__init__(self, view)
        self.__view = view
        view.entered.connect(self._handle_entered)

    def _handle_entered(self, index):
        if index is None:
            self.__view.selectionModel().clear()
        else:
            self.__view.selectionModel().setCurrentIndex(
                index,
                QtGui.QItemSelectionModel.SelectCurrent)

    def _create_widget(self, parent):
        w = self._create_button(parent)
        w.setVisible(False)
        w.clicked.connect(self._handle_clicked)
        return w

    def _on_before_paint(self, widget, model_index, style_options, selected=False):
        (source_index, item, model) = self._source_for_index(model_index)
        self._configure_widget(widget, item)
        stylesheet = self._stylesheet_for_options(style_options, selected)
        if stylesheet is not None:
            widget.setStyleSheet(stylesheet)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def _on_before_selection(self, widget, model_index, style_options):
        self._on_before_paint(widget, model_index, style_options, selected=True)

    def _configure_widget(self, widget, item):
        raise NotImplementedError("abstract method called")

    def _stylesheet_for_options(self, style_options, selected):
        raise NotImplementedError("abstract method called")

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
        index = self.__view.selectionModel().currentIndex()
        (_, item, model) = self._source_for_index(index)

        # need to clear the selection to avoid artifacts upon editor closing
        self.__view.selectionModel().clear()

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

        self.__view.model().sort(0)


class RecentCommandDelegate(AbstractCommandDelegate):
    ICON_SIZE = QtCore.QSize(60, 60)
    MARGIN = 10
    TEXT_HEIGHT = 50

    def _create_button(self, parent):
        button = QtGui.QPushButton(parent)
        button.setFlat(True)
        button.setLayout(QtGui.QVBoxLayout())

        icon_label = QtGui.QLabel(button)
        icon_label.setFixedSize(self.ICON_SIZE)
        icon_label.setAlignment(QtCore.Qt.AlignHCenter)
        icon_label.setScaledContents(True)
        button.layout().addWidget(icon_label)

        text_label = QtGui.QLabel(parent)
        text_label.setWordWrap(True)
        text_label.setScaledContents(True)
        text_label.setAlignment(QtCore.Qt.AlignHCenter)
        button.layout().addWidget(text_label)

        return button

    def _configure_widget(self, widget, item):
        text_label = widget.layout().itemAt(1).widget()
        button_name = item.data(ProjectCommandModel.BUTTON_NAME_ROLE)
        menu_name = item.data(ProjectCommandModel.MENU_NAME_ROLE)
        if menu_name is None:
            text_label.setText(button_name)
        else:
            text_label.setText("%s\n%s" % (button_name, menu_name))

        icon_label = widget.layout().itemAt(0).widget()
        icon = item.data(QtCore.Qt.DecorationRole)
        if icon is None:
            icon_label.setPixmap(QtGui.QIcon().pixmap(self.ICON_SIZE))
        else:
            icon_label.setPixmap(icon.pixmap(self.ICON_SIZE))

        widget.setToolTip(item.toolTip())

    def _stylesheet_for_options(self, style_options, selected):
        if selected:
            return PUSHBUTTON_HOVER_STYLE
        return PUSHBUTTON_STYLE

    def sizeHint(self, style_options, model_index):
        return QtCore.QSize(
            self.ICON_SIZE.width() + 2*self.MARGIN,
            self.ICON_SIZE.height() + self.TEXT_HEIGHT)


class ProjectCommandDelegate(AbstractCommandDelegate):
    ICON_SIZE = QtCore.QSize(56, 56)

    def __init__(self, view):
        AbstractCommandDelegate.__init__(self, view)
        self.__view = view

        # register a different delegate for the Recent group
        view.set_group_delegate(
            ProjectCommandModel.RECENT_GROUP_NAME,
            RecentCommandDelegate(view))

    def _create_button(self, parent):
        widget = QtGui.QToolButton(parent)
        widget.setSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding,
            QtGui.QSizePolicy.MinimumExpanding)
        return widget

    def _configure_widget(self, widget, item):
        # update button text
        widget.setText(item.data(ProjectCommandModel.BUTTON_NAME_ROLE))

        # update button icon
        icon = item.data(QtCore.Qt.DecorationRole)
        widget.setToolTip(item.toolTip())
        if icon is None:
            widget.setIcon(QtGui.QIcon())
        else:
            widget.setIcon(icon)

        widget.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        widget.setIconSize(self.ICON_SIZE)

        # update button menu
        i = 0
        menu = None
        while True:
            child = item.child(i, 0)
            i += 1
            if child is None:
                break

            if menu is None:
                menu = QtGui.QMenu()
            action = menu.addAction(child.data(ProjectCommandModel.MENU_NAME_ROLE))
            action.setData({
                "command": child.data(ProjectCommandModel.COMMAND_ROLE),
                "button": child.data(ProjectCommandModel.BUTTON_NAME_ROLE),
            })
            action.setToolTip(child.toolTip())
            action.setIconVisibleInMenu(False)

            icon = child.data(QtCore.Qt.DecorationRole)
            if icon is not None:
                action.setIcon(icon)
        widget.setMenu(menu)

        if menu is None:
            widget.setPopupMode(widget.DelayedPopup)
        else:
            widget.setPopupMode(widget.MenuButtonPopup)
            menu.triggered.connect(self._handle_clicked)

    def _stylesheet_for_options(self, style_options, selected):
        if selected:
            return TOOLBUTTON_HOVER_STYLE
        return TOOLBUTTON_STYLE

    def sizeHint(self, style_options, model_index):
        return QtCore.QSize((self.__view.width() / 2) - 8, self.ICON_SIZE.height() + 6)
