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

import tank


shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunModel = shotgun_model.ShotgunModel


class SgProjectModel(ShotgunModel):
    """
    This model represents the data which is displayed in the projects list view
    """
    SORT_KEY_ROLE = QtCore.Qt.UserRole + 101
    DISPLAY_NAME_ROLE = QtCore.Qt.UserRole + 102

    def __init__(self, overlay_parent_widget):
        """ Constructor """
        ShotgunModel.__init__(self, overlay_parent_widget, download_thumbs=True)

        self._loading_icon = QtGui.QPixmap(":/res/loading_512x400.png")

        # specify sort key
        self.setSortRole(self.SORT_KEY_ROLE)

        # get data from Shotgun
        ShotgunModel._load_data(
            self,
            entity_type='Project',
            filters=[],
            hierarchy=["name"],
            fields=[],
            order=[],
        )

        self._refresh_data()

    ############################################################################################
    # subclassed methods

    def _ShotgunModel__on_worker_failure(self, uid, msg):
        super(SgProjectModel, self)._ShotgunModel__on_worker_failure(uid, msg)

    def _populate_item(self, item, sg_data):
        name = sg_data.get("name", "No Name")
        item.setData(name, self.DISPLAY_NAME_ROLE)

    def _populate_default_thumbnail(self, item):
        # set up publishes with a "thumbnail loading" icon
        item.setIcon(self._loading_icon)

    def _populate_thumbnail(self, item, field, path):
        thumb = QtGui.QPixmap(path)
        item.setIcon(thumb)
