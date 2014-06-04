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
import re
import sys
import string
import logging
import fnmatch
import traceback
import collections
import logging.handlers

import sgtk
from sgtk.platform import Engine
from sgtk.errors import TankEngineInitError


class KeyedDefaultDict(collections.defaultdict):
    """
    Simple class to provide a dictionary whose default value for a key is a
    function of that key.
    """
    def __missing__(self, key):
        # call the default factory with the key as an argument
        ret = self[key] = self.default_factory(key)
        return ret


class DisplayNameTemplate(string.Template):
    def __init__(self, template):
        # since the template is going to be used as a regex, escape everything
        # except $ so that it isn't interpreted as part of the re we are building
        template = re.escape(template).replace("\\$", "$")
        string.Template.__init__(self, template)

        # do a substitution where we build a regular expression with a group
        # for each dollar var we match, substitute in a group named after
        # the variable that will match any non-whitespace characters
        default_kwargs = KeyedDefaultDict(lambda k: "(?P<%s>\S+)" % k)
        self.match_re = re.compile(self.safe_substitute(default_kwargs))

    def match(self, match_string):
        """
        Given a string, if the string matches the template, return a dictionary
        where each key:value represents a substitution from the variables that
        matched the template.  If the string does not match the template, returns
        None.
        """
        match = self.match_re.match(match_string)
        if match:
            return match.groupdict()
        return None


class DesktopEngine(Engine):
    def __init__(self, tk, *args, **kwargs):
        """ Constructor """
        # Need to init logging before init_engine to satisfy logging from framework setup
        self._initialize_logging()

        # Now continue with the standard initialization
        Engine.__init__(self, tk, *args, **kwargs)

    def init_engine(self):
        """ Initialize the engine """
        # set logging to the proper level from settings
        if self.get_setting("debug_logging", False):
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger.setLevel(logging.INFO)

        self.proxy = None
        self.msg_server = None

        self.__callback_map = {}  # mapping from (namespace, name) to callbacks

        # rules that determine how to collapse commands into buttons
        # each rule is a dictionary with keys for match, button_label, and
        # menu_label
        self.__collapse_rules = []

        # see if we are running with a gui proxy
        self.has_gui = True
        self.has_gui_proxy = False
        self.disconnected = True
        bootstrap_data = getattr(self.sgtk, "_desktop_data", None)
        if bootstrap_data is not None:
            if "proxy_pipe" in bootstrap_data and "proxy_auth" in bootstrap_data:
                self.has_gui = False
                self.has_gui_proxy = True
                self.disconnected = False

        # HACK ALERT: See if we can move this part of engine initialization
        # above the call to init_engine in core
        #
        # try to pull in QT classes and assign to sgtk.platform.qt.XYZ
        from sgtk.platform import qt
        base_def = self._define_qt_base()
        qt.QtCore = base_def.get("qt_core")
        qt.QtGui = base_def.get("qt_gui")
        qt.TankDialogBase = base_def.get("dialog_base")

        self.tk_desktop = self.import_module("tk_desktop")

        # we have a gui proxy, connect to it via the data from the bootstrap
        if self.has_gui_proxy:
            pipe = bootstrap_data["proxy_pipe"]
            auth = bootstrap_data["proxy_auth"]
            self.log_info("Connecting to gui pipe %s" % pipe)

            # create the connection to the gui proxy
            self.proxy = self.tk_desktop.RPCProxy(pipe, auth)

            # startup our server to receive gui calls
            self.start_app_server()

            # get the list of configured groups
            groups = [g["name"] for g in self.get_setting("groups", [])]
            default_group = self.get_setting("default_group", [])

            # add the default group in if it isn't already in the list.
            # it goes at the beginning by default
            if default_group not in groups:
                groups.insert(0, default_group)

            # get the rules for how to collapse the buttons
            collapse_rules = self.get_setting("collapse_rules", [])

            # and register our side of the pipe as the current app proxy
            self.proxy.create_app_proxy(self.msg_server.pipe, self.msg_server.authkey)
            self.proxy.set_groups(groups)
            self.proxy.set_collapse_rules(collapse_rules)

    def post_app_init(self):
        """ Called after all the apps have been initialized """
        if self.has_gui_proxy:
            # send the commands over to the proxy
            for name, command_info in self.commands.iteritems():
                self.__callback_map[("__commands", name)] = command_info["callback"]

                # pull out needed values since this needs to be pickleable
                gui_properties = {}
                for prop in ["type", "icon", "title", "description"]:
                    if prop in command_info["properties"]:
                        gui_properties[prop] = command_info["properties"][prop]

                # evaluate groups on the app proxy side
                groups = self._get_groups(name, gui_properties)
                self.proxy.trigger_register_command(name, gui_properties, groups)

            # need to let the gui proxy know that all apps have been initialized
            self.proxy.finish_app_initialization()

    def start_app_server(self):
        """ Start up the app side rpc server """
        if self.msg_server is not None:
            self.msg_server.close()

        self.msg_server = self.tk_desktop.RPCServerThread(self)
        self.msg_server.register_function(self.trigger_callback, "trigger_callback")
        self.msg_server.register_function(self.trigger_disconnect, "signal_disconnect")
        self.msg_server.register_function(self.open_project_locations, "open_project_locations")

        self.msg_server.start()

    def start_gui_server(self):
        """ Start up the gui side rpc server """
        if self.msg_server is not None:
            self.msg_server.close()

        self.msg_server = self.tk_desktop.RPCServerThread(self)
        self.msg_server.register_function(self.app_proxy_startup_error, "engine_startup_error")
        self.msg_server.register_function(self.create_app_proxy, "create_app_proxy")
        self.msg_server.register_function(self.set_groups, "set_groups")
        self.msg_server.register_function(self.set_collapse_rules, "set_collapse_rules")
        self.msg_server.register_function(self.destroy_app_proxy, "destroy_app_proxy")
        self.msg_server.register_function(self.trigger_register_command, "trigger_register_command")
        self.msg_server.register_function(self.trigger_finish_app_initialization, "finish_app_initialization")
        self.msg_server.register_function(self.trigger_gui, "trigger_gui")

        self.msg_server.start()

    def destroy_engine(self):
        """ Clean up the engine """
        # clean up our logging setup
        self._tear_down_logging()

        # if we have a gui proxy alert it to the destruction
        if self.has_gui_proxy:
            self.proxy.destroy_app_proxy()
            self.proxy.close()

        # and close down our server thread
        self.msg_server.close()

    def open_project_locations(self):
        """ Open the project locations in an os specific browser window """
        paths = self.context.filesystem_locations
        for disk_location in paths:
            # get the setting
            system = sys.platform

            # run the app
            if system.startswith("linux"):
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)

            exit_code = os.system(cmd)
            if exit_code != 0:
                self.log_error("Failed to launch '%s'!" % cmd)

    def create_app_proxy(self, pipe, authkey):
        self.proxy = self.tk_desktop.RPCProxy(pipe, authkey)

    def disconnect_app_proxy(self):
        """ Disconnect from the app proxy. """
        if self.proxy is not None:
            try:
                self.proxy.signal_disconnect(__proxy_expected_return=False)
                self.proxy.close()
            except Exception, e:
                self.log_warning("Error disconnecting from proxy: %s", e)
            finally:
                self.proxy = None

    def set_groups(self, groups):
        self.desktop_window.set_groups(groups)

    def set_collapse_rules(self, collapse_rules):
        self.__collapse_rules = collapse_rules

    def destroy_app_proxy(self):
        """ App proxy has been destroyed, clean up state. """
        self.desktop_window.clear_app_uis()
        self.proxy.close()
        self.proxy = None

    ############################################################################
    # App proxy side methods

    def call_callback(self, namespace, command, *args, **kwargs):
        self.log_debug("calling callback %s::%s(%s, %s)" % (namespace, command, args, kwargs))
        self.proxy.trigger_callback(namespace, command, *args, **kwargs)

    def trigger_callback(self, namespace, command, *args, **kwargs):
        callback = self.__callback_map.get((namespace, command))
        try:
            callback(*args, **kwargs)
        except Exception:
            self.log_error("Error calling %s::%s(%s, %s):\n%s" % (
                namespace, command, args, kwargs, traceback.format_exc()))

    def trigger_disconnect(self):
        from tank.platform.qt import QtGui

        app = QtGui.QApplication.instance()
        self.disconnected = True

        top_level_windows = app.topLevelWidgets()
        if top_level_windows:
            self.log_debug("Disconnected with open windows, setting quit on last window closed.")
            app.setQuitOnLastWindowClosed(True)
        else:
            self.log_debug("Quitting on disconnect")
            app.quit()

    def register_gui(self, namespace, callback):
        """
        App side method to register a callback to build a gui when a
        namespace is triggered.
        """
        self.__callback_map[namespace] = callback

    def trigger_build_gui(self, namespace):
        """
        App side method to trigger the building of a GUI for a given namespace.
        """
        self.proxy.trigger_gui(namespace)

    ############################################################################
    # GUI side methods

    def trigger_gui(self, namespace):
        """ GUI side handler for building a custom GUI. """
        callback = self.__callback_map.get(namespace)

        if callback is not None:
            parent = self.desktop_window.get_app_widget(namespace)
            callback(parent)

    def trigger_finish_app_initialization(self):
        """ GUI side handler called after app initialization is finished. """
        # self.desktop_window.ui.project_commands.finalize()

    def trigger_register_command(self, name, properties, groups):
        """ GUI side handler for the add_command call. """
        from tank.platform.qt import QtGui

        self.log_debug("register_command(%s, %s)", name, properties)

        command_type = properties.get("type")
        command_icon = properties.get("icon")
        command_tooltip = properties.get("description")

        icon = None
        if command_icon is not None:
            if os.path.exists(command_icon):
                icon = QtGui.QIcon(command_icon)
            else:
                self.log_error("Icon for command '%s' not found: '%s'" % (name, command_icon))

        title = self._get_display_name(name, properties)

        if command_type == "context_menu":
            # Add the command to the project menu
            action = QtGui.QAction(self.desktop_window)
            if icon is not None:
                action.setIcon(icon)
            if command_tooltip is not None:
                action.setToolTip(command_tooltip)
            action.setText(title)

            def action_triggered():
                self.context_menu_app_triggered(name, properties)
            action.triggered.connect(action_triggered)
            self.desktop_window.add_to_project_menu(action)
        else:
            # Default is to add an icon/label for the command

            # figure out what the button should be labeled
            # default is that the button has no menu and is labeled
            # the display name of the command
            menu_name = None
            button_name = title
            for collapse_rule in self.__collapse_rules:

                template = DisplayNameTemplate(collapse_rule["match"])
                match = template.match(title)
                if match is not None:
                    self.log_debug("matching %s against %s" % (title, collapse_rule["match"]))
                    if collapse_rule["menu_label"] == "None":
                        menu_name = None
                    else:
                        menu_name = string.Template(collapse_rule["menu_label"]).safe_substitute(match)
                    button_name = string.Template(collapse_rule["button_label"]).safe_substitute(match)
                    break

            self.desktop_window._project_command_model.add_command(
                name, button_name, menu_name, icon, command_tooltip, groups)

    def context_menu_app_triggered(self, name, properties):
        """ App triggered from the project specific menu. """
        # make sure to pass in that we are not expecting a response
        # Especially for the engine restart command, the connection
        # itself gets reset and so there isn't a channel to get a
        # response back.
        self.proxy.trigger_callback("__commands", name, __proxy_expected_return=False)

    def _handle_button_command_triggered(self, group, name):
        """ Button clicked from a registered command. """
        self.proxy.trigger_callback("__commands", name, __proxy_expected_return=False)

    def app_proxy_startup_error(self, error, tb=None):
        """ Handle an error starting up the engine for the app proxy. """
        if isinstance(error, TankEngineInitError):
            message = "Error starting engine\n\n%s" % error.message
        else:
            message = "Unknown Error\n\n%s" % error.message

        # add the traceback if debug is true
        if self.get_setting("debug_logging", False) and tb is not None:
            message += "\n\n%s" % tb

        self.log_error(message)
        self.desktop_window.project_overlay.show_error_message(message)

    def clear_app_groups(self):
        pass

    def _get_display_name(self, name, properties):
        return properties.get("title", name)

    def _get_groups(self, name, properties):
        display_name = self._get_display_name(name, properties)

        default_group = self.get_setting("default_group", "Studio")
        groups = self.get_setting("groups", [])

        matches = []
        for group in groups:
            for match in group["matches"]:
                if fnmatch.fnmatch(display_name.lower(), match.lower()):
                    matches.append(group["name"])
                    break

        if not matches:
            matches = [default_group]

        self.log_debug("'%s' goes in groups: %s" % (display_name, matches))
        return matches

    def run(self, splash=None):
        """
        Run the engine.

        This method is called from the GUI bootstrap to setup the application
        and to run the Qt event loop.
        """
        # Initialize Qt app
        from tank.platform.qt import QtGui

        self.app = QtGui.QApplication.instance()
        if self.app is None:
            # setup the stylesheet
            QtGui.QApplication.setStyle("cleanlooks")
            self.app = QtGui.QApplication(sys.argv)
            css_file = os.path.join(self.disk_location, "resources", "dark.css")
            f = open(css_file)
            css = f.read()
            f.close()
            self.app.setStyleSheet(css)

        # update the app icon
        icon = QtGui.QIcon(":res/default_systray_icon")
        self.app.setWindowIcon(icon)

        splash.showMessage("Building UI")

        # initialize System Tray
        self.desktop_window = self.tk_desktop.DesktopWindow()

        # hide the splash if it exists
        if splash is not None:
            splash.finish(self.desktop_window)

        # and run the app
        return self.app.exec_()

    ############################################################################
    # Logging

    def _initialize_logging(self):
        # platform specific locations for the log file
        if sys.platform == "darwin":
            fname = os.path.join(os.path.expanduser("~"), "Library", "Logs", "Shotgun", "tk-desktop.log")
        elif sys.platform == "win32":
            fname = os.path.join(os.environ.get("APPDATA", "APPDATA_NOT_SET"), "Shotgun", "tk-desktop.log")
        elif sys.platform.startswith("linux"):
            fname = os.path.join(os.path.expanduser("~"), ".shotgun", "tk-desktop.log")
        else:
            raise NotImplementedError("Unknown platform: %s" % sys.platform)

        # create the directory for the log file
        log_dir = os.path.dirname(fname)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # setup default logger, used in the new default exception hook
        self._logger = logging.getLogger("tk-desktop")
        self._handler = logging.handlers.RotatingFileHandler(fname, maxBytes=1024*1024, backupCount=5)
        formatter = logging.Formatter("%(asctime)s %(process) 5d [%(levelname) -7s] %(name)s - %(message)s")
        self._handler.setFormatter(formatter)
        self._logger.addHandler(self._handler)

    def _tear_down_logging(self):
        # clear the handler so we don't end up with duplicate messages
        self._logger.removeHandler(self._handler)

    def log_debug(self, msg, *args):
        self._logger.debug(msg, *args)

    def log_info(self, msg, *args):
        self._logger.info(msg, *args)

    def log_warning(self, msg, *args):
        self._logger.warn(msg, *args)

    def log_error(self, msg, *args):
        self._logger.error(msg, *args)

    ##########################################################################################
    # pyside / qt

    def _define_qt_base(self):
        """ check for pyside then pyqt """
        # proxy class used when QT does not exist on the system.
        # this will raise an exception when any QT code tries to use it
        class QTProxy(object):
            def __getattr__(self, name):
                raise sgtk.TankError("Looks like you are trying to run an App that uses a QT "
                                     "based UI, however the Shell engine could not find a PyQt "
                                     "or PySide installation in your python system path. We "
                                     "recommend that you install PySide if you want to "
                                     "run UI applications from the Shell.")

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
                        QtGui.QDialog.exec_(self)

                base["qt_core"] = QtCore
                base["qt_gui"] = QtGui
                base["dialog_base"] = ProxyDialogPySide
                self.log_debug("Successfully initialized PySide '%s' located in %s."
                               % (PySide.__version__, PySide.__file__))
                self._has_ui = True
            except ImportError:
                pass
            except Exception, e:
                self.log_warning("Error setting up pyside. Pyside based UI support will not "
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
                        QtGui.QDialog.exec_(self)

                # hot patch the library to make it work with pyside code
                QtCore.Signal = QtCore.pyqtSignal
                QtCore.Slot = QtCore.pyqtSlot
                QtCore.Property = QtCore.pyqtProperty
                base["qt_core"] = QtCore
                base["qt_gui"] = QtGui
                base["dialog_base"] = ProxyDialogPyQt
                self.log_debug("Successfully initialized PyQt '%s' located in %s."
                               % (QtCore.PYQT_VERSION_STR, PyQt4.__file__))
                self._has_ui = True
            except ImportError:
                pass
            except Exception, e:
                self.log_warning("Error setting up PyQt. PyQt based UI support will not "
                                 "be available: %s" % e)

        return base
