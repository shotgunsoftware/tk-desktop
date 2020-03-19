# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import functools

from sgtk.platform.qt import QtCore, QtGui
from tank_vendor import six

from .shared import ICON_SIZE, BUTTON_STYLE


class CommandButton(QtGui.QToolButton):

    command_triggered = QtCore.Signal(str)

    def __init__(self, parent, command_name, button_name, icon, tooltip):
        super(CommandButton, self).__init__(parent)
        self.setSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding
        )
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setIconSize(ICON_SIZE)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.setStyleSheet(BUTTON_STYLE)

        self.setText(" %s" % button_name)
        self._set_default(command_name, tooltip, icon)
        self.clicked.connect(
            lambda: self.command_triggered.emit(
                six.ensure_str(self._default_command_name)
            )
        )
        self._actions = []

        self._menu = QtGui.QMenu(self)
        self._is_menu_empty = True
        self._button_name = button_name
        # The data of an action contains the command name.
        self._menu.triggered.connect(
            lambda action: self.command_triggered.emit(six.ensure_str(action.data()))
        )

        def cleanup():
            self.setAttribute(
                QtCore.Qt.WA_UnderMouse,
                self.rect().contains(self.mapFromGlobal(QtGui.QCursor.pos())),
            )

        self._menu.aboutToHide.connect(cleanup)

    @property
    def name(self):
        return self._button_name

    def _set_default(self, command_name, tooltip, icon):
        self._default_command_name = command_name
        self.setToolTip(tooltip)
        self.setIcon(QtGui.QIcon(icon))

    def add_command(self, command_name, menu_name, icon, tooltip, is_menu_default):
        if is_menu_default:
            self._set_default(command_name, tooltip, icon)
            action_name = menu_name + "*"
        else:
            action_name = menu_name

        # QMenu doesn't support insertion of an action in the middle of the menu
        # so we'll recreate the items every single time one is added.
        self._menu.clear()

        # Keep track of the new item being added.
        self._actions.append((command_name, menu_name, action_name, tooltip))

        # For all actions on the menu name
        for command_name, _, action_name, tooltip in sorted(
            self._actions, key=functools.cmp_to_key(self._compare_menu_actions)
        ):
            action = self._menu.addAction(action_name)
            action.setToolTip(tooltip)
            action.setData(command_name)

        if len(self._menu.actions()) > 1:
            # If there is more than one available item in the menu
            # show the menu.
            self.setPopupMode(self.MenuButtonPopup)
            self.setMenu(self._menu)

    def _compare_menu_actions(self, lhs, rhs):
        # extract the action name so we can sort based on that.
        lhs = lhs[2]
        rhs = rhs[2]

        # The default action, denoted by a * in the menu, is always at the top.
        # Everything else is sorted alphabetically.
        if "*" in lhs:
            return -1
        elif "*" in rhs:
            return 1
        elif lhs < rhs:
            return -1
        elif lhs > rhs:
            return 1
        else:
            return 0

    def sizeHint(self):
        hint = QtCore.QSize((self.parent().width() / 2) - 20, ICON_SIZE.height() + 8)
        return hint
