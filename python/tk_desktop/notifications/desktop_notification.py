# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from .notification import Notification


class DesktopNotification(Notification):

    _DESKTOP_NOTIFICATIONS = "desktop.notifications"

    def __init__(self, engine):
        self._engine = engine

    @classmethod
    def create(cls, banner_settings, engine):

        banner_id = engine.get_setting("banner_id")
        banner_message = engine.get_setting("banner_message")

        if not banner_id or not banner_message:
            return

        if banner_settings.get(
            cls._DESKTOP_NOTIFICATIONS, {}
        ).get(banner_id, False):
            return None
        else:

            return DesktopNotification(engine)

    @property
    def message(self):
        return self._engine.get_setting("banner_message")

    def _dismiss(self, banner_settings):
        banner_settings.setdefault(
            self._DESKTOP_NOTIFICATIONS, {}
        )[self._engine.get_setting("banner_id")] = True
