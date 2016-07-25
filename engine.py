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
import traceback

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

        # Figure out which implementation we will use.  If the tk instance
        # has the proxy connection information in it, then we are running
        # for a specific project.  Otherwise we are running the GUI for a
        # whole site.
        interface_type = "site"
        bootstrap_data = getattr(self.sgtk, "_desktop_data", None)
        if bootstrap_data is not None:
            if "proxy_pipe" in bootstrap_data and "proxy_auth" in bootstrap_data:
                interface_type = "project"

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
        self.logger.debug("destroy_engine")

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
        # We allow other handlers to be added to the logger (the GUI console for example).
        # Track them so we can clean them up when we clean up logging
        self.__extra_handlers = []

    def _tear_down_logging(self):
        # clear the handlers so we don't end up with duplicate messages
        while (self.__extra_handlers):
            self.logger.removeHandler(self.__extra_handlers.pop())

    def add_logging_handler(self, handler):
        sgtk.LogManager().initialize_custom_handler(handler)
        self.__extra_handlers.append(handler)

    ##########################################################################################
    # pyside / qt
    @property
    def has_ui(self):
        """ Override base has_ui to reflect the state of Qt imports """
        return self._has_ui

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

        if not self._has_ui:
            try:
                from PySide import QtCore, QtGui
                import PySide

                # Some old versions of PySide don't include version information
                # so add something here so that we can use PySide.__version__
                # later without having to check!
                if not hasattr(PySide, "__version__"):
                    PySide.__version__ = "<unknown>"

                # tell QT to interpret C strings as utf-8
                utf8 = QtCore.QTextCodec.codecForName("utf-8")
                QtCore.QTextCodec.setCodecForCStrings(utf8)

                # a simple dialog proxy that pushes the window forward
                class ProxyDialogPySide(QtGui.QDialog):
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
                base["dialog_base"] = ProxyDialogPySide
                self.logger.debug("Successfully initialized PySide '%s' located in %s."
                               % (PySide.__version__, PySide.__file__))
                self._has_ui = True
            except ImportError:
                pass
            except Exception, e:
                self.logger.warning("Error setting up pyside. Pyside based UI support will not "
                                 "be available: %s" % e)

        if not self._has_ui:
            try:
                from PyQt4 import QtCore, QtGui
                import PyQt4

                # tell QT to interpret C strings as utf-8
                utf8 = QtCore.QTextCodec.codecForName("utf-8")
                QtCore.QTextCodec.setCodecForCStrings(utf8)

                # a simple dialog proxy that pushes the window forward
                class ProxyDialogPyQt(QtGui.QDialog):
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

                # hot patch the library to make it work with pyside code
                QtCore.Signal = QtCore.pyqtSignal
                QtCore.Slot = QtCore.pyqtSlot
                QtCore.Property = QtCore.pyqtProperty
                base["qt_core"] = QtCore
                base["qt_gui"] = QtGui
                base["dialog_base"] = ProxyDialogPyQt
                self.logger.debug("Successfully initialized PyQt '%s' located in %s."
                               % (QtCore.PYQT_VERSION_STR, PyQt4.__file__))
                self._has_ui = True
            except ImportError:
                pass
            except Exception, e:
                self.logger.warning("Error setting up PyQt. PyQt based UI support will not "
                                 "be available: %s" % e)

        return base
