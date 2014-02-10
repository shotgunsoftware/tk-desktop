# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys

from PySide import QtGui
from PySide import QtCore

import tank
from tank.platform import constants

from .ui import systray
from .ui import resources_rc

from .model_project import SgProjectModel
from .delegate_project import SgProjectDelegate
from .systray_icon import ShotgunSystemTrayIcon

# import the shotgun_model module from the shotgun utils framework
shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunModel = shotgun_model.ShotgunModel


class SystemTrayWindow(QtGui.QMainWindow):
    """ Dockable window for the Shotgun system tray """

    # constants to track what state the window is in
    STATE_WINDOWED = 0x0001
    STATE_PINNED = 0x0002

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)

        # initialize member variables
        self.__state = None  # pinned or windowed
        self.__mouse_down_pos = None  # track position when dragging
        self.__mouse_down_global = None  # track global position when dragging

        # setup the window
        self.ui = systray.Ui_SystemTrayWindow()
        self.ui.setupUi(self)

        # create the system tray icon
        self.systray = ShotgunSystemTrayIcon(self)
        self.systray.show()

        # initialize state
        self.state = self.STATE_PINNED

        # load up the gear menu
        self._setup_config_menu()

        # load and initialize cached projects
        self._project_model = SgProjectModel(self.ui.projects)
        self.ui.projects.setModel(self._project_model)

        # tell our project view to use a custom delegate to produce widgets
        self._project_delegate = SgProjectDelegate(self.ui.projects)
        self.ui.projects.setItemDelegate(self._project_delegate)

        # handle project selection change
        self._project_selection_model = self.ui.projects.selectionModel()
        self._project_selection_model.selectionChanged.connect(self._on_project_selection)

        # hook up handler for when the systray is clicked
        self.systray.clicked.connect(self.systray_clicked)

    ########################################################################################
    # Event handlers
    def mousePressEvent(self, event):
        """ Handle mouse press to track the start of a drag from the pinned window header """
        if self.state == self.STATE_PINNED and self.ui.header_frame.underMouse():
            # only trigger on left click
            if event.buttons() == QtCore.Qt.LeftButton:
                # clicked on the header while pinned, track position for possible drag
                self.__mouse_down_pos = event.pos()
                self.__mouse_down_global = QtGui.QCursor.pos()

        # propagate event
        event.ignore()

    def mouseReleaseEvent(self, event):
        """ Handle mouse release to switch to window mode if there has been a long enough drag """
        # only do something if we are dragging
        if self.__mouse_down_pos is None:
            event.ignore()
            return

        # if we have moved more than threshold then trigger a switch to windowed mode
        if self.state == self.STATE_PINNED:
            delta = QtGui.QCursor.pos() - self.__mouse_down_global
            if delta.manhattanLength() > QtGui.QApplication.startDragDistance():
                self.state = self.STATE_WINDOWED

        # clear cached positions
        self.__mouse_down_pos = None
        self.__mouse_down_global = None

        # propagate event
        event.ignore()

    def mouseMoveEvent(self, event):
        """ Handle mouse moves to move the window with the mouse if we are dragging """
        if self.__mouse_down_pos is not None:
            # move window to track mouse
            self.move(self.mapToParent(event.pos() - self.__mouse_down_pos))

        # propagate event
        event.ignore()

    def closeEvent(self, event):
        """ Take over the close event to simply hide the window and repin """
        # figure out start and end positions for the window
        systray_geo = self.systray.geometry()
        final = QtCore.QRect(systray_geo.center().x(), systray_geo.bottom(), 5, 5)
        start = self.geometry()

        # setup the animation to shrink the window to the systray
        # parent the anim to self to keep it from being garbage collected
        anim = QtCore.QPropertyAnimation(self, "geometry", self)
        anim.setDuration(300)
        anim.setStartValue(start)
        anim.setEndValue(final)
        anim.setEasingCurve(QtCore.QEasingCurve.InQuad)

        # when the anim is finished, call the post handler
        closure = lambda: self._postCloseAnimation(start)
        anim.finished.connect(closure)

        # run the animation
        anim.start()

        # propagate the event
        event.ignore()

    def _postCloseAnimation(self, original):
        """ After the animation is finished hide the window, reset it size, and pin it """
        self.hide()
        self.setGeometry(original)
        self.state = self.STATE_PINNED

    ########################################################################################
    # Pinning
    def _getState(self):
        """ return the current state of the window """
        return self.__state

    def _setState(self, value):
        """ set the current state of the window """
        # if state isn't changing do not do anything
        if self.__state == value:
            return

        # update tracker variable
        self.__state = value

        # if we are visible, we will need to reshow and position after changing flags
        shown = self.isVisible()
        if shown:
            pos = self.pos()

        if self.__state == self.STATE_PINNED:
            # update the mask and get rid of the window decorations
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
            self._set_window_mask()

            # reset visibility after setting flags
            if shown:
                self.__move_to_systray()
                self.show()
        elif self.__state == self.STATE_WINDOWED:
            # clear the mask and decorate the window
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.FramelessWindowHint)
            self._clear_window_mask()

            # reset visibility after setting flags
            if shown:
                self.show()
                self.move(pos)
        else:
            raise ValueError("Unknown value for state: %s" % value)

    # create a property from the getter/setter
    state = property(_getState, _setState)

    def _clear_window_mask(self):
        """ reset the window mask """
        self.clearMask()

    def _set_window_mask(self):
        """ set the window mask when pinned to the systray """
        roundness = 10

        # temp bitmap to store the mask
        bmp = QtGui.QBitmap(self.size())

        # create and configure the painter
        self.painter = QtGui.QPainter(bmp)
        self.painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing, True)

        # mask out from the margin of the border_layout via a rounded rectangle
        rect = self.rect()
        (left, top, right, bottom) = self.ui.border_layout.getContentsMargins()
        self.painter.fillRect(rect, QtCore.Qt.white)
        self.painter.setBrush(QtGui.QColor(0, 0, 0))
        mask = rect.adjusted(left, top, -right, -bottom)
        self.painter.drawRoundedRect(mask, roundness, roundness)

        # add back in the anchor triangle
        (x, y, w, h) = rect.getRect()
        midpoint = x + w/2.0
        points = []
        points.append(QtCore.QPoint(midpoint, y))
        points.append(QtCore.QPoint(midpoint-top, y+top))
        points.append(QtCore.QPoint(midpoint+top, y+top))
        self.painter.drawPolygon(points)

        # need to end the painter to make sure that its resources get
        # garbage collected before the bitmap to avoid a crash
        self.painter.end()

        # finally set the window mask to the bitmap
        self.setMask(bmp)

    def _setup_config_menu(self):
        """ create the gear menu """
        app = QtGui.QApplication.instance()

        # quit action to exit the app
        self._quit_action = QtGui.QAction("&Quit", self)
        self._quit_action.triggered.connect(app.quit)

        # create the menu itself
        self._config_menu = QtGui.QMenu(self)
        self._config_menu.addAction(self._quit_action)

        # update the settings button with the menu
        self.ui.settings_button.setMenu(self._config_menu)

        # clear the down arrow from the button
        self.ui.settings_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")

    ########################################################################################
    # project view
    def _on_project_selection(self, selected, deselected):
        selected_indexes = selected.indexes()

        self.ui.tabs.clear()

        if len(selected_indexes) == 0:
            return

        item = selected_indexes[0].model().itemFromIndex(selected_indexes[0])
        sg_data = item.data(ShotgunModel.SG_DATA_ROLE)

        engine = tank.platform.current_engine()

        platform_fields = {
            'darwin': 'mac_path',
            'linux': 'linux_path',
            'win32': 'windows_path',
        }
        path_field = platform_fields.get(sys.platform)

        if path_field is None:
            raise SystemError("Unsupported platform: %s" % sys.platform)

        filters = [
            ["code", "is", constants.PRIMARY_PIPELINE_CONFIG_NAME],
            ["project", "is", sg_data],
        ]

        fields = [path_field, 'users']
        pipeline_configuration = engine.shotgun.find_one(
            'PipelineConfiguration',
            filters,
            fields=fields,
        )

        if pipeline_configuration is None:
            self.log_info("Selected project with no pipeline configuration: %s (%d)" % (sg_data['name'], sg_data['id']))
            return

        tank.platform.current_engine().destroy()

        os.environ['SGTK_DESKTOP_ENGINE_INITIALIZED'] = "1"
        new_tk = tank.sgtk_from_path(pipeline_configuration[path_field])
        new_ctx = new_tk.context_from_entity(sg_data['type'], sg_data['id'])
        new_engine = tank.platform.start_engine('tk-desktop', new_tk, new_ctx)

        for (cmd_name, cmd_details) in new_engine.commands.items():
            if cmd_details['properties'].get('type') != 'system_tray':
                continue

            widget = cmd_details["callback"](cmd_details["properties"], self.ui.tabs)
            self.ui.tabs.addTab(widget, cmd_name)

    ########################################################################################
    # system tray
    def __move_to_systray(self):
        """ update the window position to be centered under the system tray icon """
        geo = self.systray.geometry()
        x = geo.x() + (geo.width() - self.rect().width()) / 2.0
        self.move(x, geo.y() + geo.height())

    def systray_clicked(self):
        """ handler for single click on the system tray """
        # toggle visibility when clicked
        if self.isHidden():
            if self.state == self.STATE_PINNED:
                # make sure the window is positioned correctly if pinned
                self.__move_to_systray()
            self.show()
            self.raise_()
        else:
            self.hide()
