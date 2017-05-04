# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


# For testing outside of Desktop. Add QtCore and QtGui to the qt package.
if __name__ == "__main__":
    import sgtk
    # Set up Qt
    from PySide import QtCore, QtGui
    sgtk.platform.qt.QtCore = QtCore
    sgtk.platform.qt.QtGui = QtGui


from sgtk.platform.qt import QtCore, QtGui

try:
    from .ui.browser_integration_user_switch_dialog import Ui_BrowserIntegrationUserSwitchDialog
except ValueError:
    from ui.browser_integration_user_switch_dialog import Ui_BrowserIntegrationUserSwitchDialog


class BrowserIntegrationUserSwitchDialog(QtGui.QDialog):

    Restart = QtGui.QDialog.Accepted
    Ignore = QtGui.QDialog.Rejected
    IgnorePermanently = Restart + Ignore + 1

    def __init__(self, message, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.ui = Ui_BrowserIntegrationUserSwitchDialog()
        self.ui.setupUi(self)

        self.ui.reason_label.setText(message)

        self.ui.restart_button.clicked.connect(self._on_restart_clicked)
        self.ui.ignore_button.clicked.connect(self._on_ignore_clicked)
        self.ui.ignore_checkbox.stateChanged.connect(self._on_ignore_change_state)

    def _on_ignore_change_state(self, state):
        self.ui.restart_button.setEnabled(state != QtCore.Qt.Checked)

    def _on_restart_clicked(self):
        self.done(self.Restart)

    def _on_ignore_clicked(self):
        if self.ui.ignore_checkbox.isChecked():
            self.done(self.IgnorePermanently)
        else:
            self.done(self.Ignore)


if __name__ == "__main__":
    import sys
    QtGui.QApplication(sys.argv)

    dlg = BrowserIntegrationUserSwitchDialog(
        "It appears there was a request coming from <b>{0}</b>, but you "
        "are currently logged into <b>{1}</b>.<br/><br/>"
        "You need restart the Shotgun Desktop and connect to <b>{0}</b> in "
        "order to answer requests from that site.".format(
            "abc.shotgunstudio.com",
            "xyz.shotgunstudio.com"
        )
    )
    dlg.exec_()
    if dlg.result() == dlg.Accepted:
        print "Restart"
    elif dlg.result() == dlg.Ignore:
        print "Ignore"
    else:
        print "Permanently Ignore"

