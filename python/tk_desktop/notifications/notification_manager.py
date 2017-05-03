# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from .desktop_notification import DesktopNotification
from .configuration_update_notification import ConfigurationUpdateNotification
from .first_launch_notification import FirstLaunchNotification
from .startup_update_notification import StartupUpdateNotification


class NotificationsManager(object):
    """
    Allows to retrieve and dismiss notifications for the Shotgun Desktop.
    """

    _BANNERS = "banners"

    def __init__(self, user_settings, descriptor, engine):
        """
        :param user_settings. ``UserSettings`` instance.
        :param descriptor: Descriptor obtained from the pipeline configuration.
        :param engine: tk-desktop engine instance.
        """
        self._user_settings = user_settings
        self._descriptor = descriptor
        self._engine = engine

    def get_notifications(self):
        """
        Returns a list of notifications.

        If the FirstLaunchNotitification hasn't been dismissed yet, every other notification
        will be dismissed.

        :returns: An array on :class:``Notification`` objects.
        """
        banner_settings = self._get_banner_settings()

        # Check if this is the first launch.
        first_launch_notif = FirstLaunchNotification.create(banner_settings)

        # Get all other notification types. Filter out those who are not set.
        other_notifs = filter(
            None,
            [
                ConfigurationUpdateNotification.create(banner_settings, self._descriptor),
                StartupUpdateNotification.create(banner_settings, self._engine),
                DesktopNotification.create(banner_settings, self._engine)
            ]
        )

        # If this is the first launch, suppress all other notifications and return only the first
        # launch one.
        if first_launch_notif:
            for notif in other_notifs:
                self.dismiss(notif)
            return [first_launch_notif]
        else:
            return other_notifs

    def dismiss(self, notification):
        """
        Marks a notification as dismiss to that it is not shown in the future.
        """
        settings  = self._get_banner_settings()
        notification._dismiss(settings)
        self._user_settings.store(self._BANNERS, settings)

    def reset(self):
        """
        Undismisses all the notifications.
        """
        self._user_settings.store(self._BANNERS, {})

    def _get_banner_settings(self):
        """
        Retrieves the banner settings section from the ``UserSettings``.

        :returns: Dictionary of settings.
        """
        return self._user_settings.retrieve(self._BANNERS) or {}
