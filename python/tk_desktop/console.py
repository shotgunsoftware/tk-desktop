# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
import logging

from sgtk.platform.qt import QtGui
from sgtk.platform.qt import QtCore

from .ui import resources_rc # noqa


settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")


COLOR_MAP = {
    # colors from the Tomorrow Night Eighties theme
    logging.CRITICAL: '#f2777a',
    logging.ERROR: '#f2777a',
    logging.WARNING: '#ffcc66',
    logging.INFO: '#cccccc',
    logging.DEBUG: '#999999'
}


class ConsoleLogHandler(logging.Handler):
    # Dummy type to hold the log_message signal.
    class LogSignaller(QtCore.QObject):
        log_message = QtCore.Signal(str, bool)

    def __init__(self, console):
        logging.Handler.__init__(self)
        self.__formatter = logging.Formatter("%(asctime)s [%(levelname) 8s] %(message)s")

        # Wrap the real message logging with a signal/slot,
        # to ensure that the console is updated within the UI thread.
        self.__signals = self.LogSignaller()
        self.__signals.log_message.connect(console.append_text)

    def emit(self, record):
        # Convert the record to pretty HTML
        message = self.__formatter.format(record)
        if record.levelno in COLOR_MAP:
            color = COLOR_MAP[record.levelno]
            message = "<font color=\"%s\">%s</font>" % (color, message)
        message = "<pre>%s</pre>" % message

        # Update console (possibly in a different thread than the current one)
        # force_show can pop open the console automatically, for example on
        # ERROR: record.levelno >= logging.ERROR
        self.__signals.log_message.emit(message, False)


class Console(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Console, self).__init__(parent)

        self.setWindowTitle('Shotgun Desktop Console')
        self.setWindowIcon(QtGui.QIcon(":/tk-desktop/default_systray_icon.png"))

        self.__logs = QtGui.QPlainTextEdit()
        self.__find = QtGui.QLineEdit()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.__logs)
        layout.addWidget(self.__find)
        self.setLayout(layout)

        # configure the text widget
        self.__logs.setReadOnly(True)
        self.__logs.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.__logs.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.__logs.customContextMenuRequested.connect(self.on_logs_context_menu_request)
        self.__logs.setStyleSheet("QPlainTextEdit:focus { border: none; }")

        # configure the find lineEdit
        self.__find.setPlaceholderText("Find")
        self.__find.returnPressed.connect(self.find)
        self.__pattern = ""
        self.__match_index = 0
        self.__matches = []
        # set shortcut
        find_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self.focus_find)
        # load up previous size
        self._settings_manager = settings.UserSettings(sgtk.platform.current_bundle())
        pos = self._settings_manager.retrieve("console.pos", self.pos(), self._settings_manager.SCOPE_GLOBAL)
        size = self._settings_manager.retrieve(
            "console.size", QtCore.QSize(800, 400), self._settings_manager.SCOPE_GLOBAL)

        self.move(pos)
        self.resize(size)

        self.__console_handler = ConsoleLogHandler(self)
        sgtk.LogManager().initialize_custom_handler(self.__console_handler)

    def on_logs_context_menu_request(self, point):
        menu = self.__logs.createStandardContextMenu()
        clear_action = menu.addAction("Clear")
        clear_action.triggered.connect(self.clear)
        close_action = menu.addAction("Close")
        close_action.triggered.connect(self.close)
        find_action = menu.addAction("Find")
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.focus_find)

        menu.exec_(self.__logs.mapToGlobal(point))

    def append_text(self, text, force_show=False):
        self.__logs.appendHtml(text)
        cursor = self.__logs.textCursor()
        cursor.movePosition(cursor.End)
        cursor.movePosition(cursor.StartOfLine)
        self.__logs.setTextCursor(cursor)
        self.__logs.ensureCursorVisible()

        if force_show:
            self.show_and_raise()

    def clear(self):
        self.__logs.setPlainText("")

    def focus_find(self):
        self.__find.setFocus()
        self.__find.selectAll()

    def find(self):
        pattern = self.__find.text()
        logs = self.__logs.toPlainText()
        cursor = self.__logs.textCursor()
        regex = QtCore.QRegExp(pattern, QtCore.Qt.CaseInsensitive)
        if pattern != self.__pattern:
            self.clear_highlight()
            self.__match_index = 0
            self.__matches = self.find_all(pattern, regex, logs, cursor)
            self.__pattern = pattern
        # total number of matches
        match_count = len(self.__matches)
        # highlight pattern forward
        if self.__match_index < len(self.__matches):
            start, matched_length = self.__matches[self.__match_index]
            print "{} of {}".format(self.__match_index + 1, match_count)
            self.highlight_one(
                start,
                matched_length
            )
            self.__match_index += 1
        else:
            # search reaches end, reset match index and cursor
            self.__match_index = 0
            self.__logs.moveCursor(QtGui.QTextCursor.End)
            self.find()

    def find_all(self, pattern, regex, logs, cursor):
        highlight_format = QtGui.QTextCharFormat()
        highlight_format.setBackground(
            QtGui.QBrush(QtGui.QColor(80, 80, 80))
        )
        matches = []
        pos = 0
        index = regex.indexIn(logs, pos)
        count = 0
        while (index != -1):
            count += 1
            matched_length = regex.matchedLength()
            # append start index and length of last matched string
            # length could be different
            matches.append((index, matched_length))
            # select the matched text and apply the desired format
            self.highlight_one(index, matched_length, highlight_format)
            # Move to the next match
            pos = index + matched_length
            index = regex.indexIn(logs, pos)
        return matches

    def highlight_one(self, start, length, highlight_format=None):
        cursor = self.__logs.textCursor()
        # set the position to the beginning of the last match
        cursor.setPosition(start)
        # select one match
        cursor.movePosition(
            QtGui.QTextCursor.Right,
            QtGui.QTextCursor.KeepAnchor,
            length
        )
        if highlight_format:
            cursor.mergeCharFormat(highlight_format)
        # set this new cursor as logs' cursor
        self.__logs.setTextCursor(cursor)

    def clear_highlight(self):
        cursor = self.__logs.textCursor()
        cursor.select(QtGui.QTextCursor.Document)
        cursor.setCharFormat(QtGui.QTextCharFormat())
        cursor.clearSelection()
        self.__logs.setTextCursor(cursor)

    def show_and_raise(self):
        self.show()
        self.raise_()
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)

    def closeEvent(self, event):
        self._settings_manager.store("console.pos", self.pos(), self._settings_manager.SCOPE_GLOBAL)
        self._settings_manager.store("console.size", self.size(), self._settings_manager.SCOPE_GLOBAL)
        event.accept()
