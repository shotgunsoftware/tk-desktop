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

    _DEPRECATION_ID = "python37-breaking-changes"

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

        logger.debug("Python 3.7 deprecation banner available")

        return Python37DeprecationNotification(
            include_sgd=not cls.is_app_version_newer(engine),
        )

    def __init__(self, include_sgd=True):
        self.include_sgd = include_sgd

    @property
    def message(self):
        """
        Message to display.
        """

        url = "https://community.shotgridsoftware.com/t/20515"

        add_fptr1, add_fptr2 = ("", "")
        if self.include_sgd:
            add_fptr1 = " and <b>ShotGrid Desktop 1.7</b>"
            add_fptr2 = " and <b>FPT Desktop v2.1.0</b>"

        return f"""
            End of March 2026 - Breaking Changes for <b>Python 3.7</b>
            {add_fptr1}

            Make sure to update to <b>Python 3.11</b>{add_fptr2}, or any other
            supported versions, before  April 1, 2026 to avoid disruption.

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
        try:
            import packaging.version

            v1 = packaging.version.parse(engine.app_version)
            v2 = packaging.version.parse("1.8")
            return v1 >= v2
        except ImportError:
            logger.exception("Could not import packaging module")
        except packaging.version.InvalidVersion:
            logger.exception(
                f"Could not import parse core version {engine.app_version}"
            )
        except AttributeError:
            # no app_version field available
            pass

        return False
