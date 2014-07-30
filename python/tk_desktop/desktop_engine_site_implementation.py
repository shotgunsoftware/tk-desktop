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
import collections

from sgtk.errors import TankEngineInitError

from . import rpc
from . import desktop_window


class DesktopEngineSiteImplementation(object):
    def __init__(self, engine):
        self.proxy = None
        self.msg_server = None
        self._engine = engine
        self.app_version = None

        # rules that determine how to collapse commands into buttons
        # each rule is a dictionary with keys for match, button_label, and
        # menu_label
        self._collapse_rules = []

    def destroy_engine(self):
        if self.proxy is not None:
            self.proxy.close()

        # close down our server thread
        if self.msg_server is not None:
            self.msg_server.close()

    def startup_rpc(self):
        if self.msg_server is not None:
            self.msg_server.close()

        self.msg_server = rpc.RPCServerThread(self._engine)
        self.msg_server.register_function(self.engine_startup_error, "engine_startup_error")
        self.msg_server.register_function(self.create_app_proxy, "create_app_proxy")
        self.msg_server.register_function(self.destroy_app_proxy, "destroy_app_proxy")
        self.msg_server.register_function(self.set_groups, "set_groups")
        self.msg_server.register_function(self.set_collapse_rules, "set_collapse_rules")
        self.msg_server.register_function(self.trigger_register_command, "trigger_register_command")
        self.msg_server.register_function(self.proxy_log, "proxy_log")

        self.msg_server.start()

    def engine_startup_error(self, error, tb=None):
        """ Handle an error starting up the engine for the app proxy. """
        trigger_project_config = False
        if isinstance(error, TankEngineInitError):
            # match directly on the error message until something less fragile can be put in place
            if error.message.startswith("Cannot find an engine instance tk-desktop"):
                trigger_project_config = True
            else:
                message = "Error starting engine\n\n%s" % error.message
        else:
            message = "Error\n\n%s" % error.message

        if trigger_project_config:
            # error is that the desktop engine hasn't been setup for the project
            # show the UI to configure it
            self.desktop_window.show_update_project_config()
        else:
            # just show the error in the window
            display_message = "%s\n\nSee the console for more details." % message
            self.desktop_window.project_overlay.show_error_message(display_message)

            # add the traceback if available
            if tb is not None:
                message += "\n\n%s" % tb
            self._engine.log_error(message)

    def create_app_proxy(self, pipe, authkey):
        """ Called when the project engine has setup its RPC server thread """
        if self.proxy is not None:
            self.proxy.close()

        self.proxy = rpc.RPCProxy(pipe, authkey)

    def destroy_app_proxy(self):
        """ App proxy has been destroyed, clean up state. """
        self.desktop_window.clear_app_uis()
        if self.proxy is not None:
            self.proxy.close()
            self.proxy = None

    def disconnect_app_proxy(self):
        """ Disconnect from the app proxy. """
        if self.proxy is not None:
            try:
                self.proxy.call("signal_disconnect")
                self.proxy.close()
            except Exception, e:
                self._engine.log_warning("Error disconnecting from proxy: %s", e)
            finally:
                self.proxy = None

    def set_groups(self, groups, show_recents=True):
        self.desktop_window.set_groups(groups, show_recents)

    def set_collapse_rules(self, collapse_rules):
        self._collapse_rules = collapse_rules

    def trigger_register_command(self, name, properties, groups):
        """ GUI side handler for the add_command call. """
        from tank.platform.qt import QtGui

        self._engine.log_debug("register_command(%s, %s)", name, properties)

        command_type = properties.get("type")
        command_icon = properties.get("icon")
        command_tooltip = properties.get("description")

        icon = None
        if command_icon is not None:
            if os.path.exists(command_icon):
                icon = QtGui.QIcon(command_icon)
            else:
                self._engine.log_error(
                    "Icon for command '%s' not found: '%s'" % (name, command_icon))

        title = properties.get("title", name)

        if command_type == "context_menu":
            # Add the command to the project menu
            action = QtGui.QAction(self.desktop_window)
            if icon is not None:
                action.setIcon(icon)
            if command_tooltip is not None:
                action.setToolTip(command_tooltip)
            action.setText(title)

            def action_triggered():
                # make sure to pass in that we are not expecting a response
                # Especially for the engine restart command, the connection
                # itself gets reset and so there isn't a channel to get a
                # response back.
                self.proxy.call_no_response("trigger_callback", "__commands", name)
            action.triggered.connect(action_triggered)
            self.desktop_window.add_to_project_menu(action)
        else:
            # Default is to add an icon/label for the command

            # figure out what the button should be labeled
            # default is that the button has no menu and is labeled
            # the display name of the command
            menu_name = None
            button_name = title
            for collapse_rule in self._collapse_rules:
                template = DisplayNameTemplate(collapse_rule["match"])
                match = template.match(title)
                if match is not None:
                    self._engine.log_debug("matching %s against %s" % (title, collapse_rule["match"]))
                    if collapse_rule["menu_label"] == "None":
                        menu_name = None
                    else:
                        menu_name = string.Template(collapse_rule["menu_label"]).safe_substitute(match)
                    button_name = string.Template(collapse_rule["button_label"]).safe_substitute(match)
                    break

            self.desktop_window._project_command_model.add_command(
                name, button_name, menu_name, icon, command_tooltip, groups)

    def _handle_button_command_triggered(self, group, name):
        """ Button clicked from a registered command. """
        self.proxy.call("trigger_callback", "__commands", name)

    def run(self, splash=None, version=None):
        """
        Run the engine.

        This method is called from the GUI bootstrap to setup the application
        and to run the Qt event loop.
        """
        self.app_version = version

        # Initialize Qt app
        from tank.platform.qt import QtGui

        app = QtGui.QApplication.instance()
        if app is None:
            app = QtGui.QApplication(sys.argv)

        # update the app icon
        icon = QtGui.QIcon(":tk-desktop/default_systray_icon")
        app.setWindowIcon(icon)

        splash.showMessage("Building UI")

        # setup the global look and feel
        self._engine._initialize_dark_look_and_feel()

        # merge in app specific look and feel
        css_file = os.path.join(self._engine.disk_location, "resources", "desktop_dark.css")
        f = open(css_file)
        css = app.styleSheet() + "\n\n" + f.read()
        f.close()
        app.setStyleSheet(css)

        # initialize System Tray
        self.desktop_window = desktop_window.DesktopWindow()

        # make sure we close down our rpc threads
        app.aboutToQuit.connect(self._engine.destroy_engine)

        # hide the splash if it exists
        if splash is not None:
            splash.finish(self.desktop_window)

        # and run the app
        result = app.exec_()
        return result

    def _initialize_logging(self):
        formatter = logging.Formatter("%(asctime)s [SITE   %(levelname) -7s] %(name)s - %(message)s")
        self._engine._handler.setFormatter(formatter)

    def log(self, level, msg, *args):
        self._engine._logger.log(level, msg, *args)

    def proxy_log(self, level, msg, args):
        self._engine._logger.log(level, "[PROXY] %s" % msg, *args)


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
