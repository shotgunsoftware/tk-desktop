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

    _BANNERS = "banners"
    _FIRST_LAUNCH_BANNER_VIEWED_ID = "first_desktop_launch_banner_viewed"
    _SHOTGUN_DESKTOP_SUPPORT_PAGE_URL = (
        "https://support.shotgunsoftware.com/hc/en-us/articles/219040668-"
        "Shotgun-Desktop-Download-and-Setup#The%20Toolkit%20Project%20setup%20wizard"
    )

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

        banner_ids = self._settings_manager.retrieve(self._BANNERS, {})

        if not banner_ids.get(self._FIRST_LAUNCH_BANNER_VIEWED_ID, False):
            logger.debug("First launch message shown.")
            self.show()
            self._current_message_id = self._FIRST_LAUNCH_BANNER_VIEWED_ID

            self.ui.message.setText(
                "Welcome to the <b>Shotgun Desktop</b>. Please <a href='%s'>click here</a> to learn more!" %
                self._SHOTGUN_DESKTOP_SUPPORT_PAGE_URL
            )
            return

        bundle = sgtk.platform.current_bundle()
        banner_id = bundle.get_setting("banner_id")
        if not banner_ids.get(banner_id, False):
            logger.debug("banner_id '%s' shown.", banner_id)
            self.show()
            self._current_message_id = banner_id
            self.ui.message.setText(bundle.get_setting("banner_message"))
            return

        self.hide()

    def _on_link_clicked(self, url):
        QtGui.QDesktopServices.openUrl(url)
        self._on_dismiss_message()

    def _on_dismiss_message(self):
        banner_ids = self._settings_manager.retrieve(self._BANNERS, {})
        banner_ids[self._current_message_id] = True
        self._settings_manager.store(self._BANNERS, banner_ids)

        # Check if there is a new message to show.
        self.show_next_message()

    def reset_banners(self):
        self._settings_manager.store(self._BANNERS, {})

    def set_settings_manager(self, settings_manager):
        self._settings_manager = settings_manager
