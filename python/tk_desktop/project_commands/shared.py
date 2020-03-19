# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from sgtk.platform.qt import QtGui, QtCore

p = QtGui.QPalette()
highlight_col = p.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight)


# The minimum size of a button icon.
ICON_SIZE = QtCore.QSize(50, 50)

# The styling of the buttons.
BUTTON_STYLE = """
QToolButton {
    font-size: 15px;
}

QToolButton::menu-button  {
    border: none;
    width: 30px;
}

QPushButton, QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
}

QPushButton:hover, QToolButton:hover {
    border: 1px solid %s;
    background-color: %s;
}

QPushButton:pressed, QToolButton:pressed {
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);
}

QToolButton::menu-arrow:!hover { image:none; }


""" % (
    "rgb(%s, %s, %s)"
    % (highlight_col.red(), highlight_col.green(), highlight_col.blue(),),
    "rgba(%s, %s, %s, 25%%)"
    % (highlight_col.red(), highlight_col.green(), highlight_col.blue(),),
)

# Maximum number of recents.
MAX_RECENTS = 6
