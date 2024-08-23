# Copyright (c) 2024 Autodesk.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


import typing

from .notification import Notification

import sgtk
logger = sgtk.platform.get_logger(__name__)


class Python37DeprecationNotification(Notification):
    """
    Notification for Python 3.7 deprecation.
    """

    _DEPRECATION_ID = "deprecation-notification-python37"

    @classmethod
    def create(cls, banner_settings: typing.Dict, engine):
        """
        Notification factory for Python 3.7 deprecation.

        :param banner_settings: Dictionary of banner settings.

        :returns: A :class:`Python37DeprecationNotification` instance, or ``None``.
        """

        if banner_settings.get(cls._DEPRECATION_ID, False):
            logger.debug("Python 3.7 banner has already been dismissed")
            return

        try:
            import packaging.version
            if packaging.version.parse(engine.app_version) >= packaging.version.parse("1.8"):
                # TODO OK for SGD but what about Python version in projects????
                logger.debug("Python 3.7 banner dismissed because app version is higher than 1.7")
                return
        except ImportError:
            logger.exception("Could not import packaging module")
        except packaging.version.InvalidVersion:
            logger.exception(f"Could not import parse core version {engine.app_version}")

        logger.debug("Python 3.7 deprecation banner available")
        return Python37DeprecationNotification()

    @property
    def message(self):
        """
        Message to display.
        """

        url = "https://community.shotgridsoftware.com/t/important-notice-for-end-of-......." # TODO

        return f"""
            On <b>February 28th, 2025</b> Autodesk is ending support for
            <b>Python 3.7</b> in FPTR Toolkit and ending support for
            <b>ShotGrid Desktop 1.7</b>.

            Update to <b>Python 3.9, 3.10, or 3.11</b> before this date to avoid
            disruption. For desktop app users, please update to version 1.8 or
            newer.

            Read more <a href="{url}">here</a>.
        """

    @property
    def unique_id(self):
        """
        Returns the unique identifier of a notification.
        """
        return self._DEPRECATION_ID

    def _dismiss(self, banner_settings):
        """
        Updates the ``banner_settings`` so this notification does not come back in the future.

        :param banner_settings: Dictionary of the banners settings.
        """
        banner_settings[self._DEPRECATION_ID] = True
