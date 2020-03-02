if __name__ == "__main__":
    import sys

    sys.path.insert(0, "/Users/boismej/gitlocal/tk-core/python")

    from sgtk.util.qt_importer import QtImporter

    importer = QtImporter()
    QtGui = importer.QtGui
    QtCore = importer.QtCore

    app = QtGui.QApplication([])

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

    # Set the fusion style, which gives us a good base to build on. With
    # this, we'll be sticking largely to the style and won't need to
    # introduce much qss to get a good look.
    app.setStyle("fusion")

    # Build ourselves a dark palette to assign to the application. This
    # will take the fusion style and darken it up.
    palette = QtGui.QPalette()

    # This closely resembles the color palette used in Maya 2017 with a
    # few minor tweaks.
    palette.setBrush(
        QtGui.QPalette.Disabled, QtGui.QPalette.Button, QtGui.QColor(80, 80, 80)
    )
    palette.setBrush(
        QtGui.QPalette.Disabled, QtGui.QPalette.Light, QtGui.QColor(97, 97, 97)
    )
    palette.setBrush(
        QtGui.QPalette.Disabled, QtGui.QPalette.Midlight, QtGui.QColor(59, 59, 59)
    )
    palette.setBrush(
        QtGui.QPalette.Disabled, QtGui.QPalette.Dark, QtGui.QColor(37, 37, 37)
    )
    palette.setBrush(
        QtGui.QPalette.Disabled, QtGui.QPalette.Mid, QtGui.QColor(45, 45, 45)
    )
    palette.setBrush(
        QtGui.QPalette.Disabled, QtGui.QPalette.Base, QtGui.QColor(42, 42, 42)
    )
    palette.setBrush(
        QtGui.QPalette.Disabled, QtGui.QPalette.Window, QtGui.QColor(68, 68, 68)
    )
    palette.setBrush(
        QtGui.QPalette.Disabled, QtGui.QPalette.Shadow, QtGui.QColor(0, 0, 0)
    )
    palette.setBrush(
        QtGui.QPalette.Disabled,
        QtGui.QPalette.AlternateBase,
        palette.color(QtGui.QPalette.Disabled, QtGui.QPalette.Base).lighter(110),
    )
    palette.setBrush(
        QtGui.QPalette.Disabled,
        QtGui.QPalette.Text,
        palette.color(QtGui.QPalette.Disabled, QtGui.QPalette.Base).lighter(250),
    )
    palette.setBrush(
        QtGui.QPalette.Disabled,
        QtGui.QPalette.Link,
        palette.color(QtGui.QPalette.Disabled, QtGui.QPalette.Base).lighter(250),
    )
    palette.setBrush(
        QtGui.QPalette.Disabled,
        QtGui.QPalette.LinkVisited,
        palette.color(QtGui.QPalette.Disabled, QtGui.QPalette.Base).lighter(110),
    )

    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.WindowText, QtGui.QColor(200, 200, 200),
    )
    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.Button, QtGui.QColor(75, 75, 75)
    )
    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.ButtonText, QtGui.QColor(200, 200, 200),
    )
    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.Light, QtGui.QColor(97, 97, 97)
    )
    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.Midlight, QtGui.QColor(59, 59, 59)
    )
    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.Dark, QtGui.QColor(37, 37, 37)
    )
    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.Mid, QtGui.QColor(45, 45, 45)
    )
    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.Text, QtGui.QColor(200, 200, 200)
    )
    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.Link, QtGui.QColor(200, 200, 200)
    )
    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.LinkVisited, QtGui.QColor(97, 97, 97)
    )
    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.BrightText, QtGui.QColor(37, 37, 37)
    )
    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.Base, QtGui.QColor(42, 42, 42)
    )
    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.Window, QtGui.QColor(68, 68, 68)
    )
    palette.setBrush(
        QtGui.QPalette.Active, QtGui.QPalette.Shadow, QtGui.QColor(0, 0, 0)
    )
    palette.setBrush(
        QtGui.QPalette.Active,
        QtGui.QPalette.AlternateBase,
        palette.color(QtGui.QPalette.Active, QtGui.QPalette.Base).lighter(110),
    )

    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, QtGui.QColor(200, 200, 200),
    )
    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.Button, QtGui.QColor(75, 75, 75)
    )
    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, QtGui.QColor(200, 200, 200),
    )
    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.Light, QtGui.QColor(97, 97, 97)
    )
    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.Midlight, QtGui.QColor(59, 59, 59)
    )
    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.Dark, QtGui.QColor(37, 37, 37)
    )
    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.Mid, QtGui.QColor(45, 45, 45)
    )
    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.Text, QtGui.QColor(200, 200, 200)
    )
    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.Link, QtGui.QColor(200, 200, 200)
    )
    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.LinkVisited, QtGui.QColor(97, 97, 97),
    )
    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.BrightText, QtGui.QColor(37, 37, 37)
    )
    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.Base, QtGui.QColor(42, 42, 42)
    )
    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.Window, QtGui.QColor(68, 68, 68)
    )
    palette.setBrush(
        QtGui.QPalette.Inactive, QtGui.QPalette.Shadow, QtGui.QColor(0, 0, 0)
    )
    palette.setBrush(
        QtGui.QPalette.Inactive,
        QtGui.QPalette.AlternateBase,
        palette.color(QtGui.QPalette.Inactive, QtGui.QPalette.Base).lighter(110),
    )

    app.setPalette(palette)

    # Finally, we just need to set the default font size for our widgets
    # deriving from QWidget. This also has the side effect of correcting
    # a couple of styling quirks in the tank dialog header when it's
    # used with the fusion style.
    app.setStyleSheet(".QWidget { font-size: 11px; }")

    css_file = "/Users/boismej/gitlocal/tk-desktop/style.qss"
    with open(css_file) as f:
        css = app.styleSheet() + "\n\n" + f.read()
    app.setStyleSheet(css)
else:
    from sgtk.platform.qt import QtCore, QtGui


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

    def __init__(self, parent, command_name, button_name, icon, tooltip):
        super(RecentButton, self).__init__(parent)

        self.setFlat(True)

        layout = QtGui.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter)
        layout.setSpacing(self.SPACING)
        layout.setContentsMargins(
            self.SPACING, self.SPACING, self.SPACING, self.SPACING
        )

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

    @property
    def name(self):
        return self.text()

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
        print(full_size)

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

        if self._is_menu_empty:
            self._is_menu_empty = False
        else:
            self.setPopupMode(self.MenuButtonPopup)
            self.setMenu(self._menu)

    def sizeHint(self):
        hint = QtCore.QSize((self.parent().width() / 2) - 20, ICON_SIZE.height() + 8)
        return hint


class RecentList(QtGui.QWidget):
    def __init__(self, parent):
        super(RecentList, self).__init__(parent)
        self._layout = QtGui.QHBoxLayout(self)
        self.setLayout(self._layout)
        self._layout.addStretch(1)

    def add_command(self, command_name, button_name, icon, tooltip):
        _find_or_insert_in_layout(
            self._layout,
            range(self._layout.count() - 1),
            button_name,
            lambda: RecentButton(self, command_name, button_name, icon, tooltip),
        )


class CommandList(QtGui.QWidget):
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


class Section(QtGui.QWidget):
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

    def add_command(self, command_name, button_name, icon, tooltip):
        self._list.add_command(command_name, button_name, icon, tooltip)


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
    def __init__(self, parent):
        super(CommandsView, self).__init__(parent)
        self.setObjectName("project_commands")
        self._layout = QtGui.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self._layout.addStretch(1)
        self._recents = None
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        if parent:
            filter = ResizeEventFilter(parent)
            filter.resized.connect(self._on_parent_resized)
            parent.installEventFilter(filter)

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
        # if show_recents:
        #     self._groups["Recent"] = CommandSection("Recent")

    def clear(self):

        while self.layout().count() > 0:
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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

        # if action in recent list.
        if False:
            if self._recents is None:
                self._recents = RecentSection("Recent")
                self._layout.insertWidget(0, self._recents)
            self._recents.add_command(command_name, menu_name, icon, tooltip)

        for group_name in groups:
            # Search for the requested group.
            current_group = _find_or_insert_in_layout(
                self._layout,
                self._section_range(),
                group_name,
                lambda: CommandSection(group_name),
                first=1 if self._recents else 0,
            )
            current_group.add_command(
                command_name, button_name, menu_name, icon, tooltip, is_menu_default
            )

    def _section_range(self):
        if self._recents:
            return range(1, self._layout.count() - 1)
        else:
            return range(self._layout.count() - 1)


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
    view = CommandsView(scrollarea)
    scrollarea.setWidget(view)

    view.set_project(None, ["Creative Tools", "Editorial Tools", "Automotive Tools"])

    commands = [
        (
            "nuke_studio_120",
            "Nuke Studio",
            "Nuke Studio 12.0",
            "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
            "tooltip nuke 12.0",
            ["Creative Tools"],
            True,
        ),
        (
            "nuke_studio_120",
            "NukeX",
            "NukeX 12.5",
            "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
            "tooltip nuke 12.0",
            ["Creative Tools"],
            True,
        ),
        (
            "nuke_studio_120",
            "NukeX",
            "NukeX 12.0",
            "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
            "tooltip nuke 12.0",
            ["Creative Tools"],
            False,
        ),
        (
            "nuke_studio_120",
            "Nuke Assist",
            "Nuke Assist 12.0",
            "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
            "tooltip nuke 12.0",
            ["Creative Tools"],
            True,
        ),
        (
            "maya2019",
            "Maya",
            "Maya 2019",
            "/Users/boismej/gitlocal/tk-maya/icon_256.png",
            "tooltip maya 2019",
            ["Creative Tools"],
            True,
        ),
        (
            "maya2020",
            "Maya",
            "Maya 2020",
            "/Users/boismej/gitlocal/tk-maya/icon_256.png",
            "tooltip maya 2020",
            ["Creative Tools"],
            False,
        ),
    ]

    if False:

        def add_button():
            command = commands.pop(0)
            view.add_command(*command)
            if commands:
                QtCore.QTimer.singleShot(500, add_button)

        QtCore.QTimer.singleShot(1000, add_button)
    else:
        for cmd in commands:
            view.add_command(*cmd)

    scrollarea.show()

    app.exec_()
