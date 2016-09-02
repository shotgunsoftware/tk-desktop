# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys
import logging
import traceback
import logging.handlers

import sgtk
from sgtk.platform import Engine


class DesktopEngine(Engine):
    def __init__(self, tk, *args, **kwargs):
        """ Constructor """
        self.__impl = None

        # Need to init logging before init_engine to satisfy logging from framework setup
        self._initialize_logging()

        # Now continue with the standard initialization
        Engine.__init__(self, tk, *args, **kwargs)

    ############################################################################
    # Engine methods
    def init_engine(self):
        """ Initialize the engine """
        # set logging to the proper level from settings
        if self.get_setting("debug_logging", False):
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger.setLevel(logging.INFO)

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

        # give the implementation a chance to update logging
        if hasattr(self.__impl, "_initialize_logging"):
            self.__impl._initialize_logging()

    def post_app_init(self):
        """ Called after all the apps have been initialized """
        if hasattr(self.__impl, "post_app_init"):
            self.__impl.post_app_init()

    def destroy_engine(self):
        """ Clean up the engine """
        self.log_debug("destroy_engine")

        # clean up our logging setup
        self._tear_down_logging()

        if hasattr(self.__impl, "destroy_engine"):
            self.__impl.destroy_engine()

    ############################################################################
    # Dispatch to our implementation
    def __getattr__(self, attr):
        if self.__impl is not None:
            return getattr(self.__impl, attr)
        raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, attr))

    ############################################################################
    # Logging
    def _initialize_logging(self):
        # platform specific locations for the log file
        if sys.platform == "darwin":
            fname = os.path.join(os.path.expanduser("~"), "Library", "Logs", "Shotgun", "tk-desktop.log")
        elif sys.platform == "win32":
            fname = os.path.join(os.environ.get("APPDATA", "APPDATA_NOT_SET"), "Shotgun", "tk-desktop.log")
        elif sys.platform.startswith("linux"):
            fname = os.path.join(os.path.expanduser("~"), ".shotgun", "logs", "tk-desktop.log")
        else:
            raise NotImplementedError("Unknown platform: %s" % sys.platform)

        # create the directory for the log file
        log_dir = os.path.dirname(fname)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # setup default logger, used in the new default exception hook
        self._logger = logging.getLogger("tk-desktop")
        self._handler = logging.handlers.RotatingFileHandler(fname, maxBytes=1024*1024, backupCount=5)
        formatter = logging.Formatter("%(asctime)s [%(process) -5d %(levelname) -7s] %(name)s - %(message)s")
        self._handler.setFormatter(formatter)
        self._logger.addHandler(self._handler)

        # We allow other handlers to be added to the logger (the GUI console for example).
        # Track them so we can clean them up when we clean up logging
        self.__extra_handlers = []

    def _tear_down_logging(self):
        # clear the handlers so we don't end up with duplicate messages
        self._logger.removeHandler(self._handler)
        while (self.__extra_handlers):
            self._logger.removeHandler(self.__extra_handlers.pop())

    def log(self, level, msg, *args):
        if self.__impl is None:
            # implementation has not been setup yet, log directly to the logger
            self._logger.log(level, msg, *args)
        else:
            # implementation has been setup, let it handle the logging
            self.__impl.log(level, msg, *args)

    def log_debug(self, msg, *args):
        self.log(logging.DEBUG, msg, *args)

    def log_info(self, msg, *args):
        self.log(logging.INFO, msg, *args)

    def log_warning(self, msg, *args):
        self.log(logging.WARNING, msg, *args)

    def log_error(self, msg, *args):
        self.log(logging.ERROR, msg, *args)

    def log_exception(self, msg, *args):
        if self.__impl is None:
            # implementation has not been setup yet, log directly to the logger
            self._logger.exception(msg, *args)
        else:
            if msg is not None:
                # implementation has been setup, let it handle the logging
                exception_msg = str(msg) + "\n" + traceback.format_exc()
            else:
                exception_msg = traceback.format_exc()
            self.__impl.log(logging.ERROR, exception_msg, *args)

    def add_logging_handler(self, handler):
        self._logger.addHandler(handler)
        self.__extra_handlers.append(handler)

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

    def _define_qt_base(self):
        """ check for pyside then pyqt """
        # proxy class used when QT does not exist on the system.
        # this will raise an exception when any QT code tries to use it
        class QTProxy(object):
            def __getattr__(self, name):
                raise sgtk.TankError("Looks like you are trying to run an App that uses a QT based UI, however the "
                                     "python installation that the Desktop engine is currently using does not seem "
                                     "to contain a valid PySide or PyQt4 install. Either install PySide into your "
                                     "python environment or alternatively switch back to using the native Shotgun "
                                     "Desktop python installation, which includes full QT support.")

        base = {"qt_core": QTProxy(), "qt_gui": QTProxy(), "dialog_base": None}
        self._has_ui = False

        try:
            from PySide import QtCore, QtGui
            import PySide

            # Some old versions of PySide don't include version information
            # so add something here so that we can use PySide.__version__
            # later without having to check!
            if not hasattr(PySide, "__version__"):
                PySide.__version__ = "<unknown>"

            self.log_debug("Found PySide '%s' located in %s." % (PySide.__version__, PySide.__file__))
        except ImportError:
            try:
                from PyQt4 import QtCore, QtGui
                import PyQt4
                QtCore.Signal = QtCore.pyqtSignal
                QtCore.Slot = QtCore.pyqtSlot
                QtCore.Property = QtCore.pyqtProperty

                self.log_debug("Found PyQt '%s' located in %s." % (QtCore.PYQT_VERSION_STR, PyQt4.__file__))
            except ImportError:
                return base
        except Exception:
            self.log_exception("Error setting up QT. QT based UI support will not be available: %s" % e)
            return base

        # tell QT to interpret C strings as utf-8
        utf8 = QtCore.QTextCodec.codecForName("utf-8")
        QtCore.QTextCodec.setCodecForCStrings(utf8)

        # a simple dialog proxy that pushes the window forward
        class ProxyDialog(QtGui.QDialog):

            _requires_visibility_hack = True if sys.platform == "win32" and not self._is_site_engine else False

            def setVisible(self, make_visible):
                # On Windows, a bug in Qt seems to prevent the first dialog we invoke to appear in the
                # background process. This seems to be related to the fact that the background process
                # doesn't even have a presence in the task bar. If we give the background process a
                # taskbar presence, then dialogs will appear right away. So when there is a request to
                # show the first dialog, we will "show" another dialog first, which will clean up
                # whatever incoherent state there is in Qt and will allow the requested dialog to
                # appear.
                if self._requires_visibility_hack:
                    d = QtGui.QDialog()
                    d.show()
                    d.activateWindow()
                    d.raise_()
                    d.deleteLater()
                    self._requires_visibility_hack = False

                QtGui.QDialog.setVisible(self, make_visible)

            def show(self):
                QtGui.QDialog.show(self)
                self.activateWindow()
                self.raise_()

            def exec_(self):
                self.activateWindow()
                self.raise_()
                # the trick of activating + raising does not seem to be enough for
                # modal dialogs. So force put them on top as well.
                self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | self.windowFlags())
                return QtGui.QDialog.exec_(self)

        base["qt_core"] = QtCore
        base["qt_gui"] = QtGui
        base["dialog_base"] = ProxyDialog
        self._has_ui = True

        return base
