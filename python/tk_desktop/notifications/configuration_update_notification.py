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


class ConfigurationUpdateNotification(Notification):

    _CONFIG_UPDATES = "configuration.updates"

    def __init__(self, descriptor):
        self._descriptor = descriptor

    @classmethod
    def create(cls, banner_settings, descriptor):

        # If there is no descriptor.
        if not descriptor:
            return

        (_, url) = descriptor.changelog

        # Or no documentation url for it.
        if not url:
            return

        # If the banner hasn't been set yet.
        if banner_settings.get(cls._CONFIG_UPDATES, {}).get(descriptor.get_uri(), False):
            return None
        else:
            return ConfigurationUpdateNotification(descriptor)

    @property
    def message(self):
        return "Your <b>configuration</b> has been updated. <a href='{}'>Click here</a> to learn more.".format(
            self._descriptor.changelog[1]
        )

    def _dismiss(self, banner_settings):
        banner_settings.setdefault(self._CONFIG_UPDATES, {})[self._descriptor.get_uri()] = True

