# Copyright (c) 2023 Autodesk.
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

        if not sgtk.util.is_linux():
            logger.debug("CentOS 7 banner is out of context in this OS.")
            return

        try:
            os_data = open("/etc/os-release").read().lower()
        except IOError:
            logger.debug("CentOS 7 banner is out of context in this Linux distribution.")
            return

        if "centos" not in os_data and "7" not in os_data:
            logger.debug("CentOS 7 banner is out of context in this Linux distribution (not a EL7 system).")
            return

        logger.debug("CentOS 7 deprecation banner available")
        return CentOS7DeprecationNotification()

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
