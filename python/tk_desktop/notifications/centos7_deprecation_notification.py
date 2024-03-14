# Copyright (c) 2023 Autodesk.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import configparser
import re

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

        if not cls.display_on_this_os():
            logger.debug("CentOS 7 banner is out of context in this OS.")
            return

        logger.debug("CentOS 7 deprecation banner available")
        return CentOS7DeprecationNotification()

    @staticmethod
    def display_on_this_os(filename="/etc/os-release"):
        """
        returns True if OS is EL7. Any EL if version 7
        returns True if OS is CentOS. Any CentOS versions
        returns True if unable to identify the OS/flavor/version
        """

        if not sgtk.util.is_linux():
            logger.debug("Not a Linux OS")
            return False

        linux_util = LinuxOSRelease()

        if not linux_util.load(filename):
            # we know it's Linux but can't read the file: let's display the info
            return True

        if not linux_util.is_el_flavor():
            # We only support EL distributions so let's display the notification
            return True

        if linux_util.is_centos():
            # We only support EL distributions so let's display the notification
            return True

        # At this point, we know it's a EL but not CentOS
        # we want to match everything version 7
        version_tuple = linux_util.get_entry("VERSION_ID", default="0").split(".")
        if version_tuple[0] == "7" or linux_util.get_entry("CPE_NAME").endswith(":7"):
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


class LinuxOSRelease:
    """
    Read the /etc/os-release and provide simple utily tools to identifies flavor
    and version of the Linux distribution

    https://www.man7.org/linux/man-pages/man5/os-release.5.html

    Use a INI reader and customize a bit... It would be better to load the file into a shell and read the environment ...
    """

    def __init__(self):
        self._config = None
        self.reg_split_list = re.compile(" +")

    def load(self, filename="/etc/os-release"):
        try:
            file_data = open(filename).read()
        except IOError:
            logger.debug("Not an EL distribution")
            return False

        config = configparser.ConfigParser()
        try:
            config.read_string("[root]\n" + file_data)
        except configparser.ParsingError:
            return False

        self._config = config["root"]
        return True

    def get_entry(self, name, default="", auto_lower=True):
        data = self._config.get(name, default)
        if data.strip().startswith('"') and data.strip().endswith('"'):
            data = data[1:-1]

        if auto_lower:
            data = data.lower()

        return data

    def get_list_items(self, name):
        data = self.get_entry(name)
        return self.reg_split_list.split(data)

    def is_el_flavor(self):
        dist_ids = self.get_list_items("ID_LIKE")
        if "rhel" in dist_ids:
            return True

        platform_id = self.get_entry("PLATFORM_ID")
        if platform_id.startswith("platform:el"):
            return True

        return False

    def is_centos(self):
        if self.get_entry("ID") == "centos":
            return True

        if ":centos:" in self.get_entry("CPE_NAME"):
            return True

        return False
