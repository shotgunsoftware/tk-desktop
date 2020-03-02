from __future__ import print_function

if __name__ == "__main__":
    import sgtk

    importer = sgtk.util.qt_importer.QtImporter()
    sgtk.platform.qt.QtGui = importer.QtGui
    sgtk.platform.qt.QtCore = importer.QtCore

    app = sgtk.platform.qt.QtGui.QApplication([])


from sgtk.platform.qt import QtCore, QtGui
import datetime

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


class SortedMenu(QtGui.QMenu):
    pass


class RecentButton(QtGui.QPushButton):
    ICON_SIZE = QtCore.QSize(50, 50)
    MARGIN = 5
    SPACING = 5
    SIZER_LABEL = None

    action_clicked = QtCore.Signal(str)

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
            lambda checked: self.action_clicked.emit(self._command_name)
        )

    @property
    def name(self):
        return six.ensure_str(self.text())

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

    action_clicked = QtCore.Signal(str)

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
            lambda checked: self.action_clicked.emit(self._default_command_name)
        )

        self._menu = SortedMenu(self)
        self._is_menu_empty = True
        self._button_name = button_name

        def cleanup():
            self.setAttribute(
                QtCore.Qt.WA_UnderMouse,
                self.rect().contains(self.mapFromGlobal(QtGui.QCursor.pos())),
            )

        self._menu.aboutToHide.connect(cleanup)

    @property
    def button_name(self):
        self._button_name

    def _set_default(self, command_name, tooltip, icon):
        self._default_command_name = command_name
        self.setToolTip(tooltip)
        self.setIcon(QtGui.QIcon(icon))

    def add_command(self, command_name, menu_name, icon, tooltip, is_menu_default):
        if is_menu_default:
            self._set_default(command_name, tooltip, icon)
            menu_name = menu_name + "*"

        action = self._menu.addAction(menu_name)
        action.setToolTip(tooltip)
        action.triggered.connect(lambda action: self.action_clicked.emit(command_name))

        if self._is_menu_empty:
            self._is_menu_empty = False
        else:
            self.setPopupMode(self.MenuButtonPopup)
            self.setMenu(self._menu)

    def sizeHint(self):
        hint = QtCore.QSize((self.parent().width() / 2) - 20, ICON_SIZE.height() + 8)
        return hint


class RecentList(QtGui.QWidget):

    action_clicked = QtCore.Signal(str)
    MAX_RECENTS = 6

    def __init__(self, parent):
        super(RecentList, self).__init__(parent)
        self._layout = QtGui.QHBoxLayout(self)
        self.setLayout(self._layout)
        self._layout.addStretch(1)

    def add_command(self, command_name, button_name, icon, tooltip, timestamp):
        for insert_pos, button in enumerate(self.buttons):
            # This button already exist. Make it the first button!
            if button.command_name == command_name:
                self._layout.removeWidget(button)
                self._layout.insertWidget(0, button)
                return
            elif timestamp < button.timestamp:
                break
        else:
            insert_pos = 0

        button = RecentButton(self, command_name, button_name, icon, tooltip, timestamp)
        button.action_clicked.connect(self.action_clicked)
        self._layout.insertWidget(insert_pos, button)

        if self._layout.count() > self.MAX_RECENTS + 1:
            self._layout.takeAt(self.MAX_RECENTS).widget().deleteLater()

    @property
    def buttons(self):
        for i in range(self._layout.count() - 1):
            yield self._layout.itemAt(i).widget()


class CommandList(QtGui.QWidget):

    action_clicked = QtCore.Signal(str)

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
            self._buttons[button_name].action_clicked.connect(self.action_clicked)

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

    action_clicked = QtCore.Signal(str)

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

        self._list.action_clicked.connect(self.action_clicked)

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


def _find_or_insert_in_layout(layout, interval, name, factory, first=0):
    interval = list(interval)
    for i in interval:
        # We haven't reached the group yet!
        current_group = layout.itemAt(i).widget()
        if current_group.name < name:
            # keep searching
            continue
        elif current_group.name > name:
            # We just passed by the widget!
            current_group = factory()
            layout.insertWidget(i, current_group, alignment=QtCore.Qt.AlignTop)
        break
    else:
        current_group = factory()
        layout.insertWidget(first, current_group, alignment=QtCore.Qt.AlignTop)

    return current_group


class CommandsView(QtGui.QWidget):

    action_clicked = QtCore.Signal(str)

    def __init__(self, parent):
        super(CommandsView, self).__init__(parent)
        self.setObjectName("project_recent_commands_cache")
        self._layout = QtGui.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self._layout.addStretch(1)
        self._recents_widget = None
        self._recents = {}
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self._show_recents = False

        if parent:
            filter = ResizeEventFilter(parent)
            filter.resized.connect(self._on_parent_resized)
            parent.installEventFilter(filter)

        self.action_clicked.connect(self._update_recents_list)

        # Caches the information about all commands so we can
        # retrieve it when updating recents
        self._recent_commands_cache = {}

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
        self._load_recents()

    def clear(self):
        self._recent_commands_cache = []
        self._recents = {}
        self._recents_widget = None

        while self.layout().count() > 0:
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _update_recents_list(self, command_name):
        print(command_name)
        self._recents[command_name] = {
            "timestamp": datetime.datetime.utcnow(),
            "added": False,
        }
        self._refresh_recent_list(command_name)

    def _refresh_recent_list(self, command_name):
        # if action in recent list.
        if self._recents_widget is None:
            self._recents_widget = RecentSection("Recent")
            self._recents_widget.action_clicked.connect(self.action_clicked)
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
            current_group = _find_or_insert_in_layout(
                self._layout,
                self._section_range(),
                group_name,
                lambda: self._command_section_factory(group_name),
                first=1 if self._recents_widget else 0,
            )
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

    def _command_section_factory(self, group_name):
        section = CommandSection(group_name)
        section.action_clicked.connect(self.action_clicked)
        return section

    def _section_range(self):
        if self._recents_widget:
            return range(1, self._layout.count() - 1)
        else:
            return range(self._layout.count() - 1)

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
        self.parent()._save_setting(key, recents, site_specific=True)

    def _load_recents(self):
        """
        Loads recently launched apps from the user settings and returns them in a dict. See above
        for the format.
        """
        key = "project_recent_apps.%d" % self._current_project["id"]
        self._recents = self.parent()._load_setting(key, None, True) or {}


class ResizeEventFilter(QtCore.QObject):
    """
    Event filter which emits a resized signal whenever
    the monitored widget resizes. This is so that the overlay wrapper
    class can be informed whenever the Widget gets a resize event.
    """

    resized = QtCore.Signal()

    def eventFilter(self, obj, event):
        # peek at the message
        if event.type() == QtCore.QEvent.Resize:
            # re-broadcast any resize events
            self.resized.emit()
        # pass it on!
        return False


if __name__ == "__main__":

    scrollarea = QtGui.QScrollArea()
    scrollarea.resize(427, 715)

    CommandsView._load_recents = lambda self: None
    CommandsView._store_recents = lambda self: None
    RecentList.MAX_RECENTS = 3
    view = CommandsView(scrollarea)
    scrollarea.setWidget(view)
    # view._recents = [
    #     {
    #         "nuke_studio_120": {
    #             "timestamp": datetime.datetime.now(),
    #             "added": True
    #         },
    #         "maya2019": {
    #             "timestamp": datetime.datetime.now(),
    #             "added": True
    #         }
    #     }
    # ]

    view.set_project(None, ["Creative Tools", "Editorial Tools", "Automotive Tools"])

    commands = [
        (
            "Nuke Studio 12.0",
            "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
            "tooltip nuke 12.0",
            ["Creative Tools"],
            True,
        ),
        (
            "NukeX 12.5",
            "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
            "tooltip nuke 12.0",
            ["Creative Tools"],
            True,
        ),
        (
            "NukeX 12.0",
            "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
            "tooltip nuke 12.0",
            ["Creative Tools"],
            False,
        ),
        (
            "Nuke Assist 12.0",
            "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
            "tooltip nuke 12.0",
            ["Creative Tools"],
            True,
        ),
        (
            "Maya 2019",
            "/Users/boismej/gitlocal/tk-maya/icon_256.png",
            "tooltip maya 2019",
            ["Creative Tools"],
            True,
        ),
        (
            "Maya 2020",
            "/Users/boismej/gitlocal/tk-maya/icon_256.png",
            "tooltip maya 2020",
            ["Creative Tools"],
            False,
        ),
    ]

    commands = [
        (
            cmd[0].lower().replace(" ", "_").replace(".", ""),
            cmd[0].rsplit(" ", 1)[0],
            cmd[0],
            cmd[1],
            cmd[2],
            cmd[3],
            cmd[4],
        )
        for cmd in commands
    ]

    if False:

        def add_button():
            command = commands.pop(0)
            view.add_command()
            if commands:
                QtCore.QTimer.singleShot(500, add_button)
            else:
                import subprocess

                # subprocess.Popen(["python", "-c", "from PySide2 import QtWidgets; QtWidgets.QApplication([]).exec_()"])

        QtCore.QTimer.singleShot(3000, add_button)
    else:
        for cmd in commands:
            view.add_command(*cmd)

    scrollarea.show()

    app.exec_()
