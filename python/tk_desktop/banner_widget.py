# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk.platform.qt import QtCore, QtGui
from .ui.banner_widget import Ui_BannerWidget


logger = sgtk.platform.get_logger(__name__)


class BannerWidget(QtGui.QWidget):
    """
    Shows a notification in the banner.

    :signals: dismissed() Invoked when the banner is dismissed by the user.
    """

    dismissed = QtCore.Signal()

    def __init__(self, mgr, notif, has_seperator, parent=None):
        """
        :param mgr: ``NotificationsManager`` instance.
        :param notif: ``Notification`` instance to display.
        :param has_seperator: If ``True``, a separator will be drawn under the widget.
        :param parent: Parent widget
        """
        super(BannerWidget, self).__init__(parent)

        self.ui = Ui_BannerWidget()
        self.ui.setupUi(self)

        # If we want the background color to apply to the entire surface of the widget
        # in PySide instead of just under its children we need to set this flag.
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        self._current_message_id = None
        self._has_seperator = has_seperator

        self.ui.message.setText(notif.message)
        self._mgr = mgr
        self._notif = notif

        self.ui.close_button.clicked.connect(self._on_dismiss_message)
        self.ui.message.linkActivated.connect(self._on_link_clicked)

    def _on_link_clicked(self, url):
        """
        Opens the URL when clicked, launches it in the browser and dismisses the
        message.
        """
        if url:
            QtGui.QDesktopServices.openUrl(url)
        self._on_dismiss_message()

    def _on_dismiss_message(self):
        """
        Dismisses the message and hides the banner.
        """
        self._mgr.dismiss(self._notif)
        self.dismissed.emit()

    def paintEvent(self, paint_event):
        """
        Draws a black line at the bottom of the widget if required.
        """
        super(BannerWidget, self).paintEvent(paint_event)

        if self._has_seperator:
            p = QtGui.QPainter(self)
            size = self.size()
            old_pen = p.pen()
            try:
                p.setPen(QtGui.QColor(0, 0, 0))
                p.drawLine(0, size.height() - 1, size.width(), size.height() - 1)
            finally:
                p.setPen(old_pen)
