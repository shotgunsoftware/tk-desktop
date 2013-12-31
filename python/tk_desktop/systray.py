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


# import the shotgun_model module from the shotgun utils framework
shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunModel = shotgun_model.ShotgunModel


class SystemTrayWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.ui = systray.Ui_SystemTrayWindow()
        self.ui.setupUi(self)

        # register icon in the system tray area
        icon = QtGui.QIcon(":/res/default_systray_icon")
        self.systray = QtGui.QSystemTrayIcon(icon, self)

        # update window mask for rounded corners and anchor if docked
        self.set_window_mask()

        # load and initialize cached projects
        self._project_model = SgProjectModel(self.ui.projects)
        self.ui.projects.setModel(self._project_model)

        # tell our project view to use a custom delegate to produce widgetry
        self._project_delegate = SgProjectDelegate(self.ui.projects)
        self.ui.projects.setItemDelegate(self._project_delegate)

        # handle project selection change
        self._project_selection_model = self.ui.projects.selectionModel()
        self._project_selection_model.selectionChanged.connect(self._on_project_selection)

        # show on click
        self.systray.activated.connect(self.systray_activated)
        self.systray.show()

    def set_window_mask(self):
        roundness = 10

        # Set mask for system tray window
        bmp = QtGui.QBitmap(self.size())
        self.painter = QtGui.QPainter(bmp)
        self.painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing, True)

        rect = self.rect()
        (left, top, right, bottom) = self.ui.border_layout.getContentsMargins()
        self.painter.fillRect(rect, QtCore.Qt.white)
        self.painter.setBrush(QtGui.QColor(0, 0, 0))
        mask = rect.adjusted(left, top, -right, -bottom)
        self.painter.drawRoundedRect(mask, roundness, roundness)

        # draw anchor
        (x, y, w, h) = rect.getRect()
        midpoint = x + w/2.0
        points = []
        points.append(QtCore.QPoint(midpoint, y))
        points.append(QtCore.QPoint(midpoint-top, y+top))
        points.append(QtCore.QPoint(midpoint+top, y+top))
        self.painter.drawPolygon(points)
        self.setMask(bmp)

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

    def systray_activated(self, reason):
        if self.isHidden():
            rect = self.rect()
            geo = self.systray.geometry()
            x = geo.x() + (geo.width() - rect.width()) / 2.0
            self.move(x, geo.y() + geo.height())
            self.show()
        else:
            self.hide()
