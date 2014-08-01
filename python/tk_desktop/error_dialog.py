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

from .ui import error_dialog


class ErrorDialog(QtGui.QDialog):
    """ Simple error dialog with a text edit to handle displaying large messages. """
    def __init__(self, title, message, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.ui = error_dialog.Ui_ErrorDialog()
        self.ui.setupUi(self)

        # get the system critical icon
        style = self.style() or QtGui.QApplication.style()
        iconSize = style.pixelMetric(QtGui.QStyle.PM_MessageBoxIconSize, None, self)
        icon = style.standardIcon(QtGui.QStyle.SP_MessageBoxCritical, None, self)
        pixmap = icon.pixmap(iconSize, iconSize)
        self.ui.icon.setPixmap(pixmap)

        # set the content
        self.ui.title.setText(title)
        self.ui.message.setText(message)
