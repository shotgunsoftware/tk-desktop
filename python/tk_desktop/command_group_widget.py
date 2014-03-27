# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from PySide import QtGui
from PySide import QtCore

from .ui import resources_rc


class GroupWidget(QtGui.QFrame):
    """ Widget with a collapsable header and a blank center widget """
    def __init__(self, title, parent=None):
        """ Constructor """
        QtGui.QFrame.__init__(self, parent)

        self.title = title

        # Cache the icons used by the expand/unexpand button
        self.down_arrow = QtGui.QIcon(":res/down_arrow.png")
        self.right_arrow = QtGui.QIcon(":res/right_arrow.png")

        # Set default styling
        self.setStyleSheet("""
            border: 1px solid gray;
            border-top: none;
            border-left: none;
            border-right: none;
            background-color: transparent;
        """)

        # Add button to expand collapse widget
        self.expand_button = QtGui.QPushButton(self.down_arrow, title)
        self.expand_button.setFlat(True)
        self.expand_button.setStyleSheet("""
            text-align: left;
            font-size: 14px;
            background-color: transparent;
            border: none;
        """)

        # The container for the app widgets
        self.widget = QtGui.QWidget(self)

        # Configure the layout for the group
        group_layout = QtGui.QVBoxLayout()
        group_layout.setSpacing(0)
        group_layout.addWidget(self.expand_button)
        group_layout.addWidget(self.widget)
        self.setLayout(group_layout)

        def toggle_group():
            if self.widget.isHidden():
                self.widget.show()
                self.expand_button.setIcon(self.down_arrow)
            else:
                self.widget.hide()
                self.expand_button.setIcon(self.right_arrow)
        self.expand_button.clicked.connect(toggle_group)

    def hide_header(self):
        self.expand_button.hide()

    def show_header(self):
        self.expand_button.show()


class CommandGroupWidget(GroupWidget):
    """ Widget with a collapsable header that hosts command buttons """

    APP_COLUMN_COUNT = 2  # how many columns to layout the buttons in

    # signal emitted when a command is triggered.
    # the argument is the command_name associated with the command
    command_triggered = QtCore.Signal(str)

    def __init__(self, title, parent=None):
        """ Constructor """
        GroupWidget.__init__(self, title, parent)

        # Keep track of buttons by title so multiple commands can be added
        self.buttons = {}

        # Configure the layout for the commands
        self.app_layout = QtGui.QGridLayout()
        self.app_layout.setHorizontalSpacing(0)
        self.app_layout.setVerticalSpacing(0)
        self.app_layout.setContentsMargins(0, 10, 0, 0)
        self.widget.setLayout(self.app_layout)

    def finalize(self):
        """ Called when all the commands have been added to the group. """
        # need to make sure that there are the appropriate number of columns
        columns = self.app_layout.columnCount()
        if columns < self.APP_COLUMN_COUNT:
            for column in xrange(columns, self.APP_COLUMN_COUNT):
                self.app_layout.addWidget(QtGui.QWidget(), 0, column)

    def add_command(self, command_name, button_title, menu_title, icon=None):
        button = self.buttons.get(button_title)

        if button is None:
            button = QtGui.QToolButton()
            button.setText(button_title)
            button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
            button.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
            if icon is not None:
                button.setIcon(icon)
            self.buttons[button_title] = button

            button.setIconSize(QtCore.QSize(42, 42))
            # button.setFlat(True)
            button.setStyleSheet("""
                QToolButton {
                    text-align: left;
                    font-size: 14px;
                    border: none;
                    padding: 5px;
                    padding-right: 20px;
                }

                QToolButton::menu-arrow:!hover {
                    image:none;
                }

                QToolButton:hover {
                    background-color: rgb(32, 32, 32);
                }

                QToolButton::menu-button  {
                    border: none;
                    width: 20px;
                }
            """)

            # handle button clicks
            button.clicked.connect(lambda: self.command_triggered.emit(command_name))

            # find out where the button goes
            # based off of current widget count
            (row, column) = divmod(self.app_layout.count(), self.APP_COLUMN_COUNT)
            self.app_layout.addWidget(button, row, column, QtCore.Qt.AlignLeft)

        # Add this command to the button's menu
        if menu_title is not None:
            menu = button.menu()
            if menu is None:
                menu = QtGui.QMenu()
                button.setMenu(menu)
                button.setPopupMode(button.MenuButtonPopup)

                # need to reapply style sheet
                button.style().unpolish(button)
                button.style().polish(button)
                button.update()

            action = menu.addAction(menu_title)
            action.triggered.connect(lambda: self.command_triggered.emit(command_name))
