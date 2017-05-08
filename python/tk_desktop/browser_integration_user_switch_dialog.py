# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from sgtk.platform.qt import QtCore, QtGui
from .ui.browser_integration_user_switch_dialog import Ui_BrowserIntegrationUserSwitchDialog


class BrowserIntegrationUserSwitchDialog(QtGui.QDialog):
    """
    Prompts the user to restart the Desktop or ignore (potentially permenantly)
    the request.
    """

    RESTART = QtGui.QDialog.Accepted
    IGNORE = QtGui.QDialog.Rejected
    IGNOREPERMANENTLY = RESTART + IGNORE + 1

    def __init__(self, message, parent=None):
        """
        :param str message: Message to display to the user.
        """
        QtGui.QDialog.__init__(self, parent)

        self.ui = Ui_BrowserIntegrationUserSwitchDialog()
        self.ui.setupUi(self)

        self.ui.reason_label.setText(message)

        self.ui.restart_button.clicked.connect(self._on_restart_clicked)
        self.ui.ignore_button.clicked.connect(self._on_ignore_clicked)
        self.ui.ignore_checkbox.stateChanged.connect(self._on_ignore_change_state)

    def _on_ignore_change_state(self, state):
        """
        Disables or activates the Restart button when the ignore checkbox
        is checked or unchecked respectively.

        :param int state: State of the checkbox.
        """
        self.ui.restart_button.setEnabled(state != QtCore.Qt.Checked)

    def _on_restart_clicked(self):
        """
        Dismisses the dialog with the the Restart code.
        """
        self.done(self.RESTART)

    def _on_ignore_clicked(self):
        """
        Dismisses the dialog with the the Ignore or IgnorePermanently code
        depending on the state of the checkbox.
        """
        if self.ui.ignore_checkbox.isChecked():
            self.done(self.IGNOREPERMANENTLY)
        else:
            self.done(self.IGNORE)
