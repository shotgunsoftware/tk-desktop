# Copyright (c) 2024 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank_test.tank_test_base import TankTestBase, mock
from tank_test.tank_test_base import setUpModule  # noqa

from notifications import CentOS7DeprecationNotification

import os
import sys
import tempfile
import unittest


class TestNotificationsEL7_NotLinux(TankTestBase):
    def test(self):
        with mock.patch(
            "sgtk.util.is_linux",
            return_value=False,
        ):
            self.assertFalse(CentOS7DeprecationNotification.display_on_this_os())


@unittest.skipIf(
    sys.platform.startswith("win"),
    "Test does not work on Windows (permission denied when accessing opening a"
    "NamedTemporaryFile file)"
    "No problem: we tested useless test anyway",
)
@mock.patch("sgtk.util.is_linux", return_value=True)
class TestNotificationsEL7(TankTestBase):
    def test_file_does_not_exist(self, *patches):
        self.assertTrue(
            CentOS7DeprecationNotification.display_on_this_os(
                filename="file_does_not_exist"
            )
        )

    def test_file_is_not_ini(self, *patches):
        with tempfile.NamedTemporaryFile(mode="w+") as f:
            f.write("not an INI file")
            f.flush()
            self.assertTrue(
                CentOS7DeprecationNotification.display_on_this_os(
                    filename=f.name,
                )
            )

    def test_is_not_el_flavor(self, *patches):
        with tempfile.NamedTemporaryFile(mode="w+") as f:
            f.write(
                """
PRETTY_NAME="Ubuntu 23.10"
NAME="Ubuntu"
VERSION_ID="23.10"
VERSION="23.10 (Mantic Minotaur)"
VERSION_CODENAME=mantic
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=mantic
LOGO=ubuntu-logo
"""
            )
            f.flush()
            self.assertTrue(
                CentOS7DeprecationNotification.display_on_this_os(
                    filename=f.name,
                )
            )

    def test_is_centos7(self, *patches):
        with tempfile.NamedTemporaryFile(mode="w+") as f:
            f.write(
                """
NAME="CentOS Linux"
VERSION="7 (Core)"
ID="centos"
ID_LIKE="rhel fedora"
VERSION_ID="7"
PRETTY_NAME="CentOS Linux 7 (Core)"
ANSI_COLOR="0;31"
CPE_NAME="cpe:/o:centos:centos:7"
HOME_URL="https://www.centos.org/"
BUG_REPORT_URL="https://bugs.centos.org/"

CENTOS_MANTISBT_PROJECT="CentOS-7"
CENTOS_MANTISBT_PROJECT_VERSION="7"
REDHAT_SUPPORT_PRODUCT="centos"
REDHAT_SUPPORT_PRODUCT_VERSION="7"
"""
            )
            f.flush()
            self.assertTrue(
                CentOS7DeprecationNotification.display_on_this_os(
                    filename=f.name,
                )
            )

    def test_is_centos88(self, *patches):
        with tempfile.NamedTemporaryFile(mode="w+") as f:
            f.write(
                """
NAME="CentOS Linux"
VERSION="88 (Core)"
ID="centos"
ID_LIKE="rhel fedora"
VERSION_ID="88"
PRETTY_NAME="CentOS Linux 88 (Core)"
ANSI_COLOR="0;31"
CPE_NAME="cpe:/o:centos:centos:88"
HOME_URL="https://www.centos.org/"
BUG_REPORT_URL="https://bugs.centos.org/"

CENTOS_MANTISBT_PROJECT="CentOS-88"
CENTOS_MANTISBT_PROJECT_VERSION="88"
REDHAT_SUPPORT_PRODUCT="centos"
REDHAT_SUPPORT_PRODUCT_VERSION="88"
"""
            )
            f.flush()
            self.assertTrue(
                CentOS7DeprecationNotification.display_on_this_os(
                    filename=f.name,
                )
            )

    def test_is_rocky8(self, *patches):
        with tempfile.NamedTemporaryFile(mode="w+") as f:
            f.write(
                """
NAME="Rocky Linux"
VERSION="8.8 (Green Obsidian)"
ID="rocky"
ID_LIKE="rhel centos fedora"
VERSION_ID="8.8"
PLATFORM_ID="platform:el8"
PRETTY_NAME="Rocky Linux 8.8 (Green Obsidian)"
ANSI_COLOR="0;32"
LOGO="fedora-logo-icon"
CPE_NAME="cpe:/o:rocky:rocky:8:GA"
HOME_URL="https://rockylinux.org/"
BUG_REPORT_URL="https://bugs.rockylinux.org/"
SUPPORT_END="2029-05-31"
ROCKY_SUPPORT_PRODUCT="Rocky-Linux-8"
ROCKY_SUPPORT_PRODUCT_VERSION="8.8"
REDHAT_SUPPORT_PRODUCT="Rocky Linux"
REDHAT_SUPPORT_PRODUCT_VERSION="8.8"
"""
            )
            f.flush()
            self.assertFalse(
                CentOS7DeprecationNotification.display_on_this_os(
                    filename=f.name,
                )
            )

    def test_is_rocky9(self, *patches):
        with tempfile.NamedTemporaryFile(mode="w+") as f:
            f.write(
                """
NAME="Rocky Linux"
VERSION="9.3 (Blue Onyx)"
ID="rocky"
ID_LIKE="rhel centos fedora"
VERSION_ID="9.3"
PLATFORM_ID="platform:el9"
PRETTY_NAME="Rocky Linux 9.3 (Blue Onyx)"
ANSI_COLOR="0;32"
LOGO="fedora-logo-icon"
CPE_NAME="cpe:/o:rocky:rocky:9::baseos"
HOME_URL="https://rockylinux.org/"
BUG_REPORT_URL="https://bugs.rockylinux.org/"
SUPPORT_END="2032-05-31"
ROCKY_SUPPORT_PRODUCT="Rocky-Linux-9"
ROCKY_SUPPORT_PRODUCT_VERSION="9.3"
REDHAT_SUPPORT_PRODUCT="Rocky Linux"
REDHAT_SUPPORT_PRODUCT_VERSION="9.3"
"""
            )
            f.flush()
            self.assertFalse(
                CentOS7DeprecationNotification.display_on_this_os(
                    filename=f.name,
                )
            )

    def test_is_rhel7(self, *patches):
        with tempfile.NamedTemporaryFile(mode="w+") as f:
            f.write(
                """
NAME="Red Hat Enterprise Linux"
VERSION="7 (Core)"
ID="rhel"
ID_LIKE="rhel"
VERSION_ID="7"
PRETTY_NAME="Red Hat Enterprise Linux 7 (Core)"
CPE_NAME="cpe:/o:rhel:rhel:7"

REDHAT_SUPPORT_PRODUCT="rhel"
REDHAT_SUPPORT_PRODUCT_VERSION="7"
"""
            )
            f.flush()
            self.assertTrue(
                CentOS7DeprecationNotification.display_on_this_os(
                    filename=f.name,
                )
            )

    def test_is_weird_el7(self, *patches):
        with tempfile.NamedTemporaryFile(mode="w+") as f:
            f.write(
                """
NAME="Weird Dist"
ID="weird"
VERSION_ID="7.7"
PLATFORM_ID="platform:el7"
"""
            )
            f.flush()
            self.assertTrue(
                CentOS7DeprecationNotification.display_on_this_os(
                    filename=f.name,
                )
            )
