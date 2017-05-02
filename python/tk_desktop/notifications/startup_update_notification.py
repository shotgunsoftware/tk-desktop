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


class StartupUpdateNotification(Notification):
    """
    Notification for `tk-framework-desktopstartup` updates.
    """

    _DESKTOPSTARTUP_UPDATES_ID = "desktop-startup.updates"

    def __init__(self, engine):
        """
        :param engine: Toolkit engine.
        """
        self._engine = engine

    @classmethod
    def create(cls, banner_settings, engine):
        """
        Notification factory for the ``StartupUpdateNotification`` class.

        If the engine provides a startup descriptor with a version and release url, an instance
        of this class will be returned. Otherwise, ``None`` will be returned.

        Note that if this notification has been dismissed in the past, the method will also
        return ``None``.

        :param banner_settings: Dictionary of banner settings.
        :param engine: Toolkit engine.

        :returns: A :class:`StartupUpdateNotification` instance, or ``None``.
        """
        if not engine.startup_descriptor:
            logger.debug("Version of startup code doesn't provide descriptor.")
            return None

        if not engine.startup_descriptor.version:
            logger.debug("Startup descriptor doesn't provide a version")
            return None

        if engine.startup_descriptor.version.lower() in ["undefined", "head"]:
            logger.debug(
                "Startup descriptor version is '%s', skipping.", engine.startup_descriptor.version
            )
            return None

        if not engine.startup_descriptor.changelog[1]:
            logger.debug(
                "Startup descriptor doesn't have a release url."
            )
            return None

        if banner_settings.get(
            cls._DESKTOPSTARTUP_UPDATES_ID, {}
        ).get(engine.startup_descriptor.version, False):
            logger.debug(
                "This release has already been dismissed."
            )
            return None
        else:
            logger.debug(
                "Startup update available."
            )
            return StartupUpdateNotification(engine)

    @property
    def message(self):
        """
        Message to display.
        """
        return (
            "<b>Shotgun Desktop</b> has been updated. "
            "<a href='{0}'>Click here</a> to learn more."
        ).format(self._engine.startup_descriptor.changelog[1])

    def _dismiss(self, banner_settings):
        """
        Updates the ``banner_settings`` so this notification does not come back in the future.

        :param banner_settings: Dictionary of the banners settings.
        """
        banner_settings.setdefault(
            self._DESKTOPSTARTUP_UPDATES_ID, {}
        )[self._engine.startup_version] = True
