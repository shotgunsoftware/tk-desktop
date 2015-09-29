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
import subprocess

from sgtk.platform.qt import QtGui
from sgtk.platform.qt import QtCore

from .ui import update_project_config
from .wait_screen import WaitScreen
from .error_dialog import ErrorDialog


class UpdateProjectConfig(QtGui.QWidget):
    update_finished = QtCore.Signal(bool)

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        # initialize variables
        self.python_interpreter_path = None
        self.core_python_path = None
        self.configuration_path = None
        self.project = None

        # setup the gui
        self.ui = update_project_config.Ui_UpdateProjectConfig()
        self.ui.setupUi(self)
        self.ui.button.clicked.connect(self.do_config)
        self._parent = parent

        # hide outcome messages
        self.ui.success.setVisible(False)

        # resize with parent
        filter = ResizeEventFilter(self._parent)
        filter.resized.connect(self._on_parent_resized)
        self._parent.installEventFilter(filter)

        # start off hidden
        self.setVisible(False)

    def set_project_info(self, path_to_python, core_python, config_path, project):
        # keep the info
        self.python_interpreter_path = path_to_python
        self.core_python_path = core_python
        self.configuration_path = config_path
        self.project = project

        # reset the ui
        self.ui.label.setVisible(True)
        self.ui.success.setVisible(False)
        self.ui.button.setEnabled(True)

    def do_config(self):
        # disable the button
        self.ui.button.setEnabled(False)

        # figure out path to script to execute
        apps_copy_script = os.path.realpath(
            os.path.join(__file__, "..", "..", "..", "add_desktop_to_project.py"))

        # put together the arguments to the command
        args = [
            self.python_interpreter_path,
            apps_copy_script,
            "--core_python_path", self.core_python_path,
            "--configuration_path", self.configuration_path,
            "--project_id", str(self.project["id"]),
        ]

        try:
            # show a message to indicate that something is happening
            wait = WaitScreen("Updating project config,", "hold on...", self)
            wait.show()
            QtGui.QApplication.instance().processEvents()

            # run hidden on windows
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            # call it
            python_process = subprocess.Popen(
                args,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                startupinfo=startupinfo
            )
            (stdout, stderr) = python_process.communicate()
        finally:
            # make sure the wait screen gets hidden
            wait.hide()

        if python_process.returncode == 0:
            # success
            self.ui.label.setVisible(False)
            self.ui.success.setVisible(True)
            self.update_finished.emit(True)
        else:
            # failure
            message = """
                <html><head/><body>
                    <p><span style=" font-size:16pt;">
                        There was an error adding the desktop engine:
                    </span></p>
                    <p>
                        <pre>%s</pre>
                    </p>
                    <p><span style=" font-size:14pt;">
                        Please let support@shotgunsoftware.com know.
                    </span></p>
                </body></html>
            """ % stderr

            # show the error
            e = ErrorDialog("Toolkit Error", message, self)
            e.exec_()

            # set the button up for another attempt
            self.ui.button.setText("Try Again")
            self.ui.button.setEnabled(True)

            # let listeners know we finished
            self.update_finished.emit(False)

    def _on_parent_resized(self):
        """
        Special slot hooked up to the event filter.
        When associated widget is resized this slot is being called.
        """
        # resize overlay
        self.resize(self._parent.size())


class ResizeEventFilter(QtCore.QObject):
    """
    Event filter which emits a resized signal whenever
    the monitored widget resizes. This is so that the overlay wrapper
    class can be informed whenever the Widget gets a resize event.
    """
    resized = QtCore.Signal()

    def eventFilter(self,  obj,  event):
        # peek at the message
        if event.type() == QtCore.QEvent.Resize:
            # re-broadcast any resize events
            self.resized.emit()
        # pass it on!
        return False
