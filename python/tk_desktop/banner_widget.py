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

    dismissed = QtCore.Signal(object)

    def __init__(self, notifications_mgr, notification, parent=None):
        """
        :param notifications_mgr: ``NotificationsManager`` instance.
        :param notification: ``Notification`` instance to display.
        :param parent: Parent widget
        """
        super(BannerWidget, self).__init__(parent)

        self.ui = Ui_BannerWidget()
        self.ui.setupUi(self)

        # If we want the background color to apply to the entire surface of the widget
        # in PySide instead of just under its children we need to set this flag.
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        self._current_message_id = None

        self.ui.message.setText(notification.message)
        self._notifications_mgr = notifications_mgr
        self._notification = notification

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

    @property
    def unique_id(self):
        """
        Returns the unique identifier of a notification.
        """
        return self._notification.unique_id

    def _on_dismiss_message(self):
        """
        Dismisses the message and hides the banner.
        """
        self._notifications_mgr.dismiss(self._notification)
        self.dismissed.emit(self)