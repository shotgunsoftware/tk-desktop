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

from .ui import wait_screen


class WaitScreen(QtGui.QDialog):
    """ Simple wait dialog """
    def __init__(self, header="", subheader="", parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowFlags(QtCore.Qt.Popup)

        # setup the GUI
        self.ui = wait_screen.Ui_WaitScreen()
        self.ui.setupUi(self)
        self.ui.header.setText(header)
        self.ui.subheader.setText(subheader)

    def set_header(self, header):
        self.ui.header.setText(header)

    def set_subheader(self, subheader):
        self.ui.subheader.setText(subheader)
