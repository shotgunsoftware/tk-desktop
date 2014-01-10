# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys
import logging

from PySide import QtGui

from tank.platform import Engine


class DesktopEngine(Engine):
    def __init__(self, *args, **kwargs):
        # initialize engine logging
        platform_lookup = {
            'darwin': os.path.join(os.path.expanduser("~"), "Library", "Logs", "Shotgun", "tk-desktop.log"),
            'win32': os.path.join(os.environ.get("APPDATA", "Foo"), "Shotgun", "tk-desktop.log"),
            'linux': None,
        }

        fname = platform_lookup.get(sys.platform)

        if fname is None:
            raise NotImplementedError("Unknown platform: %s" % sys.platform)

        log_dir = os.path.dirname(fname)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self._logger = logging.getLogger("tk-desktop")
        handler = logging.handlers.RotatingFileHandler(fname, maxBytes=1024*1024, backupCount=5)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

        # Now continue with the standard initialization
        Engine.__init__(self, *args, **kwargs)

    def init_engine(self):
        if self.get_setting("debug_logging", False):
            self._logger.setLevel(logging.DEBUG)

        if "SGTK_DESKTOP_ENGINE_INITIALIZED" in os.environ:
            return

        # Initialize PySide app
        self.app = QtGui.QApplication.instance()
        if self.app is None:
            QtGui.QApplication.setStyle("cleanlooks")
            self.app = QtGui.QApplication(sys.argv)
            css_file = os.path.join(self.disk_location, "resources", "dark.css")
            f = open(css_file)
            css = f.read()
            f.close()
            self.app.setStyleSheet(css)

        # update the icon
        icon = QtGui.QIcon(":res/default_systray_icon")
        self.app.setWindowIcon(icon)

    def post_app_init(self):
        if "SGTK_DESKTOP_ENGINE_INITIALIZED" in os.environ:
            # Already initialized, just reloading engine in a new context
            return

        # Initialize System Tray
        tk_desktop = self.import_module("tk_desktop")
        self.systray = tk_desktop.SystemTrayWindow()

    def run(self):
        return self.app.exec_()

    def log_debug(self, msg, *args):
        self._logger.debug(msg, *args)

    def log_info(self, msg, *args):
        self._logger.info(msg, *args)

    def log_warning(self, msg, *args):
        self._logger.warn(msg, *args)

    def log_error(self, msg, *args):
        self._logger.error(msg, *args)
