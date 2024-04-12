# Copyright (c) 2023 Autodesk.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


import platform
import re
import sys

from .notification import Notification
from . import platform_os_release
import sgtk

logger = sgtk.platform.get_logger(__name__)


class CentOS7DeprecationNotification(Notification):
    """
    Notification for CentOS 7 deprecation.
    """

    _CENTOS7_DEPRECATION_ID = "centos7-deprecation-notification"

    @classmethod
    def create(cls, banner_settings):
        """
        Notification factory for CentOS 7 deprecation.

        :param banner_settings: Dictionary of banner settings.

        :returns: A :class:`CentOS7DeprecationNotification` instance, or ``None``.
        """

        if banner_settings.get(cls._CENTOS7_DEPRECATION_ID, False):
            logger.debug("CentOS 7 banner has already been dismissed.")
            return

        if not cls.display_on_this_os():
            logger.debug("CentOS 7 banner is out of context in this OS.")
            return

        logger.debug("CentOS 7 deprecation banner available")
        return CentOS7DeprecationNotification()

    @staticmethod
    def display_on_this_os():
        """
        rely on https://www.man7.org/linux/man-pages/man5/os-release.5.html

        returns True if OS is EL7. Any EL if version 7
        returns True if OS is CentOS. Any CentOS versions
        returns True if unable to identify the OS/flavor/version
        """

        if not sgtk.util.is_linux():
            logger.debug("Not a Linux OS")
            return False

        if sys.version_info[:2] < (3, 10):
            platform_mod = platform_os_release
        else:
            platform_mod = platform

        try:
            info = platform_mod.freedesktop_os_release()
        except OSError:
            return True

        if not info or "ID" not in info:
            # we know it's Linux but unable to retrieve os-release info
            return True

        os_ids = [info["ID"]]
        if "ID_LIKE" in info:
            os_ids.extend(info.get("ID_LIKE", "").split())

        if "rhel" not in os_ids:
            # We only support EL distributions
            return True

        if info["ID"] == "centos":
            # CentOS 7 will be the last supported distribution version
            return True

        # At this point, we know it's EL but not CentOS

        if re.match("^7(\\.\\d.*)?$", info.get("VERSION_ID", "")):
            # EL7 system
            return True

        return False

    @property
    def message(self):
        """
        Message to display.
        """

        return """
            ShotGrid is ending support for <b>CentOS</b> in SG Toolkit and
            Desktop on <b>November 1st 2024</b>.
            Update to <b>Rocky Linux 8.5+</b> before this date  to avoid
            disruption.
            Read more <a href="{url}">here</a>.
        """.format(
            url="https://community.shotgridsoftware.com/t/important-notice-for-end-of-october-2024-end-of-support-for-centos-sg-toolkit-and-sg-desktop/",
        )

    @property
    def unique_id(self):
        """
        Returns the unique identifier of a notification.
        """
        return self._CENTOS7_DEPRECATION_ID

    def _dismiss(self, banner_settings):
        """
        Updates the ``banner_settings`` so this notification does not come back in the future.

        :param banner_settings: Dictionary of the banners settings.
        """
        banner_settings[self._CENTOS7_DEPRECATION_ID] = True
