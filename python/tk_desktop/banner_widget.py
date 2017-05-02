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
    """

    def __init__(self, mgr, notif, is_last, parent=None):
        """
        :param mgr: ``NotificationsManager`` instance.
        :param notif: ``Notification`` instance to display.
        :
        """
        super(BannerWidget, self).__init__(parent)

        self.ui = Ui_BannerWidget()
        self.ui.setupUi(self)

        # If we want the background color to apply to the entire surface of the widget
        # in PySide instead of just under its children we need to set this flag.
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        self._current_message_id = None

        self.ui.message.setText(notif.message)
        self._mgr = mgr
        self._notif = notif

        self.ui.close_button.clicked.connect(self._on_dismiss_message)
        self.ui.message.linkActivated.connect(self._on_link_clicked)

        if is_last:
            self.ui.line.hide()
        else:
            self.ui.line.show()

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
        self.hide()
