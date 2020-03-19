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

from .shared import ICON_SIZE, BUTTON_STYLE


class RecentButton(QtGui.QPushButton):
    MARGIN = 5
    SPACING = 5
    SIZER_LABEL = None

    command_triggered = QtCore.Signal(str)

    def __init__(self, parent, command_name, button_name, icon, tooltip, timestamp):
        super(RecentButton, self).__init__(parent)

        self.setFlat(True)

        self.setSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding
        )
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        layout = QtGui.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter)
        layout.setSpacing(self.SPACING)
        layout.setContentsMargins(
            self.SPACING, self.SPACING, self.SPACING, self.SPACING
        )

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
        return six.ensure_str(self.text_label.text())

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def command_name(self):
        return self._command_name

    @classmethod
    def size_for_text(cls, text):
        # setup a label that we will use to get height
        if cls.SIZER_LABEL is None:
            cls.SIZER_LABEL = QtGui.QLabel()
            cls.SIZER_LABEL.setWordWrap(True)
            cls.SIZER_LABEL.setScaledContents(True)
            cls.SIZER_LABEL.setAlignment(QtCore.Qt.AlignHCenter)

        cls.SIZER_LABEL.setText(text)
        text_width = cls.SIZER_LABEL.fontMetrics().boundingRect(text).width()
        text_height = cls.SIZER_LABEL.heightForWidth(ICON_SIZE.width())

        # height is icon + text + top spacing + bottom spacing + space between
        width = max(ICON_SIZE.width(), text_width)
        height = ICON_SIZE.height() + text_height + (3 * cls.SPACING)
        return QtCore.QSize(width + 2 * cls.MARGIN, height)

    def sizeHint(self):
        # get the text size from the sizer label
        text = self.text_label.text()
        full_size = self.size_for_text(text)

        # see if the model has a limit on recents
        # limiting the number of recents, each one gets equal spacing
        # the spacing is the width of the view, without the spacing
        # divided up equally
        limit = RecentList.MAX_RECENTS
        parent = self.parent().parent().parent().parent().parent().viewport()
        space_to_divide = parent.width() - (self.SPACING * (limit + 1)) - self.MARGIN
        width = space_to_divide / limit
        return QtCore.QSize(width, full_size.height())
