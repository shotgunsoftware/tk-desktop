# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook to launch the python interpreter for a specific project.
"""

import os
import sys
import subprocess

import tank
from tank import Hook


class LaunchPython(Hook):
    def execute(self, project_python, pickle_data_path, utilities_module_path):
        """
        Launch the python process that will start the project specific tk-desktop
        engine and communicate back to the gui proxy.

        :param project_python: (str) The path to the python executable to run
        :param pickle_data_path: (str) The path to the data needed to start the engine
        :param utilities_module_path: (str) The path to a utilities module can start the engine
        """
        # get the path to the python_bootstrap.py file in this directory
        bootstrap = self.path_to_bootstrap()

        # run hidden on windows
        startupinfo = None
        if sys.platform == "win32" and not os.environ.get("SGTK_DESKTOP_BACKGROUND_CONSOLE"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        # launch, running the bootstrap and passing through the startup data
        args = [project_python, bootstrap, "-d", pickle_data_path, "-u", utilities_module_path]
        self.parent.logger.debug("launching %s", " ".join(["'%s'" % arg for arg in args]))

        # Very important to set close_fds otherwise the websocket server file descriptor
        # will be shared with the child process and it prevent restarting the server
        # after the process closes.
        # Solution was found here: http://stackoverflow.com/a/13593715
        subprocess.Popen(args, startupinfo=startupinfo, close_fds=True)

    def path_to_bootstrap(self):
        """
        Return the path to the default bootstrap

        See bootstrap.py for an example of how to properly start the desktop engine
        in the python subprocess.
        """
        engine_path = tank.platform.get_engine_path(
            self.parent.name, self.parent.sgtk, self.parent.context)
        return os.path.join(engine_path, "bootstrap.py")
