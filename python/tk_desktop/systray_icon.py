# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank.platform.qt import QtCore, QtGui


class ShotgunSystemTrayIcon(QtGui.QSystemTrayIcon):
    """ wrapper around system tray icon """
    clicked = QtCore.Signal()
    double_clicked = QtCore.Signal()
    right_clicked = QtCore.Signal()

    def __init__(self, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, parent)

        # configure the system tray icon
        icon = QtGui.QIcon(":/tk-desktop/default_systray_icon")
        self.setIcon(icon)
        self.setToolTip("Shotgun")

        # connect up signal handlers
        self.activated.connect(self.__activated)

    def __activated(self, reason):
        if reason == QtGui.QSystemTrayIcon.Trigger:
            self.clicked.emit()
        elif reason == QtGui.QSystemTrayIcon.DoubleClick:
            self.double_clicked.emit()
        elif reason == QtGui.QSystemTrayIcon.Context:
            self.right_clicked.emit()
