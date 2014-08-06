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

from tank.platform.qt import QtCore, QtGui

from .ui import resources_rc

import sgtk

from .project_commands_model import ProjectCommandModel

shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "shotgun_view")

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
    ICON_SIZE = QtCore.QSize(50, 50)
    MARGIN = 5
    SPACING = 5
    SIZER_LABEL = None

    def __init__(self, view):
        AbstractCommandDelegate.__init__(self, view)

        if self.SIZER_LABEL is None:
            # setup a label that we will use to get height
            self.SIZER_LABEL = QtGui.QLabel()
            self.SIZER_LABEL.setWordWrap(True)
            self.SIZER_LABEL.setScaledContents(True)
            self.SIZER_LABEL.setAlignment(QtCore.Qt.AlignHCenter)

    def _create_button(self, parent):
        button = QtGui.QPushButton(parent)
        button.setFlat(True)

        layout = QtGui.QVBoxLayout(button)
        layout.setSpacing(self.SPACING)
        layout.setContentsMargins(self.SPACING, self.SPACING, self.SPACING, self.SPACING)

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

        button.setFocusPolicy(QtCore.Qt.NoFocus)

        return button

    def _text_for_item(self, item):
        button_name = item.data(ProjectCommandModel.BUTTON_NAME_ROLE)
        menu_name = item.data(ProjectCommandModel.MENU_NAME_ROLE)
        if menu_name is None:
            return button_name
        else:
            return "%s\n%s" % (button_name, menu_name)

    def _configure_widget(self, widget, item, style_options):
        text_label = widget.layout().itemAt(1).widget()
        text_label.setText(self._text_for_item(item))

        icon_label = widget.layout().itemAt(0).widget()
        icon = item.data(QtCore.Qt.DecorationRole)
        if icon is None:
            icon_label.setPixmap(QtGui.QIcon().pixmap(self.ICON_SIZE))
        else:
            icon_label.setPixmap(icon.pixmap(self.ICON_SIZE))

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

    def sizeHint(self, style_options, model_index):
        # get the height from the sizer label
        (_, item, _) = self._source_for_index(model_index)
        self.SIZER_LABEL.setText(self._text_for_item(item))
        text_height = self.SIZER_LABEL.heightForWidth(self.ICON_SIZE.width() + 2*self.MARGIN)

        # height is icon + text + top spacing + bottom spacing + space between
        height = self.ICON_SIZE.height() + text_height + (3 * self.SPACING)
        return QtCore.QSize(self.ICON_SIZE.width() + 2*self.MARGIN, height)


class ProjectCommandDelegate(AbstractCommandDelegate):
    ICON_SIZE = QtCore.QSize(50, 50)

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
        widget.setFocusPolicy(QtCore.Qt.NoFocus)
        return widget

    def _configure_widget(self, widget, item, style_options):
        # update button text
        widget.setText(" %s" % item.data(ProjectCommandModel.BUTTON_NAME_ROLE))

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
        # borrowed from qtwidgets framework's thumb_widget
        p = QtGui.QPalette()
        highlight_col = p.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight)

        border = "rgb(%s, %s, %s)" % (highlight_col.red(), highlight_col.green(), highlight_col.blue())
        background = "rgba(%s, %s, %s, 25%%)" % (highlight_col.red(), highlight_col.green(), highlight_col.blue())

        if selected:
            return HOVER_STYLE % (border, background)
        return REGULAR_STYLE

    def sizeHint(self, style_options, model_index):
        return QtCore.QSize((self.__view.width() / 2) - 20, self.ICON_SIZE.height() + 8)
