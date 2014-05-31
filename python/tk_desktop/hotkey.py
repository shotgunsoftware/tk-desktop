# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import unicodedata

from tank.platform.qt import QtCore, QtGui


class HotKeyEditor(QtGui.QLineEdit):
    # Emitted when the key sequence changes.
    # The first argument is the key sequence.
    # The second argument is the native modifiers associated with the sequence
    # The third argument is the native key code associated with the sequence
    key_sequence_changed = QtCore.Signal(QtGui.QKeySequence, int, int)

    def __init__(self, parent=None):
        QtGui.QLineEdit.__init__(self, parent)

        self.__key_sequence = QtGui.QKeySequence()

        # self.__line_edit.installEventFilter(self)
        self.setReadOnly(True)
        self.setAttribute(QtCore.Qt.WA_InputMethodEnabled)

    def eventFilter(self, widget, event):
        if widget == self and event.type() == QtCore.QEvent.ContextMenu:
            menu = self.createStandardContextMenu()
            actions = menu.actions()
            for action in actions:
                action.setShortcut(QtGui.QKeySequence())
                action_string = action.text()
                pos = action_string.rfind("\t")
                if (pos > 0):
                    action_string = action_string[:pos]
                    action.setText(action_string)

            action_before = None
            if len(actions) > 0:
                action_before = actions[0]
            clear = QtGui.QAction("Clear Shortcut", menu)
            menu.insertAction(action_before, clear)
            menu.insertSeparator(action_before)
            clear.setEnabled(not self.__key_sequence.isEmpty())
            clear.triggered.connect(self.clear_shortcut)
            menu.exec_(event.globalPos())
            del menu
            event.accept()
            return True

        return QtGui.QLineEdit.eventFilter(self, widget, event)

    def clear_shortcut(self):
        if self.__key_sequence.isEmpty():
            return

        self.key_sequence = QtGui.QKeySequence()
        self.key_sequence_changed.emit(self.key_sequence, 0, 0)

    def handle_key_event(self, event):
        if event.isAutoRepeat():
            return

        key = event.key()
        if (key == QtCore.Qt.Key_Control or key == QtCore.Qt.Key_Shift or
                key == QtCore.Qt.Key_Meta or key == QtCore.Qt.Key_Alt or
                key == QtCore.Qt.Key_Super_L or key == QtCore.Qt.Key_AltGr):
            return

        if not event.modifiers():
            return

        key |= self.translate_modifiers(event.modifiers(), event.text())
        self.key_sequence = QtGui.QKeySequence(key)
        self.key_sequence_changed.emit(
            self.key_sequence,
            event.nativeModifiers(),
            event.nativeVirtualKey(),
        )

        event.accept()

    @property
    def key_sequence(self):
        return self.__key_sequence

    @key_sequence.setter
    def key_sequence(self, sequence):
        if sequence == self.__key_sequence:
            return

        self.__key_sequence = sequence
        self.setText(self.__key_sequence.toString(QtGui.QKeySequence.NativeText))

    def translate_modifiers(self, state, text):
        result = 0
        if state & QtCore.Qt.ShiftModifier:
            if len(text) == 0:
                result |= QtCore.Qt.SHIFT
            else:
                category = unicodedata.category(text[0])
                if category[0] in ["L", "N", "P", "Z"]:
                    result |= QtCore.Qt.SHIFT
        if state & QtCore.Qt.ControlModifier:
            result |= QtCore.Qt.CTRL
        if state & QtCore.Qt.MetaModifier:
            result |= QtCore.Qt.META
        if state & QtCore.Qt.AltModifier:
            result |= QtCore.Qt.ALT
        return result

    def focusInEvent(self, event):
        QtGui.QLineEdit.focusInEvent(self, event)
        self.selectAll()

    def keyPressEvent(self, event):
        self.handle_key_event(event)
        event.accept()

    def event(self, event):
        if (event.type() == QtCore.QEvent.Shortcut or
           event.type() == QtCore.QEvent.ShortcutOverride or
           event.type() == QtCore.QEvent.KeyRelease):
            event.accept()
            return True

        return QtGui.QLineEdit.event(self, event)
