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


class ConfigurationUpdateNotification(Notification):
    """
    Notification for updates to the configuration.
    """

    _CONFIG_UPDATES = "configuration.updates"

    def __init__(self, descriptor):
        """
        :oaram descriptor: Descriptor for the configuration.
        """
        self._descriptor = descriptor

    @classmethod
    def create(cls, banner_settings, descriptor):
        """
        Notification factory for this class.

        If the pipeline configuration provided a descriptor and it has a release notes url, an
        instance of this class will be returned. Otherwise, ``None`` will be returned.

        Note that if this notification has been dismissed in the past, the method will also
        return ``None``.

        :param banner_settings: Dictionary of banner_settings.
        :param engine: Toolkit engine.
        """

        # If there is no descriptor.
        if not descriptor:
            logger.debug("Configuration has no descriptor.")
            return

        (_, url) = descriptor.changelog

        # Or no documentation url for it.
        if not url:
            logger.debug("Configuration descriptor has no release notes URL.")
            return

        # If the banner hasn't been set yet.
        if banner_settings.get(cls._CONFIG_UPDATES, {}).get(descriptor.get_uri(), False):
            logger.debug("Configuration update notification has already been dismissed.")
            return None
        else:
            logger.debug("Configuration update notification is available.")
            return ConfigurationUpdateNotification(descriptor)

    @property
    def message(self):
        """
        Message to display.
        """
        return "Your <b>configuration</b> has been updated. <a href='{}'>Click here</a> to learn more.".format(
            self._descriptor.changelog[1]
        )

    @property
    def unique_id(self):
        """
        Returns the unique identifier of a notification.
        """
        return self._CONFIG_UPDATES + self._descriptor.get_uri()

    def _dismiss(self, banner_settings):
        """
        Updates the ``banner_settings`` so this notification does not come back in the future.

        :param banner_settings: Dictionary of the banners settings.
        """
        banner_settings.setdefault(self._CONFIG_UPDATES, {})[self._descriptor.get_uri()] = True
