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

from tank import Hook


class LaunchPython(Hook):
    def execute(self, project_python, pickle_data_path, utilities_module_path):
        """
        Launch the python process that will start the project specific tk-desktop
        engine and communicate back to the gui proxy.
        """
        # get the path to the python_bootstrap.py file in this directory
        bootstrap = self.path_to_bootstrap()

        # run hidden on windows
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        # launch, running the bootstrap and passing through the startup data
        args = [project_python, bootstrap, "-d", pickle_data_path, "-u", utilities_module_path]
        self.parent.log_debug("launching %s" % " ".join(["'%s'" % arg for arg in args]))
        subprocess.Popen(args, startupinfo=startupinfo)

    def path_to_bootstrap(self):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), "python_bootstrap.py")
