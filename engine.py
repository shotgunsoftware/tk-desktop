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

from PySide import QtGui
from PySide import QtCore

from tank.platform import Engine


class DesktopEngine(Engine):
    def init_engine(self):
        if "SGTK_DESKTOP_ENGINE_INITIALIZED" in os.environ:
            return

        # Initialize PySide app
        QtGui.QApplication.setStyle("cleanlooks")
        self.app = QtGui.QApplication(sys.argv)
        css_file = os.path.join(self.disk_location, "resources", "dark.css")
        f = open(css_file)
        css = f.read()
        f.close()
        self.app.setStyleSheet(css)

    def post_app_init(self):
        if "SGTK_DESKTOP_ENGINE_INITIALIZED" in os.environ:
            return

        # Initialize System Tray
        tk_desktop = self.import_module("tk_desktop")
        self.systray = tk_desktop.SystemTrayWindow()

    def run(self):
        return self.app.exec_()

    def _log(self, level, msg, *args):
        fmt = "[%s] %s" % (level, msg)
        ret = args and (fmt % args) or fmt
        print ret

    def log_debug(self, msg, *args):
        self._log("DEBUG", msg, *args)

    def log_info(self, msg, *args):
        self._log("INFO", msg, *args)

    def log_warning(self, msg, *args):
        self._log("WARN", msg, *args)

    def log_error(self, msg, *args):
        self._log("ERROR", msg, *args)
