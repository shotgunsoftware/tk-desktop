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
        self.site_comm.proxy_created.connect(self._on_proxy_created)

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

    def set_global_debug(self, state):
        """
        Attempts to tell a project subprocess to set the state of
        the global debug logging setting. This will never raise
        an exception, but a warning message will be logged if something
        causes the RPC call to raise.

        :param bool state: The debug to set.
        """
        if self.site_comm.is_connected and "set_global_debug" in self.site_comm.call("list_functions"):
            try:
                self.site_comm.call_no_response("set_global_debug", state)
            except Exception:
                # This really can't be a debug log call, because we might have just
                # toggled debug logging off, in which case the message would not be
                # logged.
                logger.warning(
                    "The RPC call to set_global_debug did not succeed. This is likely "
                    "caused by an older version of the tk-desktop engine being "
                    "used by the project. This issue can be resolved by updating to "
                    "the latest version of tk-desktop using the 'tank updates' command."
                )
        elif self.site_comm.is_connected:
            logger.warning(
                "A connection is active, but the proxy does not support the "
                "set_global_debug RPC function. The debug log state will not "
                "be toggled in the project context as a result."
            )
        else:
            logger.debug(
                "No connection exists to a project subprocess. No debug "
                "toggling will occur via RPC as a result."
            )

    ###########################################################################
    # panel support (displayed as tabs)
    def _run_startup_commands(self):
        """
        Runs the commands that are configured to be executed at startup, through
        the 'run_at_startup' setting in the configuration.

        This gives an opportunity for apps to display panels through the
        execution of a command, which will add a tab to Desktop.
        """
        apps_selector = {"app_instance": "", "name": "Apps"}

        selectors = self._engine.get_setting("run_at_startup", [apps_selector])

        # "Apps" is currently a builtin command, so we take care of it
        # separately.
        # We first figure out what is its index in the selectors, or None if it
        # is not present
        apps_index = (selectors.index(apps_selector)
                      if apps_selector in selectors else None)
        # strip the "Apps" tab from the selectors, as we handle it separately
        if apps_index is not None:
            del selectors[apps_index]

        commands = self._engine.get_matching_commands(selectors)

        # add the "Apps" tab back at the appropriate position
        if apps_index is not None:
            # we can't blindly use the previous index, since the following
            # special cases can occur:
            # - commands were not found (a selector with no matching command)
            # - multiple commands were found (a wildcard selector found many)
            #
            # Thus, we go through the matched commands until we have run through
            # all the commands that should occur before our "Apps" tab (based on
            # its location in the selectors).
            # In other words, we find where the "Apps" tab belongs in the
            # matched commands.
            apps_command_index = 0
            # skip the commands from the selectors preceding "Apps"
            for index in xrange(apps_index):
                selector = selectors[index]
                # skip all the commands that fit the current selector
                # insert as the last command in the worst case
                while apps_command_index < len(commands):
                    app, name, _ = commands[apps_command_index]

                    # only keep skipping commands if the current selector
                    # matches the current command
                    if (
                        selector["app_instance"] != app or
                        (selector["name"] != "" and selector["name"] != name)
                    ):
                        break

                    apps_command_index += 1

            # we now have the index where the apps command should be and we can
            # add a fake command callback that will register the "Apps" tab.
            apps_tab_callback = self.desktop_window._register_apps_tab
            commands.insert(apps_command_index, ("", "", apps_tab_callback))

        # Execute the actual commands.
        # For example, a command could be displaying a panel in order to
        # display it as a tab in the desktop.
        for (_, _, command_callback) in commands:
            command_callback()

    def show_panel(self, panel_id, title, bundle, widget_class,
                   *args, **kwargs):
        """
        Adds an app widget as a tab in the desktop UI. The tab is placed in the
        next available tab slot in the desktop, going from left to right.

        :param panel_id:     Unique identifier for the panel, as obtained by
                             register_panel().
        :param title:        The title of the panel, which is the title
                             displayed for the tab in the UI.
        :param bundle:       The app, engine or framework object that is
                             associated with this window.
        :param widget_class: The class of the UI to be constructed. This must
                             derive from QWidget.

        Additional parameters specified will be passed through to the
        widget_class constructor.
        """
        self._engine.log_debug("Registering panel \"%s\" (id %s) as a tab." %
                               (title, panel_id))
        # create widget
        widget = widget_class(*args, **kwargs)
        # apply std toolkit stylings
        # note: since this class is an engine but doesn't derive from
        #       engine, we have to call the protected method via bundle.engine
        #       rather than using self._apply_external_stylesheet()
        bundle.engine._apply_external_stylesheet(bundle, widget)
        # register UI tab
        self.desktop_window.register_tab(title, widget)
        return widget

    def startup_rpc(self):
        self.site_comm.start_server()
        self.site_comm.register_function(self.bootstrap_progress_callback, "bootstrap_progress")
        self.site_comm.register_function(self.engine_startup_error, "engine_startup_error")
        self.site_comm.register_function(self.set_groups, "set_groups")
        self.site_comm.register_function(self.set_collapse_rules, "set_collapse_rules")
        self.site_comm.register_function(self.trigger_register_command, "trigger_register_command")
        self.site_comm.register_function(self.project_commands_finished, "project_commands_finished")

    def engine_startup_error(self, error, tb=None):
        """
        Handle an error starting up the engine for the app proxy.

        :param error: Exception object that was raised during bootstrap.
        :param tb: Traceback of the exception raised during bootstrap.
        """
        self.desktop_window.engine_startup_error(error, tb)

    def bootstrap_progress_callback(self, value, msg):
        """
        Called by the bootstrap to report progress.

        :param value: Value between 0 and 1 indicating how far along we are into
            bootstrapping.
        :param msg: Message to print.
        """
        self.desktop_window.bootstrap_progress_callback(value, msg)

    def _on_proxy_closing(self):
        """
        Invoked when background process is closing down.
        """
        # Clear the UI, we can't launch anything anymore!
        self.desktop_window.clear_app_uis()

    def _on_proxy_created(self):
        """
        Invoked when background process has created proxy
        """
        # Clears the project menu so the previous engine's actions
        # are removed before adding new one
        self.desktop_window.clear_actions_from_project_menu()

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
        css_file = os.path.join(self._engine.disk_location, "style.qss")
        with open(css_file) as f:
            css = app.styleSheet() + "\n\n" + f.read()
        app.setStyleSheet(css)

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
        from .console import Console

        # When we instantiate the console, it also instantiates the logging handler that will
        # route messages from the logger to the console. We're instantiating it here, right after
        # Qt has been fully initialized, so that we get more entries in that dialog.
        console = Console()

        self.app_version = version

        # Startup version will not be set if we have an old installer invoking
        # this engine.
        self.startup_version = kwargs.get("startup_version")
        self.startup_descriptor = kwargs.get("startup_descriptor")
        server = kwargs.get("server")

        try:
            # Log usage statistics about the Shotgun Desktop executable and the desktop startup.
            #
            # First we update `host_info` property so subsequent metrics can benefit
            # having the updated information. A special case is made for for Desktop
            # as we do want both versiond but don't want to create another metric field.
            # We are then combining both versions into single version string.
            self._engine._host_info["version"] = "%s / %s" % (self.app_version, self.startup_version)

            # Actually log the metric
            self._engine.log_metric("Launched Software")

        except Exception:
            logger.exception("Unexpected error logging a metric")
            # DO NOT raise exception. It's reasonnable to log an error about it but
            # we don't want to break normal execution for metric related logging.

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

        # initialize System Tray
        self.desktop_window = desktop_window.DesktopWindow(console)

        # We need for the dialog to exist for messages to get to the UI console.
        if kwargs.get("server") is not None:
            logger.warning(
                "You are running an older version of the Shotgun Desktop which is not fully compatible "
                "with the Shotgun Integrations. Please install the latest version."
            )

        # run the commands that are configured to be executed at startup
        self._run_startup_commands()

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
