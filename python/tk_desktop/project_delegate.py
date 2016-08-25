# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank.platform.qt import QtCore

import sgtk

from .thumb_widget import ThumbWidget
from .project_model import SgProjectModel

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
views = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")

ShotgunModel = shotgun_model.ShotgunModel


class SgProjectDelegate(views.EditSelectedWidgetDelegate):
    def __init__(self, view, size):
        self._size = size
        self._view = view
        views.EditSelectedWidgetDelegate.__init__(self, view)

    def _create_widget(self, parent):
        """ Widget factory as required by base class """
        return ThumbWidget(self._size.width(), parent)

    def _on_before_paint(self, widget, model_index, style_options, selected=False):
        """
        Called by the base class before the associated widget should be
        painted in the view.
        """
        # setup thumbnail
        icon = model_index.data(QtCore.Qt.DecorationRole)
        if icon is not None:
            thumb = icon.pixmap(512)
            widget.set_thumbnail(thumb)

        # set name
        widget.set_text(model_index.data(SgProjectModel.DISPLAY_NAME_ROLE))

        # set description tooltip
        project = model_index.data(ShotgunModel.SG_DATA_ROLE)
        if project is not None:
            tooltip = project.get("sg_description") or ""
            self._view.setToolTip(tooltip)

        widget.set_selected(selected)

    def _on_before_selection(self, widget, model_index, style_options):
        """
        Called by the base class before the associated widget should
        be selected.
        """
        # rendering of a selected widget is the same
        self._on_before_paint(widget, model_index, style_options, selected=True)

    def sizeHint(self, style_options, model_index):
        text = model_index.data(SgProjectModel.DISPLAY_NAME_ROLE)
        height = ThumbWidget.height_for_width(self._size.width(), text)
        return QtCore.QSize(self._size.width(), height)
