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

    def __init__(self, parent=None):
        super(BannerWidget, self).__init__(parent)

        self.ui = Ui_BannerWidget()
        self.ui.setupUi(self)

        # If we want the background color to apply to the entire surface of the widget
        # in PySide instead of just under its children we need to set this flag.
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        self._current_message_id = None

        self.ui.close_button.clicked.connect(self._on_dismiss_message)
        self.ui.message.linkActivated.connect(self._on_link_clicked)

    def show_next_message(self):
        notifs = list(self._notifications_manager.get_notifications())

        if not notifs:
            self.hide()
            return

        notif = notifs.pop(0)

        self._notif = notif

        self.ui.message.setText(notif.message)
        self.show()

    def _on_link_clicked(self, url):
        QtGui.QDesktopServices.openUrl(url)
        self._on_dismiss_message()

    def _on_dismiss_message(self):
        self._notifications_manager.dismiss(self._notif)
        # Check if there is a new message to show.
        self.show_next_message()

    def reset_banners(self):
        self._notifications_manager.reset()

    def set_settings_manager(self, notifications_manager):
        self._notifications_manager = notifications_manager
