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

from .model_project import SgProjectModel


shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
shotgun_view = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_view")


class SgProjectDelegate(shotgun_view.WidgetDelegate):
    def __init__(self, view):
        shotgun_view.WidgetDelegate.__init__(self, view)

    def _create_widget(self, parent):
        """ Widget factory as required by base class """
        return shotgun_view.ThumbWidget(parent)

    def _draw_widget(self, widget, model_index, style_options):
        """
        Called by the base class when the associated widget should be
        painted in the view.
        """
        if style_options.state & QtGui.QStyle.State_Selected:
            selected = True
        else:
            selected = False

        icon = model_index.data(QtCore.Qt.DecorationRole)
        thumb = icon.pixmap(512)

        widget.set_thumbnail(thumb)
        widget.set_selected(selected)
        widget.set_text(model_index.data(SgProjectModel.DISPLAY_NAME_ROLE), "", "")

    def _configure_widget(self, widget, model_index, style_options):
        pass

    def sizeHint(self, style_options, model_index):
        return shotgun_view.ThumbWidget.calculate_size(72)
