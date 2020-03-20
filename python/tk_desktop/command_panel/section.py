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
from .section_header import SectionHeader


class Section(QtGui.QWidget):
    """
    Implement common functionality for each section type.

    The widget contains a header that shows the name of the
    section and an icon button that allows to expand and collapse
    the section.

    It also contains a BaseIconList derived instance, which will
    hold all the buttons for this section.
    """

    command_triggered = QtCore.Signal(str)
    expand_toggled = QtCore.Signal(str, bool)

    def __init__(self, name, list_factory):
        """
        :param str name: Name of the section.
        :param class list_factory: Class of the list widget to instantiate.
        """
        super(Section, self).__init__(parent=None)

        self._layout = QtGui.QVBoxLayout(self)
        self.setLayout(self._layout)

        self._name = name

        # Create the header.
        self._grouping = SectionHeader()
        self._grouping.setText(name.upper())
        self._grouping.toggled.connect(self.set_expanded)
        self._layout.addWidget(self._grouping)

        # Add the list of buttons widget.
        self._list = list_factory(self)
        self._layout.addWidget(self._list)

        # Finally add a separator at the bottom.
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

        # Each time a command is triggered on the list, the command_triggered
        # event is emitted.
        self._list.command_triggered.connect(self.command_triggered)

    @property
    def name(self):
        """
        Name of the section.
        """
        return self._name

    def is_expanded(self):
        """
        Return if the group is currently expanded.
        """
        return self._grouping.is_expanded()

    def set_expanded(self, checked):
        """
        Expand or collapse the group.

        :param bool checked: If True, expands the group, collapses it otherwise.
        """
        self._grouping.set_expanded(checked)
        self._list.setVisible(checked)
        self.expand_toggled.emit(self._name, checked)

    @property
    def buttons(self):
        """
        An iterator over the buttons in the section.
        """
        return self._list.buttons
