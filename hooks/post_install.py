# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
import time
import subprocess
import sys


class PostInstall(sgtk.get_hook_baseclass()):
    """
    Ran after this desktop version is installed. It is run to make sure that
    the Shotgun API version is the one bundled with core v0.16.0 or higher.
    This test is required because the Desktop app historically didn't restart
    the Desktop app after updating core. Because of this, upgrading to core
    v0.16.0 meant that the wrong version of shotgun_api3 would be in memory.
    Therefore, even though the code was updated and the newer engine downloaded,
    we were actually still running the old code. This causes a crash in the
    tk-desktop engine because it expects the shotgun_api3 module to have
    the AuthenticationFault class. When we're running into this situation,
    we'll simply make sure we are in Desktop and if we are, we'll import
    the splash screen, let the user know an upgrade took place and reboot the
    app.
    """

    def _is_wrong_shotgun_api3_version(self):
        """
        Checks if we have the wrong version of shotgun_api3, ie
        AuthenticationFault doesn't exist.

        :returns True if we have the wrong version, False otherwise.
        """
        from tank_vendor import shotgun_api3
        return not hasattr(shotgun_api3, "AuthenticationFault")

    def _get_shotgun_desktop(self):
        """
        Returns the shotgun_desktop module, if available.

        :returns: The shotgun_desktop module or None.
        """
        try:
            import shotgun_desktop
            return shotgun_desktop
        except ImportError:
            return None

    def _reboot_app(self, shotgun_desktop):
        """
        Reboots the application. Calls sys.exit so this method never actually
        returns.

        :param shotgun_desktop: The shotgun_desktop module.
        """
        splash = shotgun_desktop.splash.Splash()
        splash.show()
        splash.raise_()
        splash.activateWindow()
        # Provide a countdown so the user knows that the desktop app is
        # being restarted on purpose because of a core update. Otherwise,
        # the user would get a flickering splash screen that from the user
        # point of view looks like the app is redoing work it already did by
        # mistake. This makes the behavior explicit.
        for i in range(3, 0, -1):
            splash.set_message("Core updated. Restarting desktop in %d seconds..." % i)
            time.sleep(1)
        # Very important to set close_fds otherwise the websocket server file descriptor
        # will be shared with the child process and it prevent restarting the server
        # after the process closes.
        # Solution was found here: http://stackoverflow.com/a/13593715
        subprocess.Popen(sys.argv, close_fds=True)
        sys.exit(0)

    def execute(self, *args, **kwargs):
        """
        Reboots the app if we have the wrong version of the Shotgun API and
        we're running the Shotgun Desktop.

        :raises Exception: Raised if we have then wrong version of Shotgun but are
            not running the Desktop. As of this writing, there's no reason for this
            to happen.
        """
        if self._is_wrong_shotgun_api3_version():
            shotgun_desktop = self._get_shotgun_desktop()
            if shotgun_desktop:
                self._reboot_app(shotgun_desktop)
            else:
                raise Exception("Wrong version of Shotgun API3. AuthenticationFault not accessible.")
