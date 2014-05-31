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


shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "shotgun_view")


class SgProjectDelegate(shotgun_view.WidgetDelegate):
    def __init__(self, view, size):
        shotgun_view.WidgetDelegate.__init__(self, view)
        self._size = size
        self.__current_selected_widget = None

    def _create_widget(self, parent):
        """ Widget factory as required by base class """
        return ThumbWidget(parent)

    def _on_before_paint(self, widget, model_index, style_options):
        """
        Called by the base class before the associated widget should be
        painted in the view.
        """
        icon = model_index.data(QtCore.Qt.DecorationRole)
        thumb = icon.pixmap(512)
        widget.set_thumbnail(thumb)
        widget.set_text(model_index.data(SgProjectModel.DISPLAY_NAME_ROLE))
        widget.set_selected(False)

    def _on_before_selection(self, widget, model_index, style_options):
        """
        Called by the base class before the associated widget should
        be selected.
        """
        if self.__current_selected_widget is not None:
            try:
                # only one selection at a time
                self.__current_selected_widget.set_selected(False)
            except RuntimeError:
                # the current selected widget may be deleted from
                # underneath us
                pass

        # rendering of a selected widget is the same
        self._on_before_paint(widget, model_index, style_options)

        widget.set_selected(True)
        self.__current_selected_widget = widget

    def sizeHint(self, style_options, model_index):
        return self._size
