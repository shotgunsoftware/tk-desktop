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

from .ui import about_screen


class AboutScreen(QtGui.QDialog):
    """ Simple about dialog """
    def __init__(self, body="", parent=None):
        QtGui.QDialog.__init__(self, parent)

        # setup the GUI
        self.ui = about_screen.Ui_AboutScreen()
        self.ui.setupUi(self)
        self.ui.body.setText(body)

    def set_body(self, body):
        self.ui.body.setText(body)
