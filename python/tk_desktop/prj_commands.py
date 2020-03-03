# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from __future__ import print_function

from sgtk.platform.qt import QtCore, QtGui
from tank_vendor import six
import datetime
import functools

p = QtGui.QPalette()
highlight_col = p.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight)

border = "rgb(%s, %s, %s)" % (
    highlight_col.red(),
    highlight_col.green(),
    highlight_col.blue(),
)
background = "rgba(%s, %s, %s, 25%%)" % (
    highlight_col.red(),
    highlight_col.green(),
    highlight_col.blue(),
)


COMMAND_STYLE = """
QToolButton {
    font-size: 15px;
}

QToolButton::menu-button  {
    border: none;
    width: 30px;
}

QPushButton, QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
}

QPushButton:hover, QToolButton:hover {
    border: 1px solid %s;
    background-color: %s;
}

QPushButton:pressed, QToolButton:pressed {
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);
}

QToolButton::menu-arrow:!hover { image:none; }


""" % (
    border,
    background,
)


class DefaultGroupingHeader(QtGui.QPushButton):
    """ Default widget for a group header """

    def __init__(self, parent=None):
        QtGui.QPushButton.__init__(self, parent)

        # cache the icons for collapsed/expanded
        self.down_arrow = QtGui.QIcon(
            "/Users/boismej/gitlocal/tk-desktop/resources/down_arrow.png"
        )
        self.right_arrow = QtGui.QIcon(
            "/Users/boismej/gitlocal/tk-desktop/resources/right_arrow.png"
        )

        # adjust the button look
        self.setFlat(True)
        self.setCheckable(True)
        self.setChecked(True)
        self.setStyleSheet(
            """
            text-align: left;
            font-size: 14px;
            background-color: transparent;
            border: none;
        """
        )

        # default is to be expanded
        self.set_expanded(True)

    def set_expanded(self, is_expanded):
        """ Set the widget to be expanded or collapsed """
        if is_expanded:
            self.setIcon(self.down_arrow)
        else:
            self.setIcon(self.right_arrow)


ICON_SIZE = QtCore.QSize(50, 50)


class RecentButton(QtGui.QPushButton):
    ICON_SIZE = QtCore.QSize(50, 50)
    MARGIN = 5
    SPACING = 5
    SIZER_LABEL = None

    command_triggered = QtCore.Signal(str)

    def __init__(self, parent, command_name, button_name, icon, tooltip, timestamp):
        super(RecentButton, self).__init__(parent)

        self.setFlat(True)

        layout = QtGui.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter)
        layout.setSpacing(self.SPACING)
        layout.setContentsMargins(
            self.SPACING, self.SPACING, self.SPACING, self.SPACING
        )

        self._timestamp = timestamp

        self.icon_label = QtGui.QLabel(self)
        self.icon_label.setAlignment(QtCore.Qt.AlignHCenter)
        self.layout().addWidget(self.icon_label, QtCore.Qt.AlignHCenter)

        self.text_label = QtGui.QLabel(parent)
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(QtCore.Qt.AlignHCenter)
        self.layout().addWidget(self.text_label, QtCore.Qt.AlignHCenter)

        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet(COMMAND_STYLE)

        self.text_label.setText(button_name)
        if icon is None:
            self.icon_label.setPixmap(QtGui.QIcon().pixmap(self.ICON_SIZE))
        else:
            self.icon_label.setPixmap(QtGui.QIcon(icon).pixmap(self.ICON_SIZE))

        self._command_name = command_name

        self.clicked.connect(
            lambda checked: self.command_triggered.emit(
                six.ensure_str(self._command_name)
            )
        )

    @property
    def name(self):
        return six.ensure_str(self.text_label.text())

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def command_name(self):
        return self._command_name

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
        return QtCore.QSize(width + 2 * cls.MARGIN, height)

    def sizeHint(self):
        # get the text size from the sizer label
        text = self.text_label.text()
        full_size = self.size_for_text(text)

        # see if the model has a limit on recents
        # limiting the number of recents, each one gets equal spacing
        # the spacing is the width of the view, without the spacing
        # divided up equally
        limit = 6
        space_to_divide = (
            self.parent().width() - (self.SPACING * (limit + 1)) - self.MARGIN
        )
        width = space_to_divide / limit
        return QtCore.QSize(width, full_size.height())


class CommandButton(QtGui.QToolButton):

    command_triggered = QtCore.Signal(str)

    def __init__(self, parent, command_name, button_name, icon, tooltip):
        super(CommandButton, self).__init__(parent)
        self.setSizePolicy(
            QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.MinimumExpanding
        )
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setIconSize(ICON_SIZE)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.setStyleSheet(COMMAND_STYLE)

        self.setText(" %s" % button_name)
        self._set_default(command_name, tooltip, icon)
        self.clicked.connect(
            lambda checked: self.command_triggered.emit(
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
        for command_name, _, action_name, tooltip in sorted(self._actions):
            action = self._menu.addAction(action_name)
            action.setToolTip(tooltip)
            action.setData(command_name)

        if len(self._menu.actions()) > 1:
            # If there is more than one available item in the menu
            # show it.
            self.setPopupMode(self.MenuButtonPopup)
            self.setMenu(self._menu)

    def sizeHint(self):
        hint = QtCore.QSize((self.parent().width() / 2) - 20, ICON_SIZE.height() + 8)
        return hint


class RecentList(QtGui.QWidget):

    command_triggered = QtCore.Signal(str)
    MAX_RECENTS = 6

    def __init__(self, parent):
        super(RecentList, self).__init__(parent)
        self._layout = QtGui.QHBoxLayout(self)
        self.setLayout(self._layout)
        self._layout.addStretch(1)

    def add_command(self, command_name, button_name, icon, tooltip, timestamp):
        buttons = list(self.buttons)

        # If we do not have any buttons, simply insert at the beginning.
        if not buttons:
            insert_pos = 0
        else:
            # If we do have something, search for where to insert the
            # button.
            for insert_pos, button in enumerate(buttons):
                # This button already exist. Make it the first button!
                if button.command_name == command_name:
                    self._layout.removeWidget(button)
                    self._layout.insertWidget(0, button)
                    return
                # The timestamp of this command is earlier that the current
                # button, so we'll insert here.
                elif timestamp >= button.timestamp:
                    break
            else:
                # We haven't found anything, so we'll insert one past the
                # last button in the UI.
                insert_pos += 1

        if insert_pos >= self.MAX_RECENTS:
            return

        button = RecentButton(self, command_name, button_name, icon, tooltip, timestamp)
        button.command_triggered.connect(self.command_triggered)
        self._layout.insertWidget(insert_pos, button)

        if (self._layout.count() - 1) > self.MAX_RECENTS:
            self._layout.takeAt(self.MAX_RECENTS).widget().deleteLater()

    @property
    def buttons(self):
        for i in range(self._layout.count() - 1):
            yield self._layout.itemAt(i).widget()


class CommandList(QtGui.QWidget):

    command_triggered = QtCore.Signal(str)

    def __init__(self, parent):
        super(CommandList, self).__init__(parent)

        self._layout = QtGui.QGridLayout(self)
        self.setLayout(self._layout)
        self._filler = QtGui.QWidget(self)
        self._buttons = {}

    def add_command(
        self, command_name, button_name, menu_name, icon, tooltip, is_menu_default
    ):
        if button_name not in self._buttons:

            for btn in self._buttons:
                self._layout.removeWidget(self._buttons[btn])
            self._layout.removeWidget(self._filler)

            self._layout.update()
            self._buttons[button_name] = CommandButton(
                self, command_name, button_name, icon, tooltip
            )
            self._buttons[button_name].command_triggered.connect(self.command_triggered)

            for idx, name in enumerate(sorted(self._buttons)):
                column = idx % 2
                row = idx // 2
                self._layout.addWidget(self._buttons[name], row, column)

            # if last column inserted was the first one, then add a filler so the grid
            # doesn't space the button.
            if column == 0:
                self._layout.addWidget(self._filler, row, column + 1)

        if menu_name is not None:
            self._buttons[button_name].add_command(
                command_name, menu_name, icon, tooltip, is_menu_default
            )

    @property
    def buttons(self):
        for i in range(len(self._buttons)):
            yield self._layout.itemAt(i).widget()


class Section(QtGui.QWidget):

    command_triggered = QtCore.Signal(str)

    def __init__(self, name, WidgetListFactory):
        super(Section, self).__init__(parent=None)

        self._layout = QtGui.QVBoxLayout(self)
        self.setLayout(self._layout)

        self._name = name

        self._grouping = DefaultGroupingHeader()
        self._grouping.setText(name.upper())
        self._layout.addWidget(self._grouping)

        self._list = WidgetListFactory(self)
        self._layout.addWidget(self._list)
        self._grouping.toggled.connect(self._toggled)

        self._line = QtGui.QFrame()
        self._line.setFrameShape(QtGui.QFrame.HLine)
        self._line.setStyleSheet(
            "background-color: transparent; color: rgb(30, 30, 30);"
        )
        self._line.setMidLineWidth(2)
        self._layout.addWidget(self._line)

        margins = self._layout.contentsMargins()
        margins.setTop(0)
        margins.setBottom(0)
        self._layout.setContentsMargins(margins)

        self._list.command_triggered.connect(self.command_triggered)

    @property
    def name(self):
        return self._name

    def _toggled(self, checked):
        self._grouping.set_expanded(checked)
        self._list.setVisible(checked)

    def sizeHint(self):
        # size is the parent width and height fixed to the margins
        return QtCore.QSize(self.parent().width(), 50)


class RecentSection(Section):
    def __init__(self, name):
        super(RecentSection, self).__init__(name, RecentList)

    def add_command(self, command_name, button_name, icon, tooltip, timestamp):
        self._list.add_command(command_name, button_name, icon, tooltip, timestamp)


class CommandSection(Section):
    def __init__(self, name):
        super(CommandSection, self).__init__(name, CommandList)

    def add_command(
        self, command_name, button_name, menu_name, icon, tooltip, is_menu_default
    ):
        self._list.add_command(
            command_name, button_name, menu_name, icon, tooltip, is_menu_default
        )

    @property
    def buttons(self):
        return self._list.buttons


class CommandsView(QtGui.QWidget):

    command_triggered = QtCore.Signal(str)

    def __init__(self, parent, settings):
        super(CommandsView, self).__init__(parent)
        self.setObjectName("project_recent_commands_cache")
        self._layout = QtGui.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self._layout.addStretch(1)
        self._recents_widget = None
        self._recents = {}
        self._groups = []
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self._show_recents = False

        # if parent:
        #     filter = ResizeEventFilter(parent)
        #     filter.resized.connect(self._on_parent_resized)
        #     parent.installEventFilter(filter)

        self.command_triggered.connect(self._update_recents_list)

        # Caches the information about all commands so we can
        # retrieve it when updating recents
        self._recent_commands_cache = {}

        self._settings = settings

    def _on_parent_resized(self):
        """
        Special slot hooked up to the event filter.
        When associated widget is resized this slot is being called.
        """
        # resize overlay
        self.resize(self.parentWidget().size())

    def set_project(self, current_project, groups, show_recents=True):
        self._current_project = current_project
        self._show_recents = show_recents
        self._groups = groups
        self._load_recents()

    def clear(self):
        self._recent_commands_cache = {}
        self._recents = {}
        self._recents_widget = None

        if self._recents_widget:
            self.layout().removeWidget(self._recents_widget)
            self._recents_widget.deleteLater()
            self._recents_widget = None

        # Remove all the sections. Create a copy of the list
        # buttons so we don't iterate and modify the list at the
        # same time.
        for section in list(self.sections):
            self.layout().removeWidget(section)
            section.deleteLater()

        # There should be only one item left, the stretcher.
        assert self.layout().count() == 1

    def _update_recents_list(self, command_name):
        self._recents[command_name] = {
            "timestamp": datetime.datetime.utcnow(),
            # This is present for backwards compatibility with
            # previous version of desktop. we do not actually use this
            # value for this implementation.
            "added": False,
        }
        self._store_recents()
        self._refresh_recent_list(command_name)

    def _refresh_recent_list(self, command_name):
        # if action in recent list.
        if self._recents_widget is None:
            self._recents_widget = RecentSection("Recent")
            self._recents_widget.command_triggered.connect(self.command_triggered)
            self._layout.insertWidget(0, self._recents_widget)

        timestamp = self._recents[command_name]["timestamp"]
        command = self._recent_commands_cache[command_name]

        self._recents_widget.add_command(
            command_name,
            command["menu_name"],
            command["icon"],
            command["tooltip"],
            timestamp,
        )

    def add_command(
        self,
        command_name,
        button_name,
        menu_name,
        icon,
        tooltip,
        groups,
        is_menu_default=False,
    ):
        for group_name in groups:
            # Search for the requested group.
            current_group = self._find_or_insert_section(group_name)
            current_group.add_command(
                command_name, button_name, menu_name, icon, tooltip, is_menu_default
            )
            # Caches information about the command so that if it is a recent
            self._recent_commands_cache[command_name] = {
                "menu_name": menu_name,
                "icon": icon,
                "tooltip": tooltip,
            }
        if self._show_recents and command_name in self._recents:
            self._refresh_recent_list(command_name)

    @property
    def recents_visible(self):
        return bool(self._recents_widget)

    @property
    def sections(self):
        if self._recents_widget:
            first_section = 1
        else:
            first_section = 0

        for i in range(first_section, self._layout.count() - 1):
            yield self._layout.itemAt(i).widget()

    def _find_or_insert_section(self, group_name):
        if group_name not in self._groups:
            raise RuntimeError(
                "Unknown group %s. Expecting one of %s" % (group_name, self._groups)
            )
        # Due to visual glitches in PySide1, we're inserting sections as we need them
        # instead of creating them all hidden up front.
        # Skip over the recent widgets.
        if self._recents_widget:
            first_group_index = 1
        else:
            first_group_index = 0

        # First, generate a collection of sections and their indices
        name_to_pos = {section.name: idx for idx, section in enumerate(self.sections)}

        print("Searching for", group_name, "in", list(name_to_pos))
        # If the section already exists.
        if group_name in name_to_pos:
            print("Section already exists!")
            return self._layout.itemAt(
                first_group_index + name_to_pos[group_name]
            ).widget()

        # The section does not exist!

        # Let's the following groups are configured: A, B, C and D.
        # We currently have groups C and D and we now want to insert B.
        # Since we'll be using insertWidget, which inserts a widget right
        # before another, we'll look for the first that we know that comes
        # after B.

        # Find the groups after the one we're searching for (B in the above example).
        idx = self._groups.index(group_name)
        groups_after = self._groups[idx + 1 :]

        # Loop over the remaining groups (C and D in the above example)
        for group_after in groups_after:
            # If that group exists, we've found where we'll insert the group!
            if group_after in name_to_pos:
                print("Inserting before", group_after)
                insert_position = name_to_pos[group_after]
                break
        else:
            # We haven't found any of the groups that come after the one
            # we want to insert, which means we'll have to insert right before
            # the stretch item.
            print("Inserting at the end.")
            insert_position = len(name_to_pos)

        print("Inserting at position %s" % (insert_position + first_group_index))
        new_group = CommandSection(group_name)
        new_group.command_triggered.connect(self.command_triggered)
        self._layout.insertWidget(
            insert_position + first_group_index, new_group, alignment=QtCore.Qt.AlignTop
        )

        return new_group

    def _store_recents(self):
        """
        Stores a list of recently launched apps in the user settings. Resets the "added" key so
        when the settings are loaded again, each item will be added to the list. They are stored as
        a dictionary in the following format::

            self._recents = {
                'launch_nuke': {
                    'timestamp': datetime.datetime(2016, 5, 20, 21, 48, 17, 495234),
                    'added': False},
                ...
            }
        """
        recents = {}
        for name, details in self._recents.items():
            recents[name] = {"timestamp": details["timestamp"], "added": False}
        key = "project_recent_apps.%d" % self._current_project["id"]
        self._settings.save(key, recents)

    def _load_recents(self):
        """
        Loads recently launched apps from the user settings and returns them in a dict. See above
        for the format.
        """
        key = "project_recent_apps.%d" % self._current_project["id"]
        self._recents = self._settings.load(key) or {}


# class ResizeEventFilter(QtCore.QObject):
#     """
#     Event filter which emits a resized signal whenever
#     the monitored widget resizes. This is so that the overlay wrapper
#     class can be informed whenever the Widget gets a resize event.
#     """

#     resized = QtCore.Signal()

#     def eventFilter(self, obj, event):
#         # peek at the message
#         if event.type() == QtCore.QEvent.Resize:
#             # re-broadcast any resize events
#             self.resized.emit()
#         # pass it on!
#         return False


# if __name__ == "__main__":

#     scrollarea = QtGui.QScrollArea()
#     scrollarea.resize(427, 715)

#     class ProjectCommandSettings(object):
#         def save(self, key, recents):
#             pass

#         def load(self, key):
#             return {
#                 "nuke_studio_120": {
#                     "timestamp": datetime.datetime(2008, 1, 1),
#                     "added": True,
#                 },
#                 "maya_2019": {
#                     "timestamp": datetime.datetime(2005, 1, 1),
#                     "added": True,
#                 },
#             }

#     RecentList.MAX_RECENTS = 3
#     view = CommandsView(scrollarea, ProjectCommandSettings())
#     scrollarea.setWidget(view)

#     view.set_project(
#         {"type": "Project", "id": 61},
#         ["Creative Tools", "Editorial Tools", "Automotive Tools"],
#     )

#     commands = [
#         (
#             "Nuke Studio 12.0",
#             "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
#             "tooltip nuke 12.0",
#             ["Creative Tools"],
#             True,
#         ),
#         (
#             "NukeX 12.5",
#             "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
#             "tooltip nuke 12.0",
#             ["Creative Tools"],
#             True,
#         ),
#         (
#             "NukeX 12.0",
#             "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
#             "tooltip nuke 12.0",
#             ["Creative Tools"],
#             False,
#         ),
#         (
#             "Nuke Assist 12.0",
#             "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
#             "tooltip nuke 12.0",
#             ["Creative Tools"],
#             True,
#         ),
#         (
#             "Maya 2019",
#             "/Users/boismej/gitlocal/tk-maya/icon_256.png",
#             "tooltip maya 2019",
#             ["Creative Tools"],
#             True,
#         ),
#         (
#             "Maya 2020",
#             "/Users/boismej/gitlocal/tk-maya/icon_256.png",
#             "tooltip maya 2020",
#             ["Creative Tools"],
#             False,
#         ),
#     ]

#     commands = [
#         (
#             cmd[0].lower().replace(" ", "_").replace(".", ""),
#             cmd[0].rsplit(" ", 1)[0],
#             cmd[0],
#             cmd[1],
#             cmd[2],
#             cmd[3],
#             cmd[4],
#         )
#         for cmd in commands
#     ]

#     if False:

#         def add_button():
#             command = commands.pop(0)
#             view.add_command()
#             if commands:
#                 QtCore.QTimer.singleShot(500, add_button)
#             else:
#                 import subprocess

#                 # subprocess.Popen(["python", "-c", "from PySide2 import QtWidgets; QtWidgets.QApplication([]).exec_()"])

#         QtCore.QTimer.singleShot(3000, add_button)
#     else:
#         for cmd in commands:
#             view.add_command(*cmd)

#     scrollarea.show()

#     app.exec_()
