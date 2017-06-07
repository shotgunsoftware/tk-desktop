# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from __future__ import absolute_import

import sys
import contextlib

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .ui import resources_rc # noqa

from .systray_icon import ShotgunSystemTrayIcon

try:
    from .extensions import osutils
except Exception:
    osutils = None


logger = sgtk.platform.get_logger(__name__)


class SystrayWindow(QtGui.QMainWindow):
    """
    Generic system tray window.

    A Qt main window that pins to a system tray icon and can be dragged
    """
    # constants to track what state the window is in
    STATE_PINNED = 0
    STATE_WINDOWED = 1

    DOCK_TOP = 0
    DOCK_LEFT = 1
    DOCK_RIGHT = 2
    DOCK_BOTTOM = 3

    # signal that is emitted when the system tray state changes
    systray_state_changed = QtCore.Signal(int)

    class ApplicationEventFilter(QtCore.QObject):
        """ Internal class to handle hiding window on App deactivate """
        def __init__(self, window, parent=None):
            QtCore.QObject.__init__(self, parent)
            self._window = window
            self._deactivated = False

        def eventFilter(self, obj, event):
            if not self._deactivated:
                if event.type() == QtCore.QEvent.ApplicationDeactivate:
                    # When the app loses focus and is in pinned mode, we hide the dialog automatically
                    # and move the app to the background so there's no more icon in the tray.
                    if self._window.state == SystrayWindow.STATE_PINNED:
                        self._window.hide()
                        if osutils is not None:
                            osutils.make_app_background()
                elif event.type() == QtCore.QEvent.ApplicationActivate:
                    # When the app gains focus and is in pinned mode, we bring the app to the background.
                    # Note that we are not showing the main dialog because there are multiple top levels
                    # windows that would have cause the application to activate.
                    if self._window.state == SystrayWindow.STATE_PINNED:
                        if osutils is not None:
                            osutils.make_app_foreground()

            return QtCore.QObject.eventFilter(self, obj, event)

        def deactivate(self, deactivated):
            """
            Allows to deactivate the event filter.

            :param deactivated: If ``True``, events will not be filtered anymore.
            """
            self._deactivated = deactivated

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)

        if sys.platform == "darwin":
            self.setAttribute(QtCore.Qt.WA_MacNoShadow)

        self.filter = self.ApplicationEventFilter(self)
        QtGui.QApplication.instance().installEventFilter(self.filter)

        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)

        self.__state = None  # pinned or windowed
        self.__anchor_side = None  # which side the anchor is currently pinned on
        self.__content_layout = None  # layout whose margin will be set to contain the anchor
        self.__mouse_down_pos = None  # track position when dragging
        self.__mouse_down_global = None  # track global position when dragging

        # setup the anchor
        self.__bottom_anchor = QtGui.QPixmap(":/tk-desktop/anchor_arrow.png")
        self.__top_anchor = self.__bottom_anchor.transformed(QtGui.QTransform(1, 0, 0, -1, 0, 0))
        self.__right_anchor = self.__bottom_anchor.transformed(QtGui.QTransform(0, 1, 1, 0, 0, 0))
        self.__left_anchor = self.__bottom_anchor.transformed(QtGui.QTransform(0, 1, -1, 0, 0, 0))

        # radius for rounded corners
        self.__corner_radius = 4

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

    def set_corner_radius(self, value):
        """ set the radius to use for rounding the window corners """
        self.__corner_radius = value

    def set_content_layout(self, value):
        """ set the layout to use to provide a margin for the anchor """
        self.__content_layout = value

    # Change pin state
    ###########################
    @property
    def state(self):
        """ return the current state of the window """
        return self.__state

    @state.setter
    def state(self, value):
        """ set the current state of the window """
        # if state isn't changing do not do anything
        if self.__state == value:
            return

        # update tracker variable
        self.__state = value

        if self.__state == self.STATE_PINNED:
            self._set_window_mask()
            self.__move_to_systray()
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
            if osutils is not None:
                osutils.make_app_background()

        elif self.__state == self.STATE_WINDOWED:
            self._set_window_mask()
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.FramelessWindowHint)
            self.show()
            if osutils is None:
                self.raise_()
            else:
                osutils.make_app_foreground()
        else:
            raise ValueError("Unknown value for state: %s" % value)

        self.systray_state_changed.emit(self.__state)

    @contextlib.contextmanager
    def deactivate_auto_hide(self):
        """
        Used to temporarily disable the auto-hide behaviour of pinned dialogs. This does not alter
        the visual state of the dialog or the state of the ``state`` property.
        """
        self.filter.deactivate(True)
        try:
            yield
        finally:
            self.filter.deactivate(False)

    def toggle_pinned(self):
        if self.state == self.STATE_PINNED:
            self.state = self.STATE_WINDOWED
        elif self.state == self.STATE_WINDOWED:
            self._pin_to_menu()

    def _pin_to_menu(self, animated=True):
        # figure out start and end positions for the window
        self.systray.show()
        QtGui.QApplication.instance().processEvents()
        systray_geo = self.systray.geometry()

        logger.debug("systray_geo: %s", systray_geo)

        if animated:
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
        else:
            # not animated
            self.hide()
            self.state = self.STATE_PINNED

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

    # Pinned behavior
    ###########################
    def __move_to_systray(self):
        """ update the window position to be centered under the system tray icon """
        geo = self.systray.geometry()
        logger.debug("__move_to_systray: systray_geo: %s" % geo)

        side = self._guess_toolbar_side()

        if side != self.__class__:
            # anchor needs to be updated
            self._set_window_mask()

        if side == self.DOCK_TOP:
            x = geo.x() + (geo.width() - self.rect().width()) / 2.0
            pos = QtCore.QPoint(x, geo.y() + geo.height())
        elif side == self.DOCK_LEFT:
            y = geo.y() + (geo.height() - self.rect().height()) / 2.0
            pos = QtCore.QPoint(geo.x() + geo.width(), y)
        elif side == self.DOCK_RIGHT:
            y = geo.y() + (geo.height() - self.rect().height()) / 2.0
            pos = QtCore.QPoint(geo.x() - self.rect().width(), y)
        elif side == self.DOCK_BOTTOM:
            x = geo.x() + (geo.width() - self.geometry().width()) / 2.0
            pos = QtCore.QPoint(x, geo.y() - self.rect().height() - geo.height())
        else:
            raise ValueError("Unknown value for side: %s" % side)

        # if part of the window will be drawn off screen, move the pos.
        screen_geometry = self._get_systray_screen_geometry()
        if (pos.x() + self.geometry().width()) > screen_geometry.right():
            diff = (pos.x() + self.geometry().width()) - screen_geometry.right()
            pos = QtCore.QPoint(pos.x() - diff, pos.y())

        self.move(pos)

    def systray_clicked(self):
        """ handler for single click on the system tray """
        self.toggle_activate()

    def is_pinned(self):
        """
        :returns: True if the dialog is pinned, false otherwise.
        """
        return self.state == self.STATE_PINNED

    def activate(self):
        """
        Ensures the Desktop's dialog is visible and on top of other windows.
        """
        if self.isHidden():
            # hidden, show and bring to the top
            if self.state == self.STATE_PINNED:
                self.__move_to_systray()
            self.show()
            self.raise_()
            self.activateWindow()
            if osutils is not None:
                osutils.make_app_foreground()
        else:
            # shown and not topmost, just bring to the top
            self.raise_()
            self.activateWindow()
            if osutils is not None:
                osutils.activate_application()

    def toggle_activate(self):
        """
        Toggles visibility when systray icon is clicked.
        """
        active = self.isActiveWindow()
        if active:
            # shown and topmost, hide
            self.hide()
            if osutils is not None:
                osutils.make_app_background()
        else:
            self.activate()

    def _get_systray_screen_geometry(self):
        pos = self.systray.geometry().center()
        desktop = QtGui.QApplication.instance().desktop()
        return desktop.screenGeometry(pos)

    # Update the window mask
    ############################
    def _guess_toolbar_side(self):
        """ guess which side of the screen the toolbar is on """
        pos = self.systray.geometry().center()
        screen_geometry = self._get_systray_screen_geometry()

        # Get dist from each edge of the screen
        top_dist = pos.y() - screen_geometry.top()
        bottom_dist = screen_geometry.bottom() - pos.y()
        left_dist = pos.x() - screen_geometry.left()
        right_dist = screen_geometry.right() - pos.x()

        # Get minimum distance from horizontal and vertical screen edges.
        # This determines the orientation of the menu.
        v_dist = min(map(abs, (top_dist, bottom_dist)))
        h_dist = min(map(abs, (left_dist, right_dist)))

        # Return the nearest edge
        if h_dist < v_dist:
            if right_dist < left_dist:
                return self.DOCK_RIGHT
            else:
                return self.DOCK_LEFT
        else:
            if top_dist < bottom_dist:
                return self.DOCK_TOP
            else:
                return self.DOCK_BOTTOM

    def _set_window_mask(self):
        """ set the window mask when pinned to the systray """
        if self.state == self.STATE_WINDOWED:
            self.__content_layout.setContentsMargins(0, 0, 0, 0)
            self.clearMask()
            return

        # temp bitmap to store the mask
        bmp = QtGui.QBitmap(self.size())

        # create and configure the painter
        self.painter = QtGui.QPainter(bmp)
        self.painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing, True)

        # figure out what side to draw the anchor on
        side = self._guess_toolbar_side()

        # mask out from the top margin of the border_layout
        rect = self.rect()

        # make sure there is room to draw the anchor
        anchor_height = self.__bottom_anchor.height()
        if self.__content_layout is not None:
            if side == self.DOCK_TOP:
                mask = rect.adjusted(0, anchor_height, 0, 0)
                self.__content_layout.setContentsMargins(0, anchor_height, 0, 0)
            elif side == self.DOCK_LEFT:
                mask = rect.adjusted(anchor_height, 0, 0, 0)
                self.__content_layout.setContentsMargins(anchor_height, 0, 0, 0)
            elif side == self.DOCK_RIGHT:
                mask = rect.adjusted(0, 0, -anchor_height, 0)
                self.__content_layout.setContentsMargins(0, 0, -anchor_height, 0)
            elif side == self.DOCK_BOTTOM:
                mask = rect.adjusted(0, 0, 0, -anchor_height)
                self.__content_layout.setContentsMargins(0, 0, 0, anchor_height)
            else:
                raise ValueError("Unknown value for side: %s" % side)

        self.painter.fillRect(rect, QtCore.Qt.white)
        self.painter.setBrush(QtCore.Qt.black)
        self.painter.drawRoundedRect(mask, self.__corner_radius, self.__corner_radius)

        if self.state == self.STATE_PINNED:
            # add back in the anchor triangle
            points = []

            # make sure the triangle is drawn over the tray icon.
            rel_systray_geo_center = self.mapFromGlobal(self.systray.geometry().center())
            mask_center = QtCore.QPoint(rel_systray_geo_center.x(), mask.center().y())

            if side == self.DOCK_TOP:
                anchor_pixmap = self.__top_anchor
                anchor_center = anchor_pixmap.rect().center()
                points.append(QtCore.QPoint(mask_center.x(), rect.top()))
                points.append(QtCore.QPoint(mask_center.x() - anchor_height, mask.top()))
                points.append(QtCore.QPoint(mask_center.x() + anchor_height, mask.top()))
            elif side == self.DOCK_LEFT:
                anchor_pixmap = self.__left_anchor
                anchor_center = anchor_pixmap.rect().center()
                points.append(QtCore.QPoint(rect.left(), mask_center.y()))
                points.append(QtCore.QPoint(mask.left(), mask_center.y() - anchor_center.y()))
                points.append(QtCore.QPoint(mask.left(), mask_center.y() + anchor_center.y()))
            elif side == self.DOCK_RIGHT:
                anchor_pixmap = self.__right_anchor
                anchor_center = anchor_pixmap.rect().center()
                points.append(QtCore.QPoint(mask.right(), mask_center.y() + anchor_center.y()))
                points.append(QtCore.QPoint(mask.right(), mask_center.y() - anchor_center.y()))
                points.append(QtCore.QPoint(rect.right(), mask_center.y()))
            elif side == self.DOCK_BOTTOM:
                anchor_pixmap = self.__bottom_anchor
                anchor_center = anchor_pixmap.rect().center()
                points.append(QtCore.QPoint(mask_center.x() - anchor_height, mask.bottom()))
                points.append(QtCore.QPoint(mask_center.x() + anchor_height, mask.bottom()))
                points.append(QtCore.QPoint(mask_center.x(), rect.bottom()))
            else:
                raise ValueError("Unknown value for side: %s" % side)

            self.painter.drawPolygon(points)

        # need to end the painter to make sure that its resources get
        # garbage collected before the bitmap to avoid a crash
        self.painter.end()

        # finally set the window mask to the bitmap
        self.setMask(bmp)
        self.__anchor_side = side
