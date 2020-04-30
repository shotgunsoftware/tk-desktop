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
from tank_vendor import six

from .shared import ICON_SIZE, BUTTON_STYLE, MAX_RECENTS


class RecentButton(QtGui.QPushButton):
    """
    The RecentButton has an icon and text underneath it and can launch
    a single action, unlike the CommandButton.
    """

    MARGIN = 5
    SPACING = 5
    SIZER_LABEL = None

    command_triggered = QtCore.Signal(str)

    def __init__(self, parent, command_name, button_name, icon, tooltip, timestamp):
        """
        :param str command_name: Name of the command.
        :param str button_name: Name of the button.
        :param str icon: Path to the icon for this command.
        :param str tooltip: Toolkit for this command.
        :param datetime.datetime timestamp: When the command was last launched.
        """
        super(RecentButton, self).__init__(parent)

        # No borders
        self.setFlat(True)

        self.setSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding
        )
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        layout = QtGui.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter)
        layout.setSpacing(self.SPACING)
        layout.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)

        self._timestamp = timestamp

        self.icon_label = QtGui.QLabel(self)
        self.icon_label.setAlignment(QtCore.Qt.AlignHCenter)
        self.layout().addWidget(self.icon_label, QtCore.Qt.AlignHCenter)

        self.text_label = QtGui.QLabel(parent)
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(QtCore.Qt.AlignHCenter)
        self.layout().addWidget(self.text_label, QtCore.Qt.AlignHCenter)

        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet(BUTTON_STYLE)

        self.text_label.setText(button_name)
        if icon is None:
            self.icon_label.setPixmap(QtGui.QIcon().pixmap(ICON_SIZE))
        else:
            self.icon_label.setPixmap(QtGui.QIcon(icon).pixmap(ICON_SIZE))

        self.setToolTip(tooltip)

        self._command_name = command_name

        self.clicked.connect(
            lambda: self.command_triggered.emit(six.ensure_str(self._command_name))
        )

    @property
    def name(self):
        """
        Name of the button.
        """
        return six.ensure_str(self.text_label.text())

    @property
    def timestamp(self):
        """
        Time when this command was last executed.
        """
        return self._timestamp

    @property
    def command_name(self):
        """
        Name of the command.
        """
        return self._command_name

    def sizeHint(self):
        """
        Hint at the button size.

        The button should occupy 1/MAX_RECENTS's of the parent widget width
        and be a bit higher than the icon.
        """
        hint = QtCore.QSize(
            (self.parentWidget().width() / MAX_RECENTS) - (self.SPACING * 2),
            ICON_SIZE.height() + 8,
        )
        return hint
