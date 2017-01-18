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

    _MORE_DETAILS = "more details..."
    _LESS_DETAILS = "less details..."

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

        self._message = None

        self._ui.progress_output.hide()
        self.show()

        self._ui.more_or_less_label.linkActivated.connect(self._on_more_less_clicked)
        self._set_label_text(self._MORE_DETAILS)

    def _set_label_text(self, msg):
        self._ui.more_or_less_label.setText("<a href='#'>%s</a>" % (msg,))

    def _on_more_less_clicked(self, _):
        if self._ui.progress_output.isVisible():
            self._ui.progress_output.setVisible(False)
            self._set_label_text(self._MORE_DETAILS)
        else:
            self._ui.progress_output.setVisible(True)
            self._set_label_text(self._LESS_DETAILS)

    def _on_parent_resized(self):
        """
        Special slot hooked up to the event filter.
        When associated widget is resized this slot is being called.
        """
        # resize overlay
        self.resize(self.parentWidget().size())

    def start_progress(self):
        self._ui.shotgun_spinning_widget.start_progress()
        self._ui.progress_output.hide()
        self._set_label_text(self._MORE_DETAILS)
        self._ui.progress_output.clear()
        self.setVisible(True)

    def report_progress(self, current, msg):
        self._ui.shotgun_spinning_widget.report_progress(current)
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

        :param msg: Message to display
        """
        # Hide all widgets
        self._shotgun_spinning_widget.hide()
        self._ui.bottom.hide()
        self._ui.progress_output.hide()

        self.setVisible(True)
        self._message = msg
        self.repaint()

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            overlay_color = QtGui.QColor("#1B1B1B")
            painter.setBrush(QtGui.QBrush(overlay_color))
            painter.setPen(QtGui.QPen(overlay_color))
            painter.drawRect(0, 0, painter.device().width(), painter.device().height())

            if self._message is not None:
                # show error text in the center
                pen = QtGui.QPen(QtGui.QColor("#C8534A"))
                painter.setPen(pen)
                text_rect = QtCore.QRect(0, 0, painter.device().width(), painter.device().height())
                text_flags = QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.TextWordWrap
                painter.drawText(text_rect, text_flags, self._message)
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
