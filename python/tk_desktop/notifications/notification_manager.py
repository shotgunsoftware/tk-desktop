# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from .configuration_update_notification import ConfigurationUpdateNotification
from .first_launch_notification import FirstLaunchNotification
from .startup_update_notification import StartupUpdateNotification


class NotificationsManager(object):

    _BANNERS = "banners"

    def __init__(self, user_settings, descriptor, engine):
        self._user_settings = user_settings
        self._descriptor = descriptor
        self._engine = engine

    def get_notifications(self):
        banner_settings = self._get_banner_settings()

        first_launch_notif = None # FirstLaunchNotification.create(banner_settings)
        config_update_notif = ConfigurationUpdateNotification.create(banner_settings, self._descriptor)
        startup_update_notif = StartupUpdateNotification.create(banner_settings, self._engine)

        if first_launch_notif:
            # Skip the config and startup updates on first launch.
            if config_update_notif:
                self.dismiss(config_update_notif)
            if startup_update_notif:
                self.dismiss(startup_update_notif)

            yield first_launch_notif
        else:
            # Report any updates that are relevant.
            if config_update_notif:
                yield config_update_notif
            if startup_update_notif:
                yield startup_update_notif

    def dismiss(self, notification):
        settings  = self._get_banner_settings()
        notification._dismiss(settings)
        self._user_settings.store(self._BANNERS, settings)

    def reset(self):
        self._user_settings.store(self._BANNERS, {})

    def _get_banner_settings(self):
        return self._user_settings.retrieve(self._BANNERS) or {}
