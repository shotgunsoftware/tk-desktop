# Copyright (c) 2026 Autodesk.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


import sys
import typing

from .notification import Notification

import sgtk

logger = sgtk.platform.get_logger(__name__)


class Python39DeprecationNotification(Notification):
    """
    Notification for Python 3.9 deprecation.
    """

    _DEPRECATION_ID = "deprecation-notification-python39"

    @classmethod
    def create(cls, banner_settings: typing.Dict, engine):
        """
        Notification factory for Python 3.9 deprecation.

        :param banner_settings: Dictionary of banner settings.
        :param engine: tk-desktop engine instance.

        :returns: A :class:`Python39DeprecationNotification` instance, or ``None``.
        """

        if banner_settings.get(cls._DEPRECATION_ID, False):
            logger.debug("Python 3.9 banner has already been dismissed")
            return

        include_sgd = not cls.is_app_version_newer(engine)
        if not include_sgd and not cls.is_python_deprecated():
            logger.debug("Python 3.9 banner not needed for this Desktop/Python")
            return

        logger.debug("Python 3.9 deprecation banner available")

        return Python39DeprecationNotification(include_sgd=include_sgd)

    def __init__(self, include_sgd=True):
        self.include_sgd = include_sgd

    @property
    def message(self):
        """
        Message to display.
        """

        url = "https://community.shotgridsoftware.com/t/important-notice-for-march-15-2027-end-of-support-for-shotgrid-desktop-1-8-and-for-python-3-9-in-toolkit/"

        add_sgd1, add_sgd2 = ("", "")
        if self.include_sgd:
            add_sgd1 = " and <b>ShotGrid Desktop 1.8</b>"
            add_sgd2 = " and <b>FPT Desktop 1.9</b>+"

        return f"""
            On <b>March 15, 2027</b> Autodesk stops supporting
            <b>Python 3.9</b>{add_sgd1} in Toolkit, and compatibility ends on
            <b>March 15, 2028</b>.

            Please plan to update to <b>Python 3.10</b>+{add_sgd2}.

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

    @classmethod
    def is_app_version_newer(cls, engine):
        """
        Checks whether the running FPT Desktop app is 1.9 or newer.

        :param engine: tk-desktop engine instance.

        :returns: ``True`` if the app version is 1.9 or newer, ``False`` if it
            is older or cannot be determined.
        """
        app_version = getattr(engine, "app_version", None)
        if not app_version:
            return False

        try:
            return not sgtk.util.is_version_older(app_version, "v1.9.0")
        except Exception:
            logger.exception(f"Could not parse app version {app_version}")

        return False

    @classmethod
    def is_python_deprecated(cls):
        """
        Checks whether FPT Desktop is running on Python 3.9 or older.
        """
        return sys.version_info[:2] < (3, 10)
