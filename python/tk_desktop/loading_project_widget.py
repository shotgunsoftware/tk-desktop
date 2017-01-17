# -*- coding: utf-8 -*-
# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


from sgtk.platform.qt import QtCore, QtGui
from .ui.loading_project_widget import Ui_LoadingProjectWidget


class LoadingProjectWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(LoadingProjectWidget, self).__init__(parent)

        self._ui = Ui_LoadingProjectWidget()
        self._ui.setupUi(self)

        # hook up a listener to the parent window so we
        # can resize the overlay at the same time as the parent window
        # is being resized.
        filter = ResizeEventFilter(parent)
        filter.resized.connect(self._on_parent_resized)
        parent.installEventFilter(filter)

        self.show()

        # make it transparent
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

    def _on_parent_resized(self):
        """
        Special slot hooked up to the event filter.
        When associated widget is resized this slot is being called.
        """
        # resize overlay
        self.resize(self.parentWidget().size())

    def start_progress(self):
        self._ui.shotgun_overlay_widget.start_progress()
        self.setVisible(True)

    def report_progress(self, current, msg):
        self._ui.shotgun_overlay_widget.report_progress(current)

    def show_error_message(self, msg):
        self._ui.progress.hide()
        self._ui.more_less_btn.hide()
        self._ui.shotgun_overlay_widget.show_error_message(msg)

    def paintEvent(self, event):

        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            overlay_color = QtGui.QColor("#1B1B1B")
            painter.setBrush(QtGui.QBrush(overlay_color))
            painter.setPen(QtGui.QPen(overlay_color))
            painter.drawRect(0, 0, painter.device().width(), painter.device().height())
        finally:
            painter.end()

        return super(LoadingProjectWidget, self).paintEvent(event)


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
