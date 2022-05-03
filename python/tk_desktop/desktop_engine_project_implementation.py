# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Shotgun Desktop project-level engine implementation.
"""

from __future__ import with_statement

import time
import os
import sys
import fnmatch
import traceback
import threading

from sgtk import LogManager
import sgtk

from .project_communication import ProjectCommunication
from .extensions import osutils

logger = LogManager.get_logger(__name__)


class DesktopEngineProjectImplementation(object):
    """
    Launches an RPC server which listens for requests from the Shotgun Desktop to launch an app.
    """

    def __init__(self, engine):
        """
        :param engine: Actual Toolkit engine this implementation is for.
        """
        self._engine = engine
        self._project_comm = ProjectCommunication(engine)
        self.__callback_map = {}
        self._lock = threading.Lock()

    def post_app_init(self):
        """
        Initializes the connection with the site engine and registers all callbacks.
        """
        try:
            # It is tempting to move connect to server in the init engine, so that logs
            # can go as early as possible to the site's logger. But that's a bad idea, because it
            # introduces races condition between Qt discovery, QApplication instantiation and an early
            # request to shut down the process.
            # Here's the flow of operations if we let during engine init to connect to the site engine.
            #
            #  Site Engine                                Project Engine
            #          connects to site engine during engine_init
            #               and sends groups and commands
            #       <-------------------------------------------
            # RACE CONDITION STARTS HERE
            #                                              _define_qt_base
            #          server signals intention to disconnect
            #                  in _signal_disconnect
            #       ------------------------------------------->
            #                                              start_app
            # RACE CONDITION ENDS HERE
            #
            # The problem is that the intent of the server to disconnect can happen anytime while the
            # background process is initializing. The ui state (engine.has_ui and QApplication.instance()) needs
            # to be coherent for start_app and _signal_disconnect to execute properly.
            #
            # For these reasons, we are postponing the connection to the server (and therefore the possibility)
            # to be torn down to after Qt has been initialized.
            #
            # At that point, it is possible to evaluate engine.has_ui and QApplication.instance() in a thread-safe
            # manner under a lock.

            self._connect_to_server()
            self._register_groups()
            self._register_commands()
        except:
            # Same deal as during init_engine.
            self.destroy_engine()
            raise

    def _connect_to_server(self):
        """
        Connects to the other process's server and starts our own.
        """
        # pull the data on how to connect to the GUI proxy from the tk instance
        bootstrap_data = self._engine.sgtk._desktop_data
        proxy_pipe = bootstrap_data["proxy_pipe"]
        proxy_auth = bootstrap_data["proxy_auth"]

        # We always prefer the HTTP pipe, as it works under every Python version.
        self._project_comm.connect_to_server(
            proxy_pipe, proxy_auth, self._signal_disconnect
        )
        # Stop logging to disk
        sgtk.LogManager().uninitialize_base_file_handler()
        logger.debug(
            "Project-level tk-desktop engine has now switched back to proxy based logging."
        )

        self._project_comm.register_function(self._trigger_callback, "trigger_callback")
        self._project_comm.register_function(
            self._test_project_locations, "test_project_locations"
        )
        self._project_comm.register_function(
            self._open_project_locations, "open_project_locations"
        )
        self._project_comm.register_function(self._get_setting, "get_setting")
        self._project_comm.register_function(self._set_global_debug, "set_global_debug")

    def _set_global_debug(self, state):
        """
        Sets the global debug to the given state.

        :param bool state: The debug state to set.
        """
        sgtk.LogManager().global_debug = state

    def _register_groups(self):
        # get the list of configured groups
        # add the default group in if it isn't already in the list.
        groups = [g["name"] for g in self._engine.get_setting("groups", [])]
        default_group = self._engine.get_setting("default_group", [])
        if default_group not in groups:
            groups.insert(0, default_group)

        # get the rules for how to collapse the buttons
        collapse_rules = self._engine.get_setting("collapse_rules", [])

        # tell the GUI how to organize our commands
        show_recents = self._engine.get_setting("show_recents", True)
        self._project_comm.call("set_groups", groups, show_recents=show_recents)
        self._project_comm.call("set_collapse_rules", collapse_rules)

    def _register_commands(self):
        # send the commands over to the proxy
        for name, command_info in self._engine.commands.items():
            self.__callback_map[("__commands", name)] = command_info["callback"]
            # pull out needed values since this needs to be pickleable
            gui_properties = {}
            for prop in [
                "type",
                "icon",
                "title",
                "description",
                "group",
                "group_default",
            ]:
                if prop in command_info["properties"]:
                    gui_properties[prop] = command_info["properties"][prop]
            # evaluate groups on the app proxy side
            groups = self._get_groups(name, gui_properties)

            # Turn this on to slow down the speed at which commands are registered so we can
            # exit the project to introduce a race condition.
            if "SGTK_DESKTOP_DEBUG_REGISTRATION" in os.environ:
                time.sleep(0.5)

            self._project_comm.call(
                "trigger_register_command", name, gui_properties, groups
            )

        # Let the proxy know command registration is complete
        self._project_comm.call_no_response("project_commands_finished")

    def destroy_engine(self):
        """
        Called when the engine is being torn-down.
        """
        # We're about to disconenct from the server, reenable file based logging.
        # Do this in a try/finally to ensure that whatever happens we are guaranteed to
        # shut down the communication with the server when we're done.
        try:
            self._enable_file_based_logging()
        finally:
            self._project_comm.shut_down()

    def _set_appkit(self, *args):
        """
        Imports AppKit module and set it for throwing an application into background.
        """
        try:
            # If we receive args we are testing,
            # manually raise an Exception
            if args:
                raise AttributeError

            import AppKit

            info = AppKit.NSBundle.mainBundle().infoDictionary()
            # Setting it to 0 will bring the application back to the foreground.
            info["LSUIElement"] = "0"

            AppKit.NSApp.setActivationPolicy_(
                AppKit.NSApplicationActivationPolicyRegular
            )
        except ImportError:
            # Since AppKit is bundled with the Desktop installer, it's possible we are using
            # an older version of the installer that doesn't contain this package. In which
            # case just move on silently.
            pass
        except AttributeError:
            # Catch AttributeError exceptions when AppKit.NSApp object is NoneType.
            pass

    def _trigger_callback(self, namespace, command, *args, **kwargs):
        callback = self.__callback_map.get((namespace, command))

        if sgtk.util.is_macos():
            # If we are on Mac with PySide2, then starting a QApplication even with no Windows
            # will steal focus from any currently focused application.
            # We set the application to use `LSUIElement=1` so that it stays in the background in start_app().
            # However we need to bring it to the foreground when we want to run an app.
            # This solution for bringing it back to the foreground is a modification of the example here:
            # https://stackoverflow.com/a/34381136/4223964
            self._set_appkit()

        try:
            callback(*args, **kwargs)
        except Exception:
            logger.error(
                "Error calling %s::%s(%s, %s):\n%s"
                % (namespace, command, args, kwargs, traceback.format_exc())
            )

    def _enable_file_based_logging(self):
        """
        Enables file based logging to the tk-desktop log file.
        """
        # We're about to disconnect from the site engine, restore our own logging system. It is possible that it has
        # already been re-enabled already however. This happens when the desktop site engine disconnects from us and
        # triggers _signal_disconnect, which re-enables logging while we are still running some UIs, in which case
        # the engine will be destroyed only when the last dialog will be closed. At that point, we don't need to
        # initialize the base file handler. Ensuring that it is not enabled means there won't be spurious log
        # messages about switching handlers in the log files.
        if not sgtk.LogManager().base_file_handler:
            logger.debug(
                "Project-level tk-desktop engine will now switch back to file based logging."
            )
            sgtk.LogManager().initialize_base_file_handler("tk-desktop")

    def _signal_disconnect(self):
        # We were disconnected from the server, restore file-based logging.
        self._enable_file_based_logging()
        # If the user is quick enough and steps out of the project right after launching it, the engine
        # will be initialized but the app won't be.
        with self._lock:
            # QtGui is accessible in non-qt-based environments through the QtProxy, but won't be accessed if has_ui is
            # False.
            from tank.platform.qt import QtGui

            # If the engine reports having qt, but the QApplication hasn't been initialized yet, we want to make sure
            # that the _signal_disconnect and start_app both use the same part of if self._engine.has_ui.
            self._engine.has_ui = (
                True
                if (self._engine.has_ui and QtGui.QApplication.instance())
                else False
            )

        if self._engine.has_ui:
            app = QtGui.QApplication.instance()

            top_level_windows = app.topLevelWidgets()
            sgtk.platform.current_engine()
            # Bugs in client code (or Toolkit) can cause a leak of a top-level dialog that is already
            # closed. So if any top level dialog is visible, wait for it to close.
            opened_windows = list(filter(lambda w: w.isVisible(), top_level_windows))
            if opened_windows:
                logger.debug("The following top level widgets are still visible:")
                for w in opened_windows:
                    logger.debug(str(w))
                logger.debug("Process will quit only when the last window is closed.")
                app.setQuitOnLastWindowClosed(True)
            else:
                logger.debug("Quitting on disconnect")
                app.quit()
        else:
            self._project_comm.shut_down()

    def start_app(self):
        """
        Starts the main processing look.
        """
        # Evaluate has_ui and initialize QApplication in a thread safe manner. This is because the site engine
        # can be asking us to disconnect at the same time as we are executing start app. To make sure
        # that methods use a coherent synchronization strategy to end the process, we will make sure we've
        # agreed how it should work.
        with self._lock:
            if self._engine.has_ui:
                app = self._initialize_application()

        if self._engine.has_ui:
            result = 0
            while True:
                if not self._project_comm.connected:
                    # we have been signaled to quit rather than waiting for more commands
                    break
                # loop until we are signaled to close, in case an app accidentally quits the app
                result = app.exec_()
            return result

        else:  # not engine.has_ui
            # wait for the engine communication channel to shut down
            self._project_comm.join()
            return 0

    def _initialize_application(self):
        from tank.platform.qt import QtGui

        if sgtk.util.is_macos():
            # If we are on Mac with PySide2, then starting a QApplication even with no Windows
            # will steal focus from any currently focused application.
            # So we need to use AppKit if available to stop it from stealing focus.
            try:
                import AppKit

                info = AppKit.NSBundle.mainBundle().infoDictionary()
                info["LSUIElement"] = "1"
            except ImportError:
                # Since AppKit is bundled with the Desktop installer, it's possible we are using
                # an older version of the installer that doesn't contain this package. In which
                # case just move on silently.
                pass

        app = QtGui.QApplication([])

        # We may launch multiple UI apps, do not quit as soon as the last one closes.
        app.setQuitOnLastWindowClosed(False)

        # Make the name pretty for the tray and the task manager.
        app.setApplicationName("%s Python" % self._engine.context.project["name"])
        # set default icon
        python_icon = os.path.join(self._engine.disk_location, "icon_bg_python.png")
        app.setWindowIcon(QtGui.QIcon(python_icon))

        self.register_qapplication(app)
        # use the toolkit look and feel
        self._engine._initialize_dark_look_and_feel()

        return app

    ############################################################################
    # Pre Desktop engine 2.0.17 compatibility section
    # Do not rename or remove methods in this section or it will break compatibility
    # with older site engines.

    def register_qapplication(self, app):
        """
        Called when QApplication has been created.

        :param app: QApplication instance.
        """
        # Make sure we shut down cleanly.
        app.aboutToQuit.connect(self._engine.destroy)

    @property
    def connected(self):
        """
        Indicates if we're still connected to the site engine.
        """
        return self._project_comm.connected

    @property
    def msg_server(self):
        """
        The msg_server functionality has now been wrapped into the ProjectCommunication object.
        """
        return self._project_comm

    # End of pre Desktop engine 2.0.17 compatibility section
    ############################################################################

    def _test_project_locations(self):
        """
        Tests for the availability of the project locations.

        :returns: True when there are file system locations; False otherwise.
        """

        return bool(self._engine.context.filesystem_locations)

    def _open_project_locations(self):
        """
        Open the project locations in an os specific browser window.
        """
        paths = self._engine.context.filesystem_locations

        for disk_location in paths:
            # run the app
            if sgtk.util.is_linux():
                cmd = 'xdg-open "%s"' % disk_location
            elif sgtk.util.is_macos():
                cmd = 'open "%s"' % disk_location
            elif sgtk.util.is_windows():
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % sys.platform)

            exit_code = os.system(cmd)
            if exit_code != 0:
                logger.error("Failed to launch '%s'!" % cmd)

    def _get_setting(self, setting_name, default_value=None):
        """
        Look up engine setting for current environment.

        :param setting_name: Name of the setting to retrieve.
        :param default_value: If the setting is missing, ``default_value`` will be returned.

        :returns: The setting's value.
        """
        return self._engine.get_setting(setting_name, default_value)

    def _emit_log_message(self, handle, record):
        """
        Logs a message to the site engine if available, otherwise logs to disk.
        """
        # If there is no file logger, attempt to send the message to the proxy server.
        if not sgtk.LogManager().base_file_handler:
            # If we can log through the proxy, only do that to avoid
            # duplicate entries in the log file.
            # Note any changes made here, should also be considered for the `ProxyLoggingHandler` class in the
            # bootstrap_utilities module.

            # Do not send logs if the connection is closed!
            if not self._project_comm.connected:
                return

            # If we have exception details, we need to format these and combine them with the message, as the traceback
            # object can't be serialize and passed over the proxy.
            if record.exc_info:
                formatted_tracback = "".join(
                    traceback.format_exception(*record.exc_info)
                )
                msg = "{msg}\n{traceback}".format(
                    msg=record.msg, traceback=formatted_tracback
                )
            else:
                msg = record.msg

            # Do the string interpolation this side of the communication. This is important
            # because Python 2 and 3 may serialize objects differently and Toolkit objects
            # may be coming from different versions of the API.
            if record.args:
                msg = msg % record.args

            try:
                self._project_comm.call_no_response(
                    "proxy_log", record.levelno, msg, []
                )
                return
            except Exception:
                # Ignore log failures, this is important, as we don't want logging to
                # cause issues.
                pass

    def _get_groups(self, name, properties):
        display_name = properties.get("title", name)

        default_group = self._engine.get_setting("default_group", "Studio")
        groups = self._engine.get_setting("groups", [])

        matches = []
        for group in groups:
            for match in group["matches"]:
                if fnmatch.fnmatch(display_name.lower(), match.lower()):
                    matches.append(group["name"])
                    break

        if not matches:
            matches = [default_group]

        logger.debug("'%s' goes in groups: %s" % (display_name, matches))
        return matches
