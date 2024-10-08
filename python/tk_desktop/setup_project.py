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
from .error_dialog import ErrorDialog

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

    def do_setup(self, show_help=False):
        try:
            # First check to see if the current user
            self._validate_user_permissions()

            if show_help:
                # Display the Help popup if requested.
                self.show_help_popup()

            setup = adminui.SetupProjectWizard(self.project, self)

            ret = setup.exec_()
            self.setup_finished.emit(ret == QtGui.QDialog.Accepted)

        except TankErrorProjectIsSetup as e:
            error_dialog = ErrorDialog(
                "Toolkit Setup Error",
                "You are trying to set up a project which has already been set up\n\n"
                "To re-setup a project, in a terminal window type: tank setup_project --force\n\n"
                "Alternatively, you can go into Flow Production Tracking and clear the Project.tank_name field\n"
                "and delete all pipeline configurations for your project.",
            )
            error_dialog.exec_()

        except TankUserPermissionsError as e:
            error_dialog = ErrorDialog(
                "Toolkit Setup Error",
                "You do not have sufficient permissions in Flow Production Tracking to setup Toolkit for "
                "project '%s'.\n\nContact a site administrator for assistance."
                % self.project["name"],
            )
            error_dialog.exec_()

    def show_help_popup(self):
        """
        Display a help screen
        """
        # For the interim, just launch an information MessageBox
        # that will open a link to the Toolkit Project setup wizard
        # documentation
        help_text = (
            "Find out more about the Setup Project Wizard by " "clicking 'Open' below."
        )
        help_buttons = QtGui.QMessageBox.Open | QtGui.QMessageBox.Cancel
        user_input = QtGui.QMessageBox.information(
            self, "Setup Project Help", help_text, help_buttons, QtGui.QMessageBox.Open
        )

        if user_input == QtGui.QMessageBox.Open:
            # Go to the Toolkit Project setup wizard documentation
            help_url = "https://developer.shotgridsoftware.com/5d83a936/?title=Configuration+Setup"
            QtGui.QDesktopServices.openUrl(help_url)

    def _validate_user_permissions(self):
        """
        Attempt to modify the Project's tank_name field to determine whether
        the current user has sufficient permission to setup the Project's
        pipeline configuration.
        """
        try:
            # Try to update the Project's tank_name value in PTR to test
            # whether current user has sufficient permission to setup
            # Toolkit for a project.
            engine = sgtk.platform.current_engine()
            sg_project = engine.shotgun.find_one(
                "Project", [["id", "is", self.project["id"]]], ["tank_name"]
            )
            engine.shotgun.update(
                "Project", self.project["id"], {"tank_name": "foobar"}
            )
            engine.shotgun.update(
                "Project", self.project["id"], {"tank_name": sg_project["tank_name"]}
            )
        except Exception as e:
            # Attempting to catch a shotgun_api3.Fault here using 'except Fault:'
            # just passes through, so we need to catch the general Exception instead
            # and check the error message directly for the specific problems we want
            # to handle.
            if "field is not editable for this user" in str(e):
                # Insufficient user permissions to setup Toolkit for a project.
                raise TankUserPermissionsError(e)

            # Raise any other general Exceptions.
            raise

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

    def eventFilter(self, obj, event):
        # peek at the message
        if event.type() == QtCore.QEvent.Resize:
            # re-broadcast any resize events
            self.resized.emit()
        # pass it on!
        return False


class TankUserPermissionsError(Exception):
    """
    Exception to raise if the current user does not have
    sufficient permissions to setup a project.
    """

    pass
