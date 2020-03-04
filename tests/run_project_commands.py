# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Simple script that allows to tet the Project Commands view without having to launch the
Shotgun Desktop.
"""

import os
import sys
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "tk-core", "python")
)

# Monkey patch Toolkit so Qt is accessible.
import sgtk

# Note that QtImporter is part of a private API and might
# break at some point. For a debug script however, it's not too bad.
importer = sgtk.util.qt_importer.QtImporter()
sgtk.platform.qt.QtGui = importer.QtGui
sgtk.platform.qt.QtCore = importer.QtCore

QtGui = sgtk.platform.qt.QtGui
QtCore = sgtk.platform.qt.QtCore

from tk_desktop.prj_commands import CommandsView, RecentList
from tk_desktop.ui.desktop_window import Ui_DesktopWindow


class ProjectCommandSettings(object):
    def save(self, key, recents):
        pass

    def load(self, key):
        return {
            "nuke_studio_120": {
                "timestamp": datetime.datetime(2008, 1, 1),
                "added": True,
            },
            "maya_2019": {"timestamp": datetime.datetime(2005, 1, 1), "added": True,},
        }


# Monkey patch the MAX_RECENTS so we don't have to create too many
# commands for testing.
RecentList.MAX_RECENTS = 3

app = importer.QtGui.QApplication([])

main = QtGui.QMainWindow()
main.ui = Ui_DesktopWindow()
main.ui.setupUi(main)
# Change the current page so the project commands page is visible.
main.ui.apps_tab.setCurrentIndex(1)

view = CommandsView(main, ProjectCommandSettings())
main.ui.project_commands_area.setWidget(view)

view.set_project(
    {"type": "Project", "id": 61},
    ["Creative Tools", "Editorial Tools", "Automotive Tools"],
)

commands = [
    (
        "Nuke Studio 12.0",
        "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
        "tooltip nuke 12.0",
        ["Creative Tools"],
        True,
    ),
    (
        "NukeX 12.5",
        "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
        "tooltip nuke 12.0",
        ["Creative Tools"],
        True,
    ),
    (
        "NukeX 12.0",
        "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
        "tooltip nuke 12.0",
        ["Creative Tools"],
        False,
    ),
    (
        "Nuke Assist 12.0",
        "/Users/boismej/gitlocal/tk-nuke/icon_256.png",
        "tooltip nuke 12.0",
        ["Creative Tools"],
        True,
    ),
    (
        "Maya 2019",
        "/Users/boismej/gitlocal/tk-maya/icon_256.png",
        "tooltip maya 2019",
        ["Creative Tools"],
        True,
    ),
    (
        "Maya 2020",
        "/Users/boismej/gitlocal/tk-maya/icon_256.png",
        "tooltip maya 2020",
        ["Creative Tools"],
        False,
    ),
]

commands = [
    (
        cmd[0].lower().replace(" ", "_").replace(".", ""),
        cmd[0].rsplit(" ", 1)[0],
        cmd[0],
        cmd[1],
        cmd[2],
        cmd[3],
        cmd[4],
    )
    for cmd in commands
]

# Setting this to true will add
if "--async" in sys.argv:

    def add_button():
        command = commands.pop(0)
        view.add_command(*command)
        if commands:
            QtCore.QTimer.singleShot(500, add_button)
        else:
            import subprocess

            subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    "from PySide2 import QtWidgets; QtWidgets.QApplication([]).exec_()",
                ]
            )

    QtCore.QTimer.singleShot(1500, add_button)
else:
    for cmd in commands:
        view.add_command(*cmd)

main.show()

app.exec_()
