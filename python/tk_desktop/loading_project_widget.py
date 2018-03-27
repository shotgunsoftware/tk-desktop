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
import sgtk

overlay = sgtk.platform.import_framework(
    "tk-framework-qtwidgets", "overlay_widget"
)


class LoadingProjectWidget(QtGui.QWidget):
    """
    Shows a Shotgun progress widget with a text box containing details of how
    far along we are in the bootstrap process. It also supports displaying
    an error message on top.
    """

    _SHOW_DETAILS = "Show Details"
    _HIDE_DETAILS = "Less Details"

    ERROR_COLOR = overlay.ShotgunOverlayWidget.ERROR_COLOR

    def __init__(self, parent=None):
        """
        :param parent: Parent widget.
        """
        super(LoadingProjectWidget, self).__init__(parent)

        self._ui = Ui_LoadingProjectWidget()
        self._ui.setupUi(self)

        self._overlay = overlay.ShotgunOverlayWidget(self)

        # hook up a listener to the parent window so we
        # can resize the overlay at the same time as the parent window
        # is being resized.
        filter = ResizeEventFilter(parent)
        filter.resized.connect(self._on_parent_resized)
        parent.installEventFilter(filter)

        self._ui.progress_output.hide()
        self.show()

        self._ui.show_hide_details.clicked.connect(self._on_more_less_clicked)
        self._ui.show_hide_details.setText(self._SHOW_DETAILS)

    def _on_more_less_clicked(self):
        """
        Toggles the text box visibility.
        """
        if self._ui.progress_output.isVisible():
            self._ui.progress_output.setVisible(False)
            self._ui.show_hide_details.setText(self._SHOW_DETAILS)
        else:
            self._ui.progress_output.setVisible(True)
            self._ui.show_hide_details.setText(self._HIDE_DETAILS)

        # Doesn't look good with the focus.
        self._ui.show_hide_details.clearFocus()

    def _on_parent_resized(self):
        """
        Special slot hooked up to the event filter.
        When associated widget is resized this slot is being called.
        """
        # resize overlay
        self.resize(self.parentWidget().size())

    def start_progress(self):
        """
        Starts the progress reporting.
        """
        # Reset the message
        self._show_progress_widgets(True)
        self._ui.shotgun_spinning_widget.start_progress()
        # Hide details
        self._ui.progress_output.hide()
        # Reset the button.
        self._ui.show_hide_details.setText(self._SHOW_DETAILS)
        # Clear the details.
        self._ui.progress_output.clear()
        self.setVisible(True)

    def report_progress(self, pct, msg):
        """
        Updates the widget's progress indicator and detailed area.

        :param float pct: Current progress. Must be between 0 and 1.
        :param str msg: Message to add to the detailed area.
        """
        self._ui.shotgun_spinning_widget.report_progress(pct)
        if msg:
            self._ui.progress_output.appendHtml(msg)
            cursor = self._ui.progress_output.textCursor()
            cursor.movePosition(cursor.End)
            cursor.movePosition(cursor.StartOfLine)
            self._ui.progress_output.setTextCursor(cursor)
            self._ui.progress_output.ensureCursorVisible()

    def show_error_message(self, msg):
        """
        Enables the overlay and displays an
        a error message centered in the middle of the overlay.

        :param str msg: Message to display
        """
        # Hide all widgets
        self._show_progress_widgets(False)
        self._overlay.show_error_message(msg)
        self.setVisible(True)

    def _show_progress_widgets(self, show=False):
        """
        Shows or hides the widgets in the UI.

        :param show: If True, shows all the widgets in the UI. Hides them on False.
        """
        self._ui.shotgun_spinning_widget.setVisible(show)
        self._ui.bottom.setVisible(show)
        self._ui.progress_output.setVisible(show)
        if show is True:
            self._overlay.hide()


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
