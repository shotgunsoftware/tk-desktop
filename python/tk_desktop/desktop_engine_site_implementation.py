# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from __future__ import with_statement
import os
import re
import sys
import string
import collections

from sgtk.errors import TankEngineInitError

from distutils.version import LooseVersion
import sgtk
from tank_vendor.shotgun_authentication import ShotgunAuthenticator, DefaultsManager

from sgtk import LogManager

from .site_communication import SiteCommunication

shotgun_globals = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_globals")
task_manager = sgtk.platform.import_framework("tk-framework-shotgunutils", "task_manager")

logger = LogManager.get_logger(__name__)


class DesktopEngineSiteImplementation(object):
    def __init__(self, engine):

        self.site_comm = SiteCommunication(engine)
        self.site_comm.proxy_closing.connect(self._on_proxy_closing)

        self._engine = engine
        self.app_version = None

        # rules that determine how to collapse commands into buttons
        # each rule is a dictionary with keys for match, button_label, and
        # menu_label
        self._collapse_rules = []

        self._task_manager = task_manager.BackgroundTaskManager(parent=None)
        shotgun_globals.register_bg_task_manager(self._task_manager)

    def destroy_engine(self):
        shotgun_globals.unregister_bg_task_manager(self._task_manager)
        self.site_comm.shut_down()

    def startup_rpc(self):
        self.site_comm.start_server()
        self.site_comm.register_function(self.engine_startup_error, "engine_startup_error")
        self.site_comm.register_function(self.set_groups, "set_groups")
        self.site_comm.register_function(self.set_collapse_rules, "set_collapse_rules")
        self.site_comm.register_function(self.trigger_register_command, "trigger_register_command")
        self.site_comm.register_function(self.project_commands_finished, "project_commands_finished")

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
            logger.error(message)

    def _on_proxy_closing(self):
        """
        Invoked when background process is closing down.
        """
        # Clear the UI, we can't launch anything anymore!
        self.desktop_window.clear_app_uis()

    def set_groups(self, groups, show_recents=True):
        self.desktop_window.set_groups(groups, show_recents)

    def set_collapse_rules(self, collapse_rules):
        self._collapse_rules = collapse_rules

    def trigger_register_command(self, name, properties, groups):
        """ GUI side handler for the add_command call. """
        from tank.platform.qt import QtGui

        logger.debug("register_command(%s, %s)", name, properties)

        command_type = properties.get("type")
        command_icon = properties.get("icon")
        command_tooltip = properties.get("description")
        command_group = properties.get("group")
        command_is_menu_default = properties.get("group_default") or False

        icon = None
        if command_icon is not None:
            # Only register an icon for the command if it exists.
            if os.path.exists(command_icon):
                icon = QtGui.QIcon(command_icon)
            else:
                logger.error(
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
                self.refresh_user_credentials()
                self.site_comm.call_no_response("trigger_callback", "__commands", name)
            action.triggered.connect(action_triggered)
            self.desktop_window.add_to_project_menu(action)
        else:
            # Default is to add an icon/label for the command

            # figure out what the button should be labeled
            # default is that the button has no menu and is labeled
            # the display name of the command
            menu_name = None
            button_name = title
            found_collapse_match = False

            # First check for collapse rules specified for this title in the desktop
            # configuration. These take precedence over the group property.
            for collapse_rule in self._collapse_rules:
                template = DisplayNameTemplate(collapse_rule["match"])
                match = template.match(title)
                if match is not None:
                    logger.debug("matching %s against %s" % (title, collapse_rule["match"]))
                    if collapse_rule["menu_label"] == "None":
                        menu_name = None
                    else:
                        menu_name = string.Template(collapse_rule["menu_label"]).safe_substitute(match)
                    button_name = string.Template(collapse_rule["button_label"]).safe_substitute(match)
                    found_collapse_match = True
                    break

            # If no collapse rules were found for this title, and the group property is
            # not empty, treat the specified group as if it were a collapse rule.
            if not found_collapse_match and command_group:
                button_name = command_group
                menu_name = title

            self.desktop_window.add_project_command(
                name,
                button_name,
                menu_name,
                icon,
                command_tooltip,
                groups,
                command_is_menu_default
            )

    def project_commands_finished(self):
        """
        Invoked when all commands found for a project have been registered.
        """
        # Let the desktop window know all commands for the project have been registered.
        self.desktop_window.on_project_commands_finished()

    def _handle_button_command_triggered(self, group, name):
        """ Button clicked from a registered command. """
        self.refresh_user_credentials()
        self.site_comm.call_no_response("trigger_callback", "__commands", name)

    # Leave app_version as is for backwards compatibility.
    def run(self, splash, version, **kwargs):
        """
        Run the engine.

        This method is called from the GUI bootstrap to setup the application
        and to run the Qt event loop.

        :param splash: Splash screen widget we can display messages on. Can be ``None``
        :param version: Version of the Shotgun Desktop installer code.
        :param startup_version: Version of the Desktop Startup code. Can be omitted.
        :param startup_descriptor: Descriptor of the Desktop Startup code. Can be omitted.
        """
        self.app_version = version

        # Startup version will not be set if we have an old installer invoking
        # this engine.
        self.startup_version = kwargs.get("startup_version")
        self.startup_descriptor = kwargs.get("startup_descriptor")
        server = kwargs.get("server")

        # Log usage statistics about the Shotgun Desktop executable and the desktop startup.
        sgtk.util.log_user_attribute_metric("tk-framework-desktopstartup", self.startup_version)
        sgtk.util.log_user_attribute_metric("Shotgun Desktop version", self.app_version)
        # If a server is passed down from the desktop startup, it means we won't be using the engine-based
        # websocket server.
        sgtk.util.log_user_attribute_metric("Engine-Websockets", "no" if server else "yes")

        if self.uses_legacy_authentication():
            self._migrate_credentials()

        # We need to initialize current login
        # We know for sure there is a default user, since either the migration was done
        # or we logged in as an actual user with the new installer.
        human_user = ShotgunAuthenticator(
            # We don't want to get the script user, but the human user, so tell the
            # CoreDefaultsManager manager that we are not interested in the script user. Do not use
            # the regular shotgun_authentication.DefaultsManager to get this user because it will
            # not know about proxy information.
            sgtk.util.CoreDefaultsManager(mask_script_user=True)
        ).get_default_user()
        # Cache the user so we can refresh the credentials before launching a background process
        self._user = human_user
        # Retrieve the current logged in user information. This will be used when creating
        # event log entries.
        self._current_login = self._engine.sgtk.shotgun.find_one(
            "HumanUser",
            [["login", "is", human_user.login]],
            ["id", "login"]
        )

        # Initialize Qt app
        from tank.platform.qt import QtGui

        app = QtGui.QApplication.instance()
        if app is None:
            app = QtGui.QApplication(sys.argv)

        # update the app icon
        icon = QtGui.QIcon(":tk-desktop/default_systray_icon")
        app.setWindowIcon(icon)

        if splash:
            splash.set_message("Building UI")

        # setup the global look and feel
        self._engine._initialize_dark_look_and_feel()

        # load custom font
        QtGui.QFontDatabase.addApplicationFont(":/tk-desktop/fonts/OpenSans-Bold.ttf")
        QtGui.QFontDatabase.addApplicationFont(":/tk-desktop/fonts/OpenSans-Regular.ttf")
        QtGui.QFontDatabase.addApplicationFont(":/tk-desktop/fonts/OpenSans-CondLight.ttf")
        QtGui.QFontDatabase.addApplicationFont(":/tk-desktop/fonts/OpenSans-Light.ttf")

        # merge in app specific look and feel
        css_file = os.path.join(self._engine.disk_location, "resources", "desktop_dark.css")
        f = open(css_file)
        css = app.styleSheet() + "\n\n" + f.read()
        f.close()
        app.setStyleSheet(css)

        # If server is passed down to this method, it means we are running an older version of the
        # desktop startup code, which runs its own browser integration.
        #
        # Sadly, we can't tear down the previous server and restart it. Attempting to tear_down() and
        # instantiate a new server will raise an error.ReactorNotRestartable exception. So we'll start
        # our websocket integration only if there is no server running from the desktop startup.
        # Note that the server argument is set regardless of whether the server launched or crashed,
        # so we have to actually get its value instead of merely checking for existence.
        if server is None:
            # Initialize all of this after the style-sheet has been applied so any prompt are also
            # styled after the Shotgun Desktop's visual-style.
            if splash:
                splash.set_message("Initializing browser integration.")
            try:
                desktop_server_framework = sgtk.platform.get_framework("tk-framework-desktopserver")
                desktop_server_framework.launch_desktop_server(
                    self._user.host, self._current_login["id"], parent=splash
                )
            except Exception:
                logger.exception("Unexpected error while trying to launch the browser integration:")
            else:
                logger.debug("Browser integration was launched successfully.")

        # hide the splash if it exists
        if splash is not None:
            splash.hide()

        # desktop_window needs to import shotgun_authentication globally. However, doing so
        # can cause a crash when running Shotgun Desktop installer 1.02 code. We used to
        # not restart Desktop when upgrading the core, which caused the older version of core
        # to be kept in memory and the newer core to not be used until the app was reloaded.
        #
        # Since pre 0.16 cores didn't have a shotgun_authentication module, we
        # would have crashed if this had been imported at init time. Note that earlier
        # in this method we forcefully restarted the application if we noticed
        # that the core was upgraded without restarting. Which means that if we
        # end up here, it's now because we're in a good state.
        from . import desktop_window

        # initialize System Tray
        self.desktop_window = desktop_window.DesktopWindow()

        # We need for the dialog to exist for messages to get to the UI console.
        if kwargs.get("server") is not None:
            logger.warning(
                "You are running an older version of the Shotgun Desktop which is not fully compatible "
                "with the Shotgun Integrations. Please install the latest version."

            )

        # make sure we close down our rpc threads
        app.aboutToQuit.connect(self._engine.destroy_engine)

        # and run the app
        result = app.exec_()
        return result

    def uses_legacy_authentication(self):
        """
        Returns if the Shotgun Desktop installed code uses the tk-framework-login for
        logging in.

        :returns: True the bootstrap logic is older than 1.1.0, False otherwise.
        """
        return LooseVersion(self.app_version) < LooseVersion("1.1.0")

    def create_legacy_login_instance(self):
        """
        Creates an instance of tk-framework-login.ShotgunLogin.

        Before we introduced Shotgun Authentication in Core 0.16.0, we used
        tk-framework-login to authenticate in the Shotgun Desktop's installer
        code. Once we've detected using uses_legacy_authentication that we are
        using tk-framework-login, create_legacy_login_instance creates an
        instance of that class in order to access the credentials.

        In the Shotgun Desktop installer v1.1.0 code and higher, this
        ShotgunLogin class is no more.

        :raises ImportError: Thrown if the module is not available.

        :returns: A tk-framework-login.ShotgunLogin instance.
        """
        try:
            from python import ShotgunLogin
        except ImportError:
            logger.exception("Could not import tk-framework-login")
            raise
        else:
            return ShotgunLogin.get_instance_for_namespace("tk-desktop")

    def _migrate_credentials(self):
        """
        Migrates the credentials from tk-framework-login to
        shotgun_authentication.
        """
        sl = self.create_legacy_login_instance()
        site, login, _ = sl._get_saved_values()
        # Call get_connection, since it will reprompt for the password if
        # for some reason it is expired now.
        connection = sl.get_connection()

        # Next set the current host and user in the framework.
        dm = DefaultsManager()
        dm.set_host(site)
        dm.set_login(login)

        # If we have a version of the framework that supports password mangling with the session token,
        # try to pick the session token from the connection.
        if hasattr(sl, "mangle_password") and connection.config.session_token is not None:
            # Extract the credentials from the old Shotgun instance and create a
            # ShotgunUser with them. This will cache the session token as well.
            ShotgunAuthenticator().create_session_user(
                login=login,
                session_token=connection.config.session_token,
                # Ugly, but this is the only way available to get at the
                # raw http_proxy string.
                http_proxy=sl._http_proxy
            )
        else:
            ShotgunAuthenticator().create_session_user(
                login=connection.config.user_login,
                password=connection.config.user_password,
                host=connection.base_url,
                # Ugly, but this is the only way available to get at the
                # raw http_proxy string.
                http_proxy=sl._http_proxy
            )

    def get_current_login(self):
        """
        Returns the user's id and login.

        :returns: Dictionary with keys id and login.
        """
        return self._current_login

    def get_current_user(self):
        """
        Returns the current login based user.

        :returns: A ShotgunUser instance.
        """
        return self._user

    def refresh_user_credentials(self):
        """
        Refreshes the human user credentials, potentially prompting for a password, only is
        the desktop project engine is using login based authentication.
        """
        self._user.refresh_credentials()


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
