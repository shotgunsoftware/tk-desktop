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
Simple script that allows to test the Project Commands view without having to launch the
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

from tk_desktop.command_panel import CommandPanel
from tk_desktop.ui.desktop_window import Ui_DesktopWindow


products = [
    "Nuke Studio 12.0",
    "Nuke Studio 12.5*",
    "Nuke Studio 11.0",
    "Nuke 12.0*",
    "Nuke 12.5",
    "Nuke 11.0",
    "Nuke 9.0",
    "Nuke 8.5",
    "Nuke Assist 12.0",
    "Nuke Assist 12.5",
    "Nuke Assist 11.0*",
    "Maya 2018",
    "Maya 2019",
    "Maya 2020*",
    "3dsMax 2018",
    "3dsMax 2019*",
    "3dsMax 2020",
]

defaults = [
    products[1],
    products[3],
    products[8],
    products[10],
]

commands = [
    (
        product.lower().replace(" ", "_").replace(".", ""),
        product.rsplit(" ", 1)[0],
        product.replace("*", ""),
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "tk-%s" % product.split(" ", 1)[0].lower(),
            "icon_256.png",
        ),
        "Tooltip %s" % product,
        ["The Foundry" if "Nuke" in product else "Autodesk"],
        product in defaults,
    )
    for product in products
]


class ProjectCommandSettings(object):
    def save(self, key, recents):
        pass

    def load(self, key):
        return {
            command: {"timestamp": datetime.datetime.now()}
            for command, _, _, _, _, _, _ in list(commands)[0:3]
        }


app = importer.QtGui.QApplication([])
app.setStyle("plastique")

css_file = os.path.join(os.path.dirname(__file__), "..", "style.qss")
with open(css_file) as f:
    css = app.styleSheet() + "\n\n" + f.read()
app.setStyleSheet(css)


main = QtGui.QMainWindow()
main.ui = Ui_DesktopWindow()
main.ui.setupUi(main)
# Change the current page so the project commands page is visible.
main.ui.apps_tab.setCurrentIndex(1)

view = CommandPanel(main.ui.command_panel_area, ProjectCommandSettings())
main.ui.command_panel_area.setWidget(view)

view.configure(
    {"type": "Project", "id": 61}, ["Autodesk", "The Foundry"],
)
main.updateGeometry()


# Setting this to true will add icons asynchronously and launch a background process
# that will steal focus from the dialog, which should trigger a hover bug in PySide2.
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
