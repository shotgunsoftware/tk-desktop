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
import sgtk

logger = sgtk.platform.get_logger(__name__)


class DesktopNotification(Notification):
    """
    Notification that can be hard-coded in the tk-desktop engine.
    """

    _DESKTOP_NOTIFICATIONS = "desktop.notifications"

    def __init__(self, engine):
        """
        :param engine: Toolkit engine.
        """
        self._engine = engine

    @classmethod
    def create(cls, banner_settings, engine):
        """
        Notification factory for the ``DesktopNotification`` class.

        If the ``banner_id`` and ``banner_message`` settings for the engine are set,
        an instance of this class will be returned. Otherwise, ``None`` will be returned.

        Note that if this notification has been dismissed in the past, the method will also
        return ``None``.

        :param banner_settings: Dictionary of banner settings.
        :param engine: Toolkit engine.

        :returns: A :class:`DesktopNotification` instance, or ``None``.
        """

        banner_id = engine.get_setting("banner_id")
        banner_message = engine.get_setting("banner_message")

        if not banner_id or not banner_message:
            logger.debug(
                "banner_id and/or banner_message not set."
            )
            return

        if banner_settings.get(
            cls._DESKTOP_NOTIFICATIONS, {}
        ).get(banner_id, False):
            logger.debug(
                "banner_id %s has already been dismissed.",
                banner_id
            )
            return None
        else:
            logger.debug("Desktop notification is available.")
            return DesktopNotification(engine)

    @property
    def message(self):
        """
        Message to display.
        """
        return self._engine.get_setting("banner_message")

    @property
    def unique_id(self):
        """
        Returns the unique identifier of a notification.
        """
        return self._DESKTOP_NOTIFICATIONS + self._engine.get_setting("banner_id")

    def _dismiss(self, banner_settings):
        """
        Updates the ``banner_settings`` so this notification does not come back in the future.

        :param banner_settings: Dictionary of the banners settings.
        """
        banner_settings.setdefault(
            self._DESKTOP_NOTIFICATIONS, {}
        )[self._engine.get_setting("banner_id")] = True
