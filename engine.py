# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sys

import sgtk
import traceback
from sgtk.platform import Engine
from sgtk import LogManager

logger = LogManager.get_logger(__file__)

previous_except_hook = sys.excepthook


def unhandled_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Unhandled exception handler.

    When this file gets loaded, we ensure that both the site desktop and project
    desktop will see any unexpected errors be logged to disk and in the GUI.

    This sort of error typically happens when an error is thrown from a Qt
    application's slot and doesn't get handled.
    """
    # Calls any previous exception handler. By default, this will invoke the
    # standard out console error handler.
    if previous_except_hook:
        previous_except_hook(exc_type, exc_value, exc_traceback)

    # Send the message to the logger for this file. In the end, this will
    # get routed to many places:
    # - the log file
    # - on the site engine side, it will show up in the Shotgun Desktop's console
    # - on the project engine side, it will be forwarded to the site engine's
    #   side via the RPC, which will forward it to the console.
    try:
        logger.error(
            "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        )
    except Exception:
        # Avoid infinite recursion if we raise an error while logging.
        pass


sys.excepthook = unhandled_exception_handler


class DesktopEngine(Engine):
    def __init__(self, tk, *args, **kwargs):
        """ Constructor """
        self.__impl = None

        # Now continue with the standard initialization
        Engine.__init__(self, tk, *args, **kwargs)

        self._host_info = {"name": "Desktop", "version": "unknown"}

    @property
    def host_info(self):
        """
        :returns: A dictionary with information about the application hosting this engine.

        Note that the version field is initially set to unknown, it gets updated at a later
        stage on execution of the `DesktopEngineSiteImplementation.run` method.

        The returned dictionary is of the following form on success where the first set
        of digits refers to the 'Desktop App' version and the second set of digits to the
        `tk-framework-desktopstartup` version:

            {
                "name": "Desktop",
                "version": "v1.4.3 / v1.4.16",
            }

        The returned dictionary is of following form until it gets updated by the
        `DesktopEngineSiteImplementation.run`

            {
                "name": "Desktop",
                "version: "unknown"
            }
        """
        return self._host_info

    @property
    def register_toggle_debug_command(self):
        """
        Indicates that the tk-desktop engine should not receive a toggle debug
        engine command during engine initialization. The desktop engine provides
        its own debug logging toggle via the advanced menu provided by the engine's
        internal module.

        :rtype: bool
        """
        return False

    ############################################################################
    # Engine methods
    def init_engine(self):
        """ Initialize the engine """

        # Figure out which implementation we will use.  If the tk instance
        # has the proxy connection information in it, then we are running
        # for a specific project.  Otherwise we are running the GUI for a
        # whole site.
        interface_type = "site"
        bootstrap_data = getattr(self.sgtk, "_desktop_data", None)
        if bootstrap_data is not None:
            if "proxy_pipe" in bootstrap_data and "proxy_auth" in bootstrap_data:
                interface_type = "project"

        self._is_site_engine = interface_type == "site"

        # Import our python library
        #
        # HACK ALERT: See if we can move this part of engine initialization
        # above the call to init_engine in core.  This is needed to enable the
        # call to import_module in init_engine.
        #
        # try to pull in QT classes and assign to sgtk.platform.qt.XYZ
        from sgtk.platform import qt

        base_def = self._define_qt_base()
        qt.QtCore = base_def.get("qt_core")
        qt.QtGui = base_def.get("qt_gui")
        qt.TankDialogBase = base_def.get("dialog_base")

        tk_desktop = self.import_module("tk_desktop")

        self.__impl = tk_desktop.get_engine_implementation(interface_type)(self)

        # run the implementation init_engine if it has one
        if hasattr(self.__impl, "init_engine"):
            self.__impl.init_engine()

    def post_app_init(self):
        """ Called after all the apps have been initialized """
        if hasattr(self.__impl, "post_app_init"):
            self.__impl.post_app_init()

    def show_panel(self, panel_id, title, bundle, widget_class, *args, **kwargs):
        """
        Shows the panel in the desktop engine, if supported by the current
        desktop mode (site vs project).

        :param panel_id:     Unique identifier for the panel, as obtained by
                             register_panel().
        :param title:        The title of the panel.
        :param bundle:       The app, engine or framework object that is
                             associated with this window.
        :param widget_class: The class of the UI to be constructed. This must
                             derive from QWidget.

        Additional parameters specified will be passed through to the
        widget_class constructor.
        """
        if hasattr(self.__impl, "show_panel"):
            # forward to site/projet implementation
            return self.__impl.show_panel(
                panel_id, title, bundle, widget_class, *args, **kwargs
            )
        else:
            # fall back on base class implementation
            return super(DesktopEngine, self).show_panel(
                panel_id, title, bundle, widget_class, *args, **kwargs
            )

    def destroy_engine(self):
        """ Clean up the engine """
        self.logger.debug("destroy_engine")

        if hasattr(self.__impl, "destroy_engine"):
            self.__impl.destroy_engine()

    def _emit_log_message(self, handler, record):
        """
        Called when a message needs to be logged.
        """
        if hasattr(self.__impl, "_emit_log_message"):
            self.__impl._emit_log_message(handler, record)

    ############################################################################
    # Dispatch to our implementation
    def __getattr__(self, attr):
        if self.__impl is not None:
            return getattr(self.__impl, attr)
        raise AttributeError(
            "'%s' object has no attribute '%s'" % (self.__class__.__name__, attr)
        )

    ##########################################################################################
    # pyside / qt
    @property
    def has_ui(self):
        """ Override base has_ui to reflect the state of Qt imports """
        return self._has_ui

    @has_ui.setter
    def has_ui(self, has_a_ui):
        """ Allows to set the has ui property. """
        self._has_ui = has_a_ui

    def _define_unavailable_base(self):
        # proxy class used when QT does not exist on the system.
        # this will raise an exception when any QT code tries to use it
        class QTProxy(object):
            def __getattr__(self, name):
                raise sgtk.TankError(
                    "Looks like you are trying to run an App that uses a QT based UI, however the "
                    "python installation that the Desktop engine is currently using does not seem "
                    "to contain a valid PySide or PyQt4 install. Either install PySide into your "
                    "python environment or alternatively switch back to using the native Shotgun "
                    "Desktop python installation, which includes full QT support."
                )

        base = {"qt_core": QTProxy(), "qt_gui": QTProxy(), "dialog_base": None}
        self._has_ui = False
        return base

    def _define_qt_base(self):
        """ check for pyside then pyqt """
        base = Engine._define_qt_base(self)

        # If QtCore hasn't been set, then nothing was.
        if base["qt_core"] is None:
            return self._define_unavailable_base()

        try:
            QtCore = base["qt_core"]
            DialogBase = base["dialog_base"]
            QtWrapper = base["wrapper"]

            # tell QT to interpret C strings as utf-8
            utf8 = QtCore.QTextCodec.codecForName("utf-8")
            QtCore.QTextCodec.setCodecForCStrings(utf8)

            # a simple dialog proxy that pushes the window forward
            class ProxyDialog(DialogBase):

                _requires_visibility_hack = (
                    True
                    if sgtk.util.is_windows() and not self._is_site_engine
                    else False
                )

                def setVisible(self, make_visible):
                    # On Windows, a bug in Qt seems to prevent the first dialog we invoke to appear in the
                    # background process. This seems to be related to the fact that the background process
                    # doesn't even have a presence in the task bar. If we give the background process a
                    # taskbar presence, then dialogs will appear right away. So when there is a request to
                    # show the first dialog, we will "show" another dialog first, which will clean up
                    # whatever incoherent state there is in Qt and will allow the requested dialog to
                    # appear.
                    if self._requires_visibility_hack:
                        d = DialogBase()
                        d.show()
                        d.activateWindow()
                        d.raise_()
                        d.close()
                        d.deleteLater()
                        self._requires_visibility_hack = False

                    DialogBase.setVisible(self, make_visible)

                def show(self):
                    DialogBase.show(self)
                    self.activateWindow()
                    self.raise_()

                def exec_(self):
                    self.activateWindow()
                    self.raise_()
                    # the trick of activating + raising does not seem to be enough for
                    # modal dialogs. So force put them on top as well.
                    self.setWindowFlags(
                        QtCore.Qt.WindowStaysOnTopHint | self.windowFlags()
                    )
                    return DialogBase.exec_(self)

            base["dialog_base"] = ProxyDialog
            self._has_ui = True
            self._has_qt = True
            # Strip the name since PySide has a \n at the end for some reason.
            self.log_debug(
                "Successfully initialized %s '%s' located in %s."
                % (
                    QtWrapper.__name__.strip(),
                    QtWrapper.__version__,
                    QtWrapper.__file__,
                )
            )

            return base
        except Exception as e:
            self.log_warning(
                "Error setting up qt. Qt based UI support will not "
                "be available: %s" % e
            )
            return self._define_unavailable_base()
