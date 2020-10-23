# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

from sgtk.platform.qt import QtGui

from .ui import licenses

LICENSE_LOCATION = os.path.join(os.path.dirname(__file__), "licenses.html")


class Licenses(QtGui.QDialog):
    """ Simple about dialog """

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        # setup the GUI
        self.ui = licenses.Ui_Licenses()
        self.ui.setupUi(self)
        # setSource seems broken on Qt4, so use setHtml instead.
        with open(LICENSE_LOCATION) as f:
            self.ui.licenseText.setHtml(f.read())
