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
import fnmatch
import logging
import traceback

from . import rpc
import sgtk


class DesktopEngineProjectImplementation(object):
    def __init__(self, engine):
        self._engine = engine

        self.proxy = None
        self.msg_server = None
        self.connected = False

    def init_engine(self):
        self.__callback_map = {}

        # pull the data on how to connect to the GUI proxy from the tk instance
        bootstrap_data = self._engine.sgtk._desktop_data
        proxy_pipe = bootstrap_data["proxy_pipe"]
        proxy_auth = bootstrap_data["proxy_auth"]

        # create the connection to the gui proxy
        self._engine.log_info("Connecting to gui pipe %s" % proxy_pipe)
        self.proxy = rpc.RPCProxy(proxy_pipe, proxy_auth)

        # startup our server to receive gui calls
        self._engine.log_debug("starting rpc")
        self.start_rpc()

        # get the list of configured groups
        # add the default group in if it isn't already in the list.
        groups = [g["name"] for g in self._engine.get_setting("groups", [])]
        default_group = self._engine.get_setting("default_group", [])
        if default_group not in groups:
            groups.insert(0, default_group)

        # get the rules for how to collapse the buttons
        collapse_rules = self._engine.get_setting("collapse_rules", [])

        # register our side of the pipe as the current app proxy
        self.proxy.call("create_app_proxy", self.msg_server.pipe, self.msg_server.authkey)
        self.connected = True

        # tell the GUI how to organize our commands
        show_recents = self._engine.get_setting("show_recents", True)
        self.proxy.call("set_groups", groups, show_recents=show_recents)
        self.proxy.call("set_collapse_rules", collapse_rules)

    def post_app_init(self):
        # send the commands over to the proxy
        for name, command_info in self._engine.commands.iteritems():
            self.__callback_map[("__commands", name)] = command_info["callback"]
            # pull out needed values since this needs to be pickleable
            gui_properties = {}
            for prop in ["type", "icon", "title", "description"]:
                if prop in command_info["properties"]:
                    gui_properties[prop] = command_info["properties"][prop]
            # evaluate groups on the app proxy side
            groups = self._get_groups(name, gui_properties)
            self.proxy.call("trigger_register_command", name, gui_properties, groups)

    def register_qapplication(self, app):
        # make sure we shut down cleanly
        app.aboutToQuit.connect(self._engine.destroy_engine)

    def start_rpc(self):
        if self.msg_server is not None:
            self.msg_server.close()

        self.msg_server = rpc.RPCServerThread(self._engine)
        self.msg_server.register_function(self.trigger_callback, "trigger_callback")
        self.msg_server.register_function(self.signal_disconnect, "signal_disconnect")
        self.msg_server.register_function(self.open_project_locations, "open_project_locations")
        self.msg_server.register_function(self.get_setting, "get_setting")

        self.msg_server.start()

    def destroy_engine(self):
        if self.proxy is not None:
            try:
                self.proxy.call_no_response("destroy_app_proxy")
            except EOFError:
                # it is ok if it is already shut down on the other side
                pass

            self.proxy.close()

        # close down our server thread
        if self.msg_server is not None:
            self.msg_server.close()

    def trigger_callback(self, namespace, command, *args, **kwargs):
        callback = self.__callback_map.get((namespace, command))
        try:
            callback(*args, **kwargs)
        except Exception:
            self._engine.log_error("Error calling %s::%s(%s, %s):\n%s" % (
                namespace, command, args, kwargs, traceback.format_exc()))

    def signal_disconnect(self):
        if self._engine.has_ui:
            from tank.platform.qt import QtGui

            app = QtGui.QApplication.instance()
            self.connected = False

            top_level_windows = app.topLevelWidgets()
            sgtk.platform.current_engine()
            # Bugs in client code (or Toolkit) can cause a leak of a top-level dialog that is already
            # closed. So if any top level dialog is visible, wait for it to close.
            if filter(lambda w: w.isVisible(), top_level_windows):
                print top_level_windows
                print("Disconnected with open windows, setting quit on last window closed.")
                app.setQuitOnLastWindowClosed(True)
            else:
                print("Quitting on disconnect")
                app.quit()
        else:
            # just close down the message thread otherwise
            self._engine.log_debug("Disconnect with no UI.  Shutting down")
            self.msg_server.close()

    def open_project_locations(self):
        """ Open the project locations in an os specific browser window """
        paths = self._engine.context.filesystem_locations

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
                self._engine.log_error("Failed to launch '%s'!" % cmd)

    def get_setting(self, setting_name, default_value=None):
        """ Look up engine setting for current environment """
        return self._engine.get_setting(setting_name, default_value)

    def _initialize_logging(self):
        formatter = logging.Formatter("%(asctime)s [PROJ   %(levelname) -7s] %(name)s - %(message)s")
        self._engine._handler.setFormatter(formatter)

    def log(self, level, msg, *args):
        if self.connected:
            # If we can log through the proxy, only do that to avoid
            # duplicate entries in the log file
            try:
                self.proxy.call_no_response("proxy_log", level, msg, args)
                return
            except Exception:
                # could not log through the proxy, log to the file
                pass

        self._engine._logger.log(level, msg, *args)

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

        self._engine.log_debug("'%s' goes in groups: %s" % (display_name, matches))
        return matches
