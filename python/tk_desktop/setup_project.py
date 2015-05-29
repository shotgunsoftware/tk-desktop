# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from sgtk.platform.qt import QtGui
from sgtk.platform.qt import QtCore
from sgtk import TankErrorProjectIsSetup
from error_dialog import ErrorDialog


from .ui import setup_project

import sgtk
from tank_vendor.shotgun_authentication import ShotgunAuthenticator


adminui = sgtk.platform.import_framework("tk-framework-adminui", "setup_project")


class SetupProject(QtGui.QWidget):
    setup_finished = QtCore.Signal(bool)

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.ui = setup_project.Ui_SetupProject()
        self.ui.setupUi(self)
        self.ui.button.clicked.connect(self.do_setup)
        self._parent = parent
        self.project = None

        filter = ResizeEventFilter(self._parent)
        filter.resized.connect(self._on_parent_resized)
        self._parent.installEventFilter(filter)

        self.setVisible(False)

    def do_setup(self):
        # Only toggle top window if it used to be off (to avoid un-necessary window flicker in case it was already off) 
        is_on_top = self._is_on_top()

        try:
            if is_on_top: 
                self._set_top_window_on_top(False)

            setup = adminui.SetupProjectWizard(self.project, self)

            ret = setup.exec_()
            self.setup_finished.emit(ret == setup.Accepted)

        except TankErrorProjectIsSetup, e:
            error_dialog = ErrorDialog("Toolkit Setup Error",
                                       "You are trying to set up a project which has already been set up\n\n"
                                       "To re-setup a project, in a terminal window type: tank setup_project --force\n\n"
                                       "Alternatively, you can go into shotgun and clear the Project.tank_name field\n"
                                       "and delete all pipeline configurations for your project.")
            ret = error_dialog.exec_()

        finally:
            if is_on_top: 
                self._set_top_window_on_top(True)

    def _is_on_top(self):
        """
        Check if top window is always on top
        :returns: True if top window is always on top
        """
        is_on_top = False
        
        flags = self.window().windowFlags()
        is_on_top = (flags & QtCore.Qt.WindowStaysOnTopHint) == QtCore.Qt.WindowStaysOnTopHint

        return is_on_top

    def _set_top_window_on_top(self, state):
        """
        Set always on top setting for top window.
        Since Qt re-parents when changing this flag, the window gets back behind everything,
        therefore we also need to bring it back to the front when toggling the state.

        :param state: Boolean Whether to set the window always on top or not.
        """
        flags = self.window().windowFlags()

        if state:
            self.window().setWindowFlags(flags | QtCore.Qt.WindowStaysOnTopHint)
        else:
            self.window().setWindowFlags(flags & ~QtCore.Qt.WindowStaysOnTopHint)

        self.window().show()
        self.window().raise_()
        self.window().activateWindow()

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
