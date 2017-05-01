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


class FirstLaunchNotification(Notification):

    _FIRST_LAUNCH_BANNER_VIEWED_ID = "first_desktop_launch_banner_viewed"
    _SHOTGUN_DESKTOP_SUPPORT_PAGE_URL = (
        "https://support.shotgunsoftware.com/hc/en-us/articles/219040668-"
        "Shotgun-Desktop-Download-and-Setup#The%20Toolkit%20Project%20setup%20wizard"
    )

    @classmethod
    def create(cls, banner_settings):
        if banner_settings.get(cls._FIRST_LAUNCH_BANNER_VIEWED_ID, False):
            return None
        else:
            return FirstLaunchNotification()

    @property
    def message(self):
        return "Welcome to the <b>Shotgun Desktop</b>. <a href='{0}'>Click here</a> to learn more.".format(
            self._SHOTGUN_DESKTOP_SUPPORT_PAGE_URL
        )

    def _dismiss(self, banner_settings):
        banner_settings[self._FIRST_LAUNCH_BANNER_VIEWED_ID] = True
