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
        Yields a list of notifications.

        If the FirstLaunchNotitification hasn't been dismissed yet, every other notification
        will be dismissed.

        :returns: An array on :class:``Notification`` objects.
        """
        banner_settings = self._get_banner_settings()

        first_launch_notif = FirstLaunchNotification.create(banner_settings)
        config_update_notif = ConfigurationUpdateNotification.create(banner_settings, self._descriptor)
        startup_update_notif = StartupUpdateNotification.create(banner_settings, self._engine)
        desktop_notif = DesktopNotification.create(banner_settings, self._engine)

        if first_launch_notif:
            # Skip the config and startup updates on first launch.
            if config_update_notif:
                self.dismiss(config_update_notif)
            if startup_update_notif:
                self.dismiss(startup_update_notif)
            if desktop_notif:
                self.dismiss(desktop_notif)

            yield first_launch_notif
        else:
            # Report any updates that are relevant.
            if config_update_notif:
                yield config_update_notif
            if startup_update_notif:
                yield startup_update_notif
            if desktop_notif:
                yield desktop_notif

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
