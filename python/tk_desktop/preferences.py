# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from __future__ import absolute_import

import logging

from tank.platform.qt import QtCore, QtGui


from .ui import preferences

logger = logging.getLogger("tk-desktop.preferences")

try:
    from .extensions import osutils
except ImportError, e:
    logger.warning("Failed to import osutils, disabling some features.")
    osutils = None


class Preferences(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.ui = preferences.Ui_Preferences()
        self.ui.setupUi(self)

        # center on the screen
        self.adjustSize()
        self.move(QtGui.QApplication.desktop().screen().rect().center() - self.rect().center())

        # setup signals
        self.ui.hotkey_clear.clicked.connect(self.ui.hotkey.clear_shortcut)

        # setup hotkey
        if osutils is None:
            self.ui.hotkey_label.setEnabled(False)
            self.ui.hotkey.setEnabled(False)
            self.ui.hotkey_clear.setEnabled(False)

        # keep on top
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
