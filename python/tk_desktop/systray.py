# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from PySide import QtGui
from PySide import QtCore

from .systray_icon import ShotgunSystemTrayIcon


class SystrayWindow(QtGui.QMainWindow):
    """
    Generic system tray window.

    A Qt main window that pins to a system tray icon and can be dragg
    """
    # constants to track what state the window is in
    STATE_PINNED = 0x0001
    STATE_WINDOWED = 0x0002

    # signal that is emitted when the system tray state changes
    systray_state_changed = QtCore.Signal(int)

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)

        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)

        self.__state = None  # pinned or windowed
        self.__mouse_down_pos = None  # track position when dragging
        self.__mouse_down_global = None  # track global position when dragging

        # height of the portion of the window that will be masked out into
        # an arrow when pinned
        self.__window_anchor_height = 0

        # radius for rounded corners
        self.__corner_radius = 5

        # widgets that will trigger the drag to move behavior
        self.__drag_widgets = []

        # create the system tray icon
        self.systray = ShotgunSystemTrayIcon(self)
        self.systray.show()

        # hook up handler for when the systray is clicked
        self.systray.clicked.connect(self.systray_clicked)

    # Customize behavior
    ###########################

    def set_drag_widgets(self, widgets):
        """ Set the list of widgets that can be dragged to move the window """
        self.__drag_widgets = widgets[:]

    def set_window_anchor_height(self, value):
        """ set the height of the anchor arrow to draw when pinned """
        self.__window_anchor_height = value

    def set_corner_radius(self, value):
        """ set the radius to use for rounding the window corners """
        self.__corner_radius = value

    # Change pin state
    ###########################
    def _get_state(self):
        """ return the current state of the window """
        return self.__state

    def _set_state(self, value):
        """ set the current state of the window """
        # if state isn't changing do not do anything
        if self.__state == value:
            return

        # update tracker variable
        self.__state = value

        if self.__state == self.STATE_PINNED:
            self._set_window_mask()
            self.__move_to_systray()
        elif self.__state == self.STATE_WINDOWED:
            self._set_window_mask()
        else:
            raise ValueError("Unknown value for state: %s" % value)

        self.systray_state_changed.emit(self.__state)

    # create a property from the getter/setter
    state = property(_get_state, _set_state)

    def toggle_pinned(self):
        if self.state == self.STATE_PINNED:
            self.state = self.STATE_WINDOWED
        elif self.state == self.STATE_WINDOWED:
            self._pin_to_menu()

    def _pin_to_menu(self):
        # figure out start and end positions for the window
        systray_geo = self.systray.geometry()
        final = QtCore.QRect(systray_geo.center().x(), systray_geo.bottom(), 5, 5)
        start = self.geometry()

        # setup the animation to shrink the window to the systray
        # parent the anim to self to keep it from being garbage collected
        anim = QtCore.QPropertyAnimation(self, "geometry", self)
        anim.setDuration(300)
        anim.setStartValue(start)
        anim.setEndValue(final)
        anim.setEasingCurve(QtCore.QEasingCurve.InQuad)

        # when the anim is finished, call the post handler
        def post_close_animation():
            self.hide()
            self.setGeometry(start)
            self.state = self.STATE_PINNED

        anim.finished.connect(post_close_animation)

        # run the animation
        anim.start()

    # Drag to move behavior
    ###########################
    def mousePressEvent(self, event):
        """ Handle mouse press to track the start of a drag from the pinned window header """
        if any([elem.underMouse() for elem in self.__drag_widgets]):
            # only trigger on left click
            if event.buttons() == QtCore.Qt.LeftButton:
                # clicked on a drag element, track position for possible drag
                self.__mouse_down_pos = event.pos()
                self.__mouse_down_global = QtGui.QCursor.pos()

        # propagate event
        event.ignore()

    def mouseReleaseEvent(self, event):
        """ Handle mouse release to switch to window mode if there has been a long enough drag """
        # only do something if we are dragging
        if self.__mouse_down_pos is None:
            event.ignore()
            return

        # if we have moved more than threshold then trigger a switch to windowed mode
        if self.state == self.STATE_PINNED:
            delta = QtGui.QCursor.pos() - self.__mouse_down_global
            if delta.manhattanLength() > QtGui.QApplication.startDragDistance():
                self.state = self.STATE_WINDOWED

        # clear cached positions
        self.__mouse_down_pos = None
        self.__mouse_down_global = None

        # propagate event
        event.ignore()

    def mouseMoveEvent(self, event):
        """ Handle mouse moves to move the window with the mouse if we are dragging """
        if self.__mouse_down_pos is not None:
            # move window to track mouse
            self.move(self.mapToParent(event.pos() - self.__mouse_down_pos))

        # propagate event
        event.ignore()

    def closeEvent(self, event):
        """ Take over the close event to simply hide the window and repin """
        self._pin_to_menu()
        event.ignore()

    def __move_to_systray(self):
        """ update the window position to be centered under the system tray icon """
        geo = self.systray.geometry()
        x = geo.x() + (geo.width() - self.rect().width()) / 2.0
        self.move(x, geo.y() + geo.height())

    def systray_clicked(self):
        """ handler for single click on the system tray """
        # toggle visibility when clicked
        if self.isHidden():
            if self.state == self.STATE_PINNED:
                # make sure the window is positioned correctly if pinned
                self.__move_to_systray()

            self.show()
            self.raise_()
        else:
            self.hide()

    # Update the window mask
    ############################

    def _set_window_mask(self):
        """ set the window mask when pinned to the systray """
        # temp bitmap to store the mask
        bmp = QtGui.QBitmap(self.size())

        # create and configure the painter
        self.painter = QtGui.QPainter(bmp)
        self.painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing, True)

        # mask out from the top margin of the border_layout
        rect = self.rect()
        top = self.__window_anchor_height
        self.painter.fillRect(rect, QtCore.Qt.white)
        self.painter.setBrush(QtCore.Qt.black)
        mask = rect.adjusted(0, top, 0, 0)
        self.painter.drawRoundedRect(mask, self.__corner_radius, self.__corner_radius)

        if self.state == self.STATE_PINNED:
            # add back in the anchor triangle
            (x, y, w, h) = rect.getRect()
            midpoint = x + w/2.0
            points = []
            points.append(QtCore.QPoint(midpoint, y))
            points.append(QtCore.QPoint(midpoint-top, y+top))
            points.append(QtCore.QPoint(midpoint+top, y+top))
            self.painter.drawPolygon(points)

        # need to end the painter to make sure that its resources get
        # garbage collected before the bitmap to avoid a crash
        self.painter.end()

        # finally set the window mask to the bitmap
        self.setMask(bmp)
