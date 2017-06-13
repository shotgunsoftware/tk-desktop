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


class FirstLaunchNotification(Notification):
    """
    Notification on the first launch of the Shotgun Desktop.
    """

    _FIRST_LAUNCH_BANNER_VIEWED_ID = "first_desktop_launch_banner_viewed"
    SHOTGUN_DESKTOP_SUPPORT_PAGE_URL = (
        r"https://support.shotgunsoftware.com/hc/en-us/articles/115000068574"
        r"#Getting%20started%20with%20Shotgun%20Desktop"
    )

    @classmethod
    def create(cls, banner_settings):
        """
        Notification factory for this class.

        If this is the first time the user launches the Shotgun Desktop, an instance of this class
        will be returned. Otherwise, ``None`` will be returned.

        Note that if this notification has been dismissed in the past, the method will also
        return ``None``.

        :param banner_settings: Dictionary of banner_settings.
        :param engine: Toolkit engine.
        """
        if banner_settings.get(cls._FIRST_LAUNCH_BANNER_VIEWED_ID, False):
            logger.debug("First launch notification has already been dismissed.")
            return None
        else:
            logger.debug("First launch notification is available.")
            return FirstLaunchNotification()

    @property
    def message(self):
        """
        Message to display.
        """
        return "Welcome to the <b>Shotgun Desktop</b>. <a href='{0}'>Click here</a> to learn more.".format(
            self.SHOTGUN_DESKTOP_SUPPORT_PAGE_URL
        )

    @property
    def unique_id(self):
        """
        Returns the unique identifier of a notification.
        """
        return self._FIRST_LAUNCH_BANNER_VIEWED_ID

    def _dismiss(self, banner_settings):
        """
        Updates the ``banner_settings`` so this notification does not come back in the future.

        :param banner_settings: Dictionary of the banners settings.
        """
        banner_settings[self._FIRST_LAUNCH_BANNER_VIEWED_ID] = True
