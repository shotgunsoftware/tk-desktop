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
from .default_grouping_header import DefaultGroupingHeader


class Section(QtGui.QWidget):

    command_triggered = QtCore.Signal(str)
    expand_toggled = QtCore.Signal(str, bool)

    def __init__(self, name, WidgetListFactory):
        super(Section, self).__init__(parent=None)

        self._layout = QtGui.QVBoxLayout(self)
        self.setLayout(self._layout)

        self._name = name

        self._grouping = DefaultGroupingHeader()
        self._grouping.setText(name.upper())
        self._layout.addWidget(self._grouping)

        self._list = WidgetListFactory(self)
        self._layout.addWidget(self._list)
        self._grouping.toggled.connect(self.set_expanded)

        self._line = QtGui.QFrame()
        self._line.setFrameShape(QtGui.QFrame.HLine)
        self._line.setStyleSheet(
            "background-color: transparent; color: rgb(30, 30, 30);"
        )
        self._line.setMidLineWidth(2)
        self._layout.addWidget(self._line)

        margins = self._layout.contentsMargins()
        margins.setTop(0)
        margins.setBottom(0)
        margins.setLeft(10)
        margins.setRight(10)
        self._layout.setContentsMargins(10, 0, 10, 0)

        self._list.command_triggered.connect(self.command_triggered)

    @property
    def name(self):
        return self._name

    def is_expanded(self):
        return self._grouping.is_expanded()

    def set_expanded(self, checked):
        print(self._name, checked)
        self._grouping.set_expanded(checked)
        self._list.setVisible(checked)
        self.expand_toggled.emit(self._name, checked)

    @property
    def buttons(self):
        return self._list.buttons
