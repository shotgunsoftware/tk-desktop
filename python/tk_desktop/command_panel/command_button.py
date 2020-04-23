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

from sgtk.deploy import util

from sgtk.platform.qt import QtCore, QtGui
from tank_vendor import six

from .shared import ICON_SIZE, BUTTON_STYLE


class CommandButton(QtGui.QToolButton):
    """
    A button that allows launching one of many commands.

    When clicking on the button itself, the default command is executed. When clicking
    on the dropdown arrow on the right, a list of all the applications can be launched
    will be displayed.

    The default command will be at the top and a * will be next to its name. If only
    one command is available on the button, the dropdown will not be displayed.
    """

    # Triggered when the button is clicked or a menu action is triggered.
    command_triggered = QtCore.Signal(str)

    def __init__(self, parent, command_name, button_name, icon, tooltip):
        """
        :param parent: Parent widget.
        :param str command_name: Name of the default command to execute.
        :param str button_name: Name of the button.
        :param str icon: Path to the icon.
        :param str tooltip: Tooltip for the button.
        """
        super(CommandButton, self).__init__(parent)
        self.setSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding
        )
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setIconSize(ICON_SIZE)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.setStyleSheet(BUTTON_STYLE)

        self.setText(" %s" % button_name)

        self._set_default(tooltip, icon)

        self._commands = []

        # This menu will implement the drop down behaviour of the tool button.
        self._menu = QtGui.QMenu(self)
        self._button_name = button_name
        # The data of an action contains the command name.
        self._menu.triggered.connect(
            # The .data method returns a unicode string in Python 2, so force it to a utf8 str.
            lambda action: self.command_triggered.emit(six.ensure_str(action.data()))
        )

        # This is a workaround for a PySide2 issue where the hover state of the button
        # is not properly cleared when the menu is dismissed or an action clicked.
        #
        # Inspired by this workaround:
        # https://forum.qt.io/topic/36348/solved-how-do-i-clear-hover-state-on-a-qgraphicswidget-wrapped-qtoolbutton
        def cleanup():
            self.setAttribute(
                QtCore.Qt.WA_UnderMouse,
                # Check if the cursor is still over the widget and set the under mouse
                # property appropriately.
                self.rect().contains(self.mapFromGlobal(QtGui.QCursor.pos())),
            )

        self._menu.aboutToHide.connect(cleanup)

        # Clicking on the button triggers the first action.
        self.clicked.connect(lambda: self._menu.actions()[0].trigger())

    @property
    def name(self):
        """
        Name of the button.
        """
        return self._button_name

    def _set_default(self, tooltip, icon):
        """
        Set the default action when the button is clicked.

        :param str tooltip: Tooltip for the button.
        :param str icon: Path to the icon.
        """
        self.setToolTip(tooltip)
        self.setIcon(QtGui.QIcon(icon))

    def add_command(self, command_name, menu_name, icon, tooltip, is_menu_default):
        """
        Add a command for this button.

        If there is already one command, the button will start displaying a drop down
        to select one of the many command on the button.

        :param str command_name: Name of the command to launch.
        :param str menu_name: Name for the command in the menu dropdown.
        :param str icon: Path of the icon for the menu dropdown.
        :param bool is_menu_default: If True, this command will become the default
            command for the button.
        """

        # Menu name is set when an app returns multiple actions to be put inside a group
        # and gives each of them a different name (e.g. Maya 2018, Maya 2019, Maya 2020).
        # For an app with a single command (e.g. the publisher) there is only a single
        # action (the command_name) and there is no grouping, so the app as no notion
        # of a menu_name for a item in a group and hence we receive an empty menu_name here.
        # Because of this, the default name for the QAction will be the command name.
        #
        # At this point, we can probably guess that there won't be any group under this
        # button as the app doesn't provide menu names for commands, and as such we don't
        # need to create an action under a menu that will only ever contain one action and
        # thus won't be displayed, but this actually makes the code more complex, so we'll
        # simply use the command name as the menu action name.
        if menu_name is None:
            menu_name = command_name

        # The default menu entry is always denoted with a star next to it.
        if is_menu_default:
            for command in self._commands:
                command[-1] = False

        # QMenu doesn't support insertion of an action in the middle of the menu
        # so we'll recreate the items every single time one is added.
        self._menu.clear()

        # Only keep the last default as the default. This can happen when
        # software entities are unproperly registered and multiple
        # defaults are defined.

        # Keep track of the new item being added.
        self._commands.append([command_name, menu_name, tooltip, icon, is_menu_default])

        # For all actions on the menu name
        is_first = True
        for command_name, menu_name, tooltip, icon, _ in sorted(
            self._commands, key=functools.cmp_to_key(self._compare_menu_actions)
        ):
            # Add an asterix to the first item since it is the default.
            if is_first:
                is_first = False
                self._set_default(tooltip, icon)
                menu_name += "*"
            action = self._menu.addAction(menu_name)
            action.setToolTip(tooltip)
            action.setData(command_name)

        # If there is more than one available item in the menu, show it so the
        # user can pick one.
        if len(self._menu.actions()) > 1:
            self.setPopupMode(self.MenuButtonPopup)
            self.setMenu(self._menu)

    def _compare_menu_actions(self, lhs, rhs):
        """
        Compare two menu actions.

        Actions are sorted alphabetically, but the default note, denoted by a *,
        is always at the top.
        """
        # extract the action name so we can sort based on that.
        lhs_action_name = lhs[1]
        rhs_action_name = rhs[1]

        lhs_is_default = lhs[-1]
        rhs_is_default = rhs[-1]

        # The default action, denoted by a * in the menu, is always at the top.
        # Everything else is sorted alphabetically.
        if lhs_is_default:
            return -1
        elif rhs_is_default:
            return 1
        elif util.is_version_newer(lhs_action_name, rhs_action_name):
            return -1
        elif util.is_version_older(lhs_action_name, rhs_action_name):
            return 1
        else:
            return 0

    def sizeHint(self):
        """
        Hint at the button size.

        The button should occupy half the width of the panel and be a bit higher
        than the icon.
        """
        hint = QtCore.QSize((self.parent().width() / 2) - 20, ICON_SIZE.height() + 8)
        return hint
