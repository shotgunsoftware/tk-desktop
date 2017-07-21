# -*- coding: utf-8 -*-
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
import tempfile
import subprocess
import cPickle as pickle
import pprint
import itertools
import urlparse
import inspect
from collections import OrderedDict

from tank.platform.qt import QtCore, QtGui
from sgtk.platform import constants

import sgtk
from sgtk.util import shotgun
from sgtk.bootstrap import ToolkitManager

from tank_vendor import shotgun_authentication as sg_auth
from sgtk import TankInvalidInterpreterLocationError, TankFileDoesNotExistError
from sgtk.platform import get_logger

from .ui import resources_rc # noqa
from .ui import desktop_window

from .console import Console
from .console import ConsoleLogHandler
from .systray import SystrayWindow
from .about_screen import AboutScreen
from .no_apps_installed_overlay import NoAppsInstalledOverlay
from .setup_project import SetupProject
from .setup_new_os import SetupNewOS
from .project_model import SgProjectModel
from .project_model import SgProjectModelProxy
from .project_delegate import SgProjectDelegate
from .update_project_config import UpdateProjectConfig
from .loading_project_widget import LoadingProjectWidget
from .browser_integration_user_switch_dialog import BrowserIntegrationUserSwitchDialog
from .banner_widget import BannerWidget

from .project_commands_model import ProjectCommandModel
from .project_commands_model import ProjectCommandProxyModel
from .project_commands_widget import ProjectCommandDelegate
from . import rpc

from .notifications import NotificationsManager, FirstLaunchNotification

try:
    from .extensions import osutils
except Exception:
    osutils = None

# import our frameworks
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
overlay_widget = sgtk.platform.import_framework("tk-framework-qtwidgets", "overlay_widget")
settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")
desktop_server_framework = sgtk.platform.get_framework("tk-framework-desktopserver")

ShotgunModel = shotgun_model.ShotgunModel

log = get_logger(__name__)


class DesktopWindow(SystrayWindow):
    """ Dockable window for the Shotgun system tray """

    ORGANIZATION = "Shotgun Software"
    APPLICATION = "tk-desktop"
    _BOOTSTRAP_END_RATIO = 0.9
    _LAUNCHING_PYTHON_RATIO = 0.95
    _CHROME_SUPPORT_URL = "https://support.shotgunsoftware.com/hc/en-us/articles/114094536273"
    _FIREFOX_SUPPORT_URL = "https://support.shotgunsoftware.com/hc/en-us/articles/115000054954"

    def __init__(self, parent=None):
        SystrayWindow.__init__(self, parent)

        # initialize member variables
        self.current_project = None
        self.__activation_hotkey = None
        self.__pipeline_configuration_separator = None
        self._settings_manager = settings.UserSettings(sgtk.platform.current_bundle())

        self._sync_thread = None

        engine = sgtk.platform.current_engine()

        # setup the window
        self.ui = desktop_window.Ui_DesktopWindow()
        self.ui.setupUi(self)
        self.project_overlay = LoadingProjectWidget(self.ui.project_commands)
        self.install_apps_widget = NoAppsInstalledOverlay(self.ui.project_commands)
        self.setup_project_widget = SetupProject(self.ui.project_commands)
        self.setup_project_widget.setup_finished.connect(self._on_setup_finished)
        self.update_project_config_widget = UpdateProjectConfig(self.ui.project_commands)
        self.update_project_config_widget.update_finished.connect(self._on_update_finished)
        self.setup_new_os_widget = SetupNewOS(self.ui.project_commands)

        self._current_pipeline_descriptor = None

        self.ui.banners.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        self._update_banners()

        # setup systray behavior
        self.set_content_layout(self.ui.center)
        self.set_drag_widgets([self.ui.header, self.ui.footer])

        self.systray_state_changed.connect(self.handle_systray_state_changed)
        QtGui.QApplication.instance().setQuitOnLastWindowClosed(False)

        # Setup header buttons
        engine = sgtk.platform.current_engine()
        connection = engine.get_current_user().create_sg_connection()

        # Setup the console
        self.__console = Console()
        self.__console_handler = ConsoleLogHandler(self.__console)
        sgtk.LogManager().initialize_custom_handler(self.__console_handler)

        # User menu
        ###########################
        user = engine.get_current_login()
        current_user = connection.find_one(
            "HumanUser", [["id", "is", user["id"]]],
            ["image", "name"])
        self._current_user_id = user["id"]
        thumbnail_url = current_user.get("image")
        if thumbnail_url is not None:
            (_, thumbnail_file) = tempfile.mkstemp(suffix=".jpg")
            try:
                shotgun.download_url(connection, thumbnail_url, thumbnail_file)
                pixmap = QtGui.QPixmap(thumbnail_file)
                self.ui.user_button.setIcon(QtGui.QIcon(pixmap))
            except Exception:
                # if it fails for any reason, that's alright
                pass
            finally:
                try:
                    os.remove(thumbnail_file)
                except Exception:
                    pass

        # populate user menu
        self.user_menu = QtGui.QMenu(self)
        name_action = self.user_menu.addAction(current_user["name"])
        url_action = self.user_menu.addAction(connection.base_url.split("://")[1])
        self.user_menu.addSeparator()
        advanced_menu = self.user_menu.addMenu("Advanced")
        self.user_menu.addAction(self.ui.actionPin_to_Menu)
        self.user_menu.addAction(self.ui.actionKeep_on_Top)
        self.user_menu.addAction(self.ui.actionRefresh_Projects)
        self.user_menu.addAction(self.ui.actionAdvanced_Project_Setup)
        about_action = self.user_menu.addAction("About...")
        self.user_menu.addAction(self.ui.actionHelp)
        self.user_menu.addSeparator()
        self.user_menu.addAction(self.ui.actionSign_Out)
        self.user_menu.addAction(self.ui.actionQuit)

        advanced_menu.addAction(self.ui.actionShow_Console)

        if desktop_server_framework.can_run_server():
            advanced_menu.addAction(self.ui.actionRegenerate_Certificates)

        # Initially hide the Advanced project setup... menu item. This
        # menu item will only be displayed for projects that do not have
        # any pipeline configurations registered in Shotgun.
        self.ui.actionAdvanced_Project_Setup.setVisible(False)

        name_action.triggered.connect(self.open_site_in_browser)
        url_action.triggered.connect(self.open_site_in_browser)
        about_action.triggered.connect(self.handle_about)

        QtGui.QApplication.instance().aboutToQuit.connect(self.handle_quit_action)

        self.ui.actionPin_to_Menu.triggered.connect(self.toggle_pinned)
        self.ui.actionKeep_on_Top.triggered.connect(self.toggle_keep_on_top)
        self.ui.actionShow_Console.triggered.connect(self.__console.show_and_raise)
        self.ui.actionAdvanced_Project_Setup.triggered.connect(self.handle_advanced_project_setup_action)
        self.ui.actionRefresh_Projects.triggered.connect(self.handle_project_refresh_action)
        self.ui.actionSign_Out.triggered.connect(self.sign_out)
        self.ui.actionQuit.triggered.connect(self.handle_quit_action)
        self.ui.actionRegenerate_Certificates.triggered.connect(self.handle_regen_certs)
        self.ui.actionHelp.triggered.connect(self.handle_help)

        self.ui.user_button.setMenu(self.user_menu)

        # Initialize the model to track project commands
        self._project_command_count = 0
        self._project_command_model = ProjectCommandModel(self)
        self._project_command_proxy = ProjectCommandProxyModel(self)
        self._project_command_proxy.setSourceModel(self._project_command_model)
        self._project_command_proxy.sort(0)
        self.ui.project_commands.setModel(self._project_command_proxy)

        # limit how many recent commands are shown
        self._project_command_proxy.set_recents_limit(6)

        self._project_command_delegate = ProjectCommandDelegate(self.ui.project_commands)
        self.ui.project_commands.setItemDelegate(self._project_command_delegate)
        self.ui.project_commands.expanded_changed.connect(self.handle_project_command_expanded_changed)

        # fix for floating delegate bug
        # see discussion at https://stackoverflow.com/questions/15331256
        self.ui.project_commands.verticalScrollBar().valueChanged.connect(
            self.ui.project_commands.updateEditorGeometries)

        self._project_command_model.command_triggered.connect(engine._handle_button_command_triggered)

        # load and initialize cached projects
        self._project_model = SgProjectModel(self, self.ui.projects)
        self._project_proxy = SgProjectModelProxy(self)

        # hook up sorting/filtering GUI
        self._project_proxy.setSourceModel(self._project_model)
        self._project_proxy.sort(0)
        self.ui.projects.setModel(self._project_proxy)

        # tell our project view to use a custom delegate to produce widgets
        self._project_delegate = \
            SgProjectDelegate(self.ui.projects, QtCore.QSize(130, 150))
        self.ui.projects.setItemDelegate(self._project_delegate)

        # handle project selection change
        self._project_selection_model = self.ui.projects.selectionModel()
        self._project_selection_model.selectionChanged.connect(self._on_project_selection)

        # handle project data updated
        self._project_model.data_refreshed.connect(self._handle_project_data_changed)

        self.ui.actionProject_Filesystem_Folder.triggered.connect(
            self.on_project_filesystem_folder_triggered)

        # setup project search
        self._search_x_icon = QtGui.QIcon(":/tk-desktop/icon_inbox_clear.png")
        self._search_magnifier_icon = QtGui.QIcon(":/tk-desktop/search_transparent.png")
        self.ui.search_button.clicked.connect(self.search_button_clicked)
        self.ui.search_text.textChanged.connect(self.search_text_changed)
        self.search_button_clicked()

        self.project_carat_up = QtGui.QIcon(":tk-desktop/up_carat.png")
        self.project_carat_down = QtGui.QIcon(":tk-desktop/down_carat.png")
        self.down_arrow = QtGui.QIcon(":tk-desktop/down_arrow.png")
        self.right_arrow = QtGui.QIcon(":tk-desktop/right_arrow.png")

        self.ui.project_arrow.clicked.connect(self._on_back_to_projects_clicked)

        self.clear_app_uis()

        self.ui.shotgun_button.clicked.connect(self.open_site_in_browser)
        self.ui.shotgun_button.setToolTip("Open Shotgun in browser.\n%s" % connection.base_url)

        self._project_model.thumbnail_updated.connect(self.handle_project_thumbnail_updated)

        desktop_server_framework.add_different_user_requested_callback(self._on_different_user)

        # Set of sites that are being ignored when browser integration requests happen. This set is not
        # persisted when the desktop is closed.
        self._ignored_sites = set()
        # Flag indicating if we are currently handling a switch user request from the browser integration.
        self._is_handling_switch_request = False

        # Do not put anything after this line, this can kick-off a Python process launch, which should
        # be done only when the dialog is fully initialized.
        self._load_settings()

    def handle_help(self):
        """
        Jumps to the help page of the Shotgun Desktop.
        """
        QtGui.QDesktopServices.openUrl(
            FirstLaunchNotification.SHOTGUN_DESKTOP_SUPPORT_PAGE_URL
        )

    def _update_banners(self):
        """
        Displays the notifications retrieved from the ``NotificationsManager``.
        """
        engine = sgtk.platform.current_engine()
        self._notifs_mgr = NotificationsManager(
            self._settings_manager,
            engine.sgtk.configuration_descriptor,
            self._current_pipeline_descriptor,
            engine
        )

        # Remove all items from the layout
        banner_layout = self.ui.banners.layout()

        # Find all the current banners and their unique identifiers.
        current_banners = {
            banner_layout.itemAt(i).widget().unique_id for i in range(banner_layout.count())
        }

        notifs = self._notifs_mgr.get_notifications()
        for notif in notifs:
            # If a banner is not already displayed, we'll add it.
            if notif.unique_id not in current_banners:
                banner = BannerWidget(self._notifs_mgr, notif, parent=self)
                banner.dismissed.connect(self._banner_dismissed)
                banner_layout.addWidget(banner)

    def _banner_dismissed(self, banner):
        """
        Removes the banner from the layout once it is dismissed.
        """
        self.ui.banners.layout().removeWidget(banner)

    def _load_settings(self):
        # last window position
        pos = self._settings_manager.retrieve("pos", QtCore.QPoint(200, 200), self._settings_manager.SCOPE_SITE)
        self.move(pos)
        # Force update so the project selection happens if the window is shown by default
        QtGui.QApplication.processEvents()

        # settings that apply across any instance (after site specific, so pinned can reset pos)
        self.set_on_top(self._settings_manager.retrieve("on_top", False))

        # always start pinned and hidden
        self.state = self._settings_manager.retrieve("dialog_pinned", self.STATE_PINNED)

        # Update the project at the very end so the Python process is kicked off when everything
        # is initialized.
        project_id = self._settings_manager.retrieve("project_id", None, self._settings_manager.SCOPE_SITE)
        self.__set_project_from_id(project_id)

    def _save_setting(self, key, value, site_specific):
        if site_specific:
            self._settings_manager.store(key, value, self._settings_manager.SCOPE_SITE)
        else:
            self._settings_manager.store(key, value)

    def _load_setting(self, key, default_value, site_specific):
        if site_specific:
            ret = self._settings_manager.retrieve(key, default_value, self._settings_manager.SCOPE_SITE)
        else:
            ret = self._settings_manager.retrieve(key, default_value)

        return ret

    def _push_dll_state(self):
        """
        Push current Dll Directory
        """
        if sys.platform == "win32":
            try:
                import win32api

                # GetDLLDirectory throws an exception if none was set
                try:
                    self._previous_dll_directory = win32api.GetDllDirectory(None)
                except StandardError:
                    self._previous_dll_directory = None

                win32api.SetDllDirectory(None)
            except StandardError:
                log.warning("Could not push DllDirectory under Windows.")

    def _pop_dll_state(self):
        """
        Pop the previously pushed DLL Directory
        """
        if sys.platform == "win32":
            try:
                import win32api
                win32api.SetDllDirectory(self._previous_dll_directory)
            except StandardError:
                log.warning("Could not restore DllDirectory under Windows.")

    def register_tab(self, tab_name, tab_widget):
        """
        Register a tab to add to the UI

        :param tab_name:   Name displayed on the tab button.
        :param tab_widget: Widget to display for the tab.
        """
        # setup the header button for the tab
        tab_button = QtGui.QPushButton(self.ui.header)

        # button behaviour/styling
        tab_button.setMouseTracking(True)
        tab_button.setFocusPolicy(QtCore.Qt.NoFocus)
        tab_button.setFlat(True)
        tab_button.setProperty("active", False)

        # tab-specific values
        tab_button.setText(tab_name)

        # setup the tab widget
        tab_widget.setParent(self)

        # define the event handler when the user changes tab
        def on_tab_selected():
            """
            Event fired when a tab is selected by the user
            """
            # update the state of tab buttons
            for i in xrange(self.ui.tabs.count()):
                button = self.ui.tabs.itemAt(i).widget()
                button.setProperty("active", button == tab_button)
                # apply style update
                button.style().unpolish(button)
                button.style().polish(button)

            # display the new tab content
            self.ui.tab_view.setCurrentWidget(tab_widget)

        # link the button to the page widget
        tab_button.toggled.connect(on_tab_selected)
        tab_button.clicked.connect(on_tab_selected)

        # add the tab components to the ui
        self.ui.tabs.addWidget(tab_button)
        self.ui.tab_view.addWidget(tab_widget)

        # select tab if this is the first one
        if self.ui.tabs.count() == 1:
            on_tab_selected()

    def _register_apps_tab(self):
        """
        Registers the "Apps" tab, which allows users to launch toolkit apps.
        This should eventually be moved to an app on its own.
        """
        self.register_tab("Apps", self.ui.apps_tab)

    ########################################################################################
    # Event handlers and slots
    def contextMenuEvent(self, event):
        self.user_menu.exec_(event.globalPos())

    def _show_rich_message_box(self, icon, title, message, buttons=[]):
        """
        Shows a QMessageBox that supports HTML formatting.

        :param icon: Icon to use.
        :type icon: ``QtGui.QMessageBox.Icon``
        :param str title: Title of the dialog.
        :param str message: Message to display.
        :param list buttons: List of `QtGui.QMessageBox.StandardButton` to display.

        :returns: `QtGui.QMessageBox.StandardButton` value associated with the button
            that was pressed.
        """
        message_box = QtGui.QMessageBox(self)
        message_box.setIcon(icon)
        message_box.setTextFormat(QtCore.Qt.RichText)
        message_box.setWindowTitle(title)
        message_box.setText(message)
        for button in buttons:
            message_box.addButton(button)
        return message_box.exec_()

    def handle_regen_certs(self):
        """
        Regenerates the certificates if the user is certain and restarts the Shotgun Desktop on
        demand.
        """
        # Need to create the message box by hand to have rich text format, hence
        # clickable Urls.

        # Deactivate the auto-hide behaviour of the desktop in pinned mode when it loses focus.
        # since we're about to be prompted by the OS, which will make our app lose focus and
        # hide our dialogs.
        with self.deactivate_auto_hide():
            choice = self._show_rich_message_box(
                QtGui.QMessageBox.Information,
                "Shotgun browser integration",
                "Regenerating the Shotgun Desktop's browser integration certificates should "
                "only be done if you have issues with the browser integration.<br/>"
                "<br/>"
                "If you are unsure how to proceed, we recommend you visit our support page "
                "to troubleshoot connections with <a href='%s'>Chrome</a> or "
                "<a href='%s'>Firefox</a>.<br/>"
                "<br/>"
                "Would you like to continue?" % (
                    self._CHROME_SUPPORT_URL,
                    self._FIREFOX_SUPPORT_URL
                ),
                [QtGui.QMessageBox.Yes, QtGui.QMessageBox.No]
            )

            if choice != QtGui.QMessageBox.Yes:
                return

            try:
                desktop_server_framework.regenerate_certificates(self)
            except Exception:
                log.exception("Unexpected error while regenerating certificates:")
                self._show_rich_message_box(
                    QtGui.QMessageBox.Critical,
                    "Shotgun browser integration",
                    "It appears there are an issue while regenerating the certificates."
                    "\n"
                    "Please contact <a href='{0}'>our support team</a> "
                    "if you need assistance resolving this issue. Make sure to zip the logs folder "
                    "at <a href='file://{1}'>{1}</a> and send it to us.".format(
                        "mailto:support@shotgunsoftware.com",
                        sgtk.LogManager().log_folder
                    )
                )
            else:
                choice = QtGui.QMessageBox.question(
                    self,
                    "Shotgun browser integration",
                    "The Shotgun Desktop needs to restart for the certificate changes "
                    "to take effect.\n"
                    "\n"
                    "Would you like to restart?",
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
                )
                if choice == QtGui.QMessageBox.Yes:
                    self._restart_desktop()

    def handle_project_command_expanded_changed(self, group_key, expanded):
        expanded_state = self._project_command_model.get_expanded_state()
        key = "project_expanded_state.%d" % self.current_project["id"]
        self._save_setting(key, expanded_state, site_specific=True)

    def handle_project_thumbnail_updated(self, item):
        project = item.data(ShotgunModel.SG_DATA_ROLE)
        if self.current_project is None or project["id"] != self.current_project["id"]:
            # nothing needs updating
            return

        self.ui.project_icon.setPixmap(self.__get_icon_pixmap(item.icon(), self.ui.project_icon.size()))

    def handle_systray_state_changed(self, state):
        if state == self.STATE_PINNED:
            self.ui.actionPin_to_Menu.setText("Undock from Menu")
        elif state == self.STATE_WINDOWED:
            self.ui.actionPin_to_Menu.setText("Pin to Menu")
        self._settings_manager.store("dialog_pinned", self.state)

    def handle_quit_action(self):
        # disconnect from the current proxy
        engine = sgtk.platform.current_engine()

        # disconnect from the current project
        engine.site_comm.shut_down()

        self._save_setting("pos", self.pos(), site_specific=True)

        self.close()
        self.systray.hide()
        QtGui.QApplication.instance().quit()

    def handle_hotkey_triggered(self):
        self.toggle_activate()

    def set_activation_hotkey(self, shortcut, native_modifiers, native_key):
        if osutils is None:
            return

        if shortcut.isEmpty():
            self._save_setting("activation_hotkey", ("", "", ""), site_specific=True)
            if self.__activation_hotkey is not None:
                osutils.unregister_global_hotkey(self.__activation_hotkey)
                self.__activation_hotkey = None
        else:
            if self.__activation_hotkey is not None:
                osutils.unregister_global_hotkey(self.__activation_hotkey)
            self.__activation_hotkey = osutils.register_global_hotkey(
                native_modifiers, native_key, self.handle_hotkey_triggered)
            self._save_setting(
                "activation_hotkey",
                (shortcut[0], native_modifiers, native_key),
                site_specific=True)

    def handle_auto_start_changed(self, state):
        if osutils is None:
            return

        if state == QtCore.Qt.Checked:
            osutils.set_launch_at_login(True)
        if state == QtCore.Qt.Unchecked:
            osutils.set_launch_at_login(False)

    def handle_project_refresh_action(self):
        """
        Force a reload of the project model.
        Clear cache and reload if shift is held down.
        """
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            self._project_model.hard_refresh()
        else:
            self._project_model._refresh_data()

    def handle_advanced_project_setup_action(self):
        """
        Display the classic project setup wizard if the current
        user appears to have sufficient permissions to actually
        setup a project. If not, pop up an error dialog informing
        them of the problem.
        """
        self.setup_project_widget.project = self.current_project

        # The first time a user selects the Advanced project setup
        # menu item, display the Setup Project help popup to provide
        # more information about this feature.
        wizard_setting = "advanced_project_setup_launched"
        help_wizard_shown = self._load_setting(
            wizard_setting, default_value=False, site_specific=False
        )
        if not help_wizard_shown:
            self._save_setting(
                wizard_setting, value=True, site_specific=False
            )

        # Bypass the Setup Toolkit overlay of the setup_project_widget
        # and go straight to the setup wizard window.
        self.setup_project_widget.do_setup(show_help=not(help_wizard_shown))

    def search_button_clicked(self):
        if self.ui.search_frame.property("collapsed"):
            # expand
            # do not show the project menu for the time being
            # self.ui.project_button.hide()
            self.ui.search_text.show()
            self.ui.search_text.setFocus()
            self.ui.search_magnifier.show()
            self.ui.search_button.setIcon(self._search_x_icon)
            self.ui.search_button.setStyleSheet("")
            self.ui.search_button.setToolTip("Clear search")
            self.ui.search_frame.setProperty("collapsed", False)
        else:
            # collapse
            self.ui.search_text.hide()
            self.ui.search_magnifier.hide()

            # Force update to keep from seeing the button flash
            QtGui.QApplication.processEvents()

            self.ui.search_text.setText("")
            # do not show the project menu for the time being
            # self.ui.project_button.show()
            self.ui.search_button.setIcon(self._search_magnifier_icon)
            self.ui.search_button.setToolTip("Search Projects")
            self.ui.search_button.setStyleSheet("""
                QPushButton {
                    border-image: url(:/tk-desktop/search_light.png);
                }

                QPushButton:hover {
                    border-image: url(:/tk-desktop/search_blue.png);
                }
            """)
            self.ui.search_frame.setProperty("collapsed", True)

        self.ui.search_frame.style().unpolish(self.ui.search_frame)
        self.ui.search_frame.style().polish(self.ui.search_frame)
        self.ui.search_frame.update()

    def search_text_changed(self, text):
        self._project_proxy.search_text = text

    def on_project_filesystem_folder_triggered(self):
        engine = sgtk.platform.current_engine()
        engine.refresh_user_credentials()
        engine.site_comm.call_no_response("open_project_locations")

    def on_project_commands_finished(self):
        """
        Invoked when all commands found for a project have been registered.
        """
        if self._project_command_count == 0:
            # Show the UI that indicates no project commands have been configured
            self.install_apps_widget.build_software_entity_config_widget(
                self.current_project
            )
            self.install_apps_widget.show()

    def _logout_current_user(self):
        """
        Logs current user out.
        """
        engine = sgtk.platform.current_engine()
        try:
            sg_auth.ShotgunAuthenticator().clear_default_user()
            if engine.uses_legacy_authentication():
                engine.create_legacy_login_instance().logout()
            return True
        except Exception:
            # if logout raises an exception, just log and don't crash
            log.exception("Error logging out.")
            return False

    def _switch_current_user(self, new_host, new_user):
        """
        Changes the default host and login.

        :param str new_host: URL of the new host.
        :param str new_user: Login of the new user.
        """

        engine = sgtk.platform.current_engine()

        # This is for ye-olde Shotgun Desktop < 1.1
        if engine.uses_legacy_authentication():
            login_framework = engine.create_legacy_login_instance()
            if new_host:
                login_framework.set_default_host(new_host)
            if new_user:
                login_framework.set_default_login(new_user)

        dm = sg_auth.DefaultsManager()
        if new_host:
            dm.set_host(new_host)

        if new_user:
            dm.set_login(new_user)

    def sign_out(self):
        self._logout_current_user()
        self._restart_desktop()

    def _restart_desktop(self):
        """
        Restarts the Shotgun Desktop application.
        """
        # restart the application
        self.handle_quit_action()
        # Very important to set close_fds otherwise the websocket server file descriptor
        # will be shared with the child process and it prevent restarting the server
        # after the process closes.
        # Solution was found here: http://stackoverflow.com/a/13593715
        # Also tell the new shotgun to skip the tray and go directly to the login.
        subprocess.Popen(sys.argv, close_fds=True)

    def _on_different_user(self, site, user_id):
        """
        Invoked when a request coming from a different site and/or user comes through.

        :param str site: URL of the site making the request.
        :param int user_id: User id of the HumanUser attempting the request.
        """
        # Makes sure that if the user is browsing multiples pages before coming back to the Desktop,
        # only the first request will generate a pop-up. Note that if requests comes from different users and/or sites,
        # only the first one will be acknowledged. This is to avoid having multiple modal dialogs popping up.
        if self._is_handling_switch_request:
            return
        self._is_handling_switch_request = True

        bundle = sgtk.platform.current_bundle()

        try:
            current_site = bundle.get_current_user().host

            if site.lower() in self._ignored_sites:
                log.info("Request ignored for '%s'.", site)
                return

            # Figure out if we need to restart because of a different site or simply a different user.
            if site.lower() != current_site.lower():
                msg = (
                    "A request originated from <b>{0}</b>, but you "
                    "are currently logged into <b>{1}</b>.<br/><br/>"
                    "If you would like to launch applications or browse for files from the browser, click the "
                    "<b>Restart</b> button below to restart Shotgun Desktop and log into <b>{0}</b>.".format(
                        urlparse.urlparse(site).netloc,
                        urlparse.urlparse(current_site).netloc
                    )
                )
                new_site = site
                # FIXME: At the moment we can't know whats the login of the user that made the
                # request from another site.
                user_login = None
            else:

                user = bundle.shotgun.find_one("HumanUser", [["id", "is", user_id]], ["login"])
                # If for some reason we can't see the user (permissions might be the cause),
                # use the <unknown> string.
                if user is None or not user.get("login"):
                    user_login = None
                else:
                    user_login = user["login"]

                msg = (
                    "A request from <b>{0}</b> was made, but you are currently "
                    "signed in as <b>{1}</b> in the Shotgun Desktop.<br/><br/>"
                    "If you would like to launch applications or browse for files from the browser, click the "
                    "<b>Restart</b> button below to restart Shotgun Desktop and log as <b>{0}</b>.".format(
                        user_login if user_login else "<unknown>", bundle.get_current_user().login
                    )
                )
                new_site = None

            dialog = BrowserIntegrationUserSwitchDialog(msg, self)

            # The following applies to macOS only and has no side-effect on other plaforms.
            # If the dialog is pinned, it means it is also in background. We'll bring the app to the foreground
            # so keyboard focus is granted automatically to the BrowserIntegrationUserSwitchDialog instead
            # of being unfocussed.
            if self.is_pinned() and osutils:
                osutils.make_app_foreground()

            dialog.exec_()

            if dialog.result() == dialog.RESTART:
                self._switch_current_user(new_site, user_login)
                self._restart_desktop()
            elif dialog.result() == dialog.IGNOREPERMANENTLY:
                self._ignored_sites.add(site.lower())
        finally:
            self._is_handling_switch_request = False

    def is_on_top(self):
        return (self.windowFlags() & QtCore.Qt.WindowStaysOnTopHint)

    def set_on_top(self, value):
        flags = self.windowFlags()
        visible = self.isVisible()

        if value:
            self.setWindowFlags(flags | QtCore.Qt.WindowStaysOnTopHint)
            self.ui.actionKeep_on_Top.setChecked(True)
            self._save_setting("on_top", True, site_specific=False)
        else:
            self.setWindowFlags(flags & ~QtCore.Qt.WindowStaysOnTopHint)
            self.ui.actionKeep_on_Top.setChecked(False)
            self._save_setting("on_top", False, site_specific=False)

        if visible:
            self.show()

    def toggle_keep_on_top(self):
        on_top = self.is_on_top()
        self.set_on_top(not on_top)

    ########################################################################################
    # project view
    def get_app_widget(self, namespace=None):
        return self.ui.project_commands

    def add_to_project_menu(self, action):
        self.project_menu.insertAction(self.__pipeline_configuration_separator, action)

    def add_project_command(
        self, name, button_name, menu_name, icon, command_tooltip, groups, is_menu_default
    ):
        """
        Add a button command to the Project dialog. Keeps a running total of how
        many commands were added. If no commands are added for the Project, the
        "We couldn't find anything to launch" overlay is displayed.

        :param str name: The name of the command used for internal tracking
        :param str button_name: The label for the command button.
        :param str menu_name: The label for the command button's drop-down menu item.
        :param QtGui.QIcon icon: The icon to display for the command button and RECENT item.
        :param str command_tooltip: A brief summary of what this command does.
        :param list groups: The list of Desktop folder groups this command should appear in.
        :param bool is_menu_default: If this command is a menu item, indicate whether it should
                                     also be run by the command button.
        """
        self._project_command_model.add_command(
            name, button_name, menu_name, icon, command_tooltip, groups, is_menu_default
        )
        self._project_command_proxy.invalidate()
        self._project_command_count += 1

    def _handle_project_data_changed(self):
        self._project_command_count = 0
        self._project_selection_model.clear()
        self._project_proxy.invalidate()
        self._project_proxy.sort(0)

    def _on_back_to_projects_clicked(self):
        """
        Invoked when the user leaves a project.
        """
        engine = sgtk.platform.current_engine()
        engine.site_comm.shut_down()

        self._current_pipeline_descriptor = None
        self._update_banners()

        # If we were in zero config mode, we need to abort the syncing.
        if self._sync_thread:
            # This is non-blocking and if the thread has already stopped running it has no side-effect.
            self._sync_thread.abort()

        self._project_command_count = 0
        self._project_selection_model.clear()
        self._project_proxy.invalidate()
        self._project_proxy.sort(0)

        self.slide_view(self.ui.project_browser_page, "left")

        # remember that we are back at the browser
        self.current_project = None
        self._save_setting("project_id", 0, site_specific=True)

        # We are switching back to the project list, so need to show the
        # "Refresh Projects" and hide the "Advanced project setup" menu
        # items once again.
        self.ui.actionRefresh_Projects.setVisible(True)
        self.ui.actionAdvanced_Project_Setup.setVisible(False)

    def set_groups(self, groups, show_recents=True):
        self._project_command_model.set_project(
            self.current_project, groups, show_recents=show_recents)
        self.project_overlay.hide()

        key = "project_expanded_state.%d" % self.current_project["id"]
        expanded_state = self._load_setting(key, {}, True)
        self._project_command_model.set_expanded_state(expanded_state)

    def clear_app_uis(self):
        # empty the project commands
        self._project_command_model.clear()

        # hide the pipeline configuration bar
        self.ui.configuration_frame.hide()

        # hide the setup project ui if it is shown
        self.setup_project_widget.hide()
        self.update_project_config_widget.hide()
        self.setup_new_os_widget.hide()
        self.install_apps_widget.hide()
        self.project_overlay.hide()

        # clear the project specific menu
        self.project_menu = QtGui.QMenu(self)
        self.project_menu.aboutToShow.connect(self._on_project_menu_about_to_show)
        self.project_menu.triggered.connect(self._on_project_menu_triggered)
        self.ui.actionProject_Filesystem_Folder.setVisible(True)
        self.project_menu.addAction(self.ui.actionProject_Filesystem_Folder)
        self.ui.project_menu.setMenu(self.project_menu)
        self.__pipeline_configuration_separator = None

    def show_update_project_config(self):
        self.update_project_config_widget.show()
        self.project_overlay.hide()

    def __populate_pipeline_configurations_menu(self, pipeline_configurations, selected):
        """
        This will populate the menu with all the pipeline configurations.

            - It will only be built if two or more configurations are available.
            - Primaries goes first, then everything else is alphabetical.
            - If two primaries have the same name, the lowest id comes first.
            - If more than two pipelines have the same name, their id is suffixed between paratheses.

        :param list pipeline_configurations: List of pipeline configurations link.
        :param id selected: Id of the pipeline that is currently selected. The selected pipeline
            will have a marked checked box next to its name.
        """

        if len(pipeline_configurations) < 2:
            log.debug("Less than two pipeline configurations were found, not building menu.")
            # only one configuration choice
            return

        log.debug("More than one pipeline configuration was found, building menu.")

        # Add a separator that will be above the pipeline configurations. Context menu actions will go over that.
        self.__pipeline_configuration_separator = self.project_menu.addSeparator()

        # Build the configuration section header.
        label = QtGui.QLabel("CONFIGURATION")
        label.setObjectName("project_menu_configuration_label")
        action = QtGui.QWidgetAction(self)
        action.setDefaultWidget(label)
        self.project_menu.addAction(action)

        # Group every sandboxes by their name and add pipelines one at a time
        for pc_name, pc_group in itertools.groupby(pipeline_configurations, lambda x: x["name"]):
            self._add_pipeline_group_to_menu(list(pc_group), selected)

    def _add_pipeline_group_to_menu(self, pc_group, selected):
        """
        Adds a group of pipelines to the menu.

        Pipelines are assumed to have the same name.

        :param list pc_group: List of pipeline entities with keys ''id'', ''name'' and ''project''.
        :param dict selected: Pipeline configuration to select.
        """
        for pc in pc_group:
            parenthesis_arguments = []
            # If this is a site level configuration, suffix (site) to it.
            if pc["project"] is None:
                parenthesis_arguments.append("site")

            # If there are more than one pipeline in the group, we'll suffix the pipeline id.
            if len(pc_group) > 1:
                parenthesis_arguments.append("id %d" % pc["id"])

            if parenthesis_arguments:
                unique_pc_name = "%s (%s)" % (pc["name"], ", ".join(parenthesis_arguments))
            else:
                unique_pc_name = pc["name"]

            action = self.project_menu.addAction(unique_pc_name)
            action.setCheckable(True)
            action.setProperty("project_configuration_id", pc["id"])

            # If this pipeline is the one that was selected, mark it in the
            # menu and update the configuration name widget.
            if selected and selected["id"] == pc["id"]:
                action.setChecked(True)
                self.ui.configuration_name.setText(unique_pc_name)

                # If we haven't picked a primary, show the sandbox header.
                if not self._is_primary_pc(pc):
                    self.ui.configuration_frame.show()

    def __set_project_just_accessed(self, project):
        self._project_model.update_project_accessed_time(project)

    def _on_project_selection(self, selected, deselected):
        selected_indexes = selected.indexes()

        if len(selected_indexes) == 0:
            return

        proxy_model = selected_indexes[0].model()
        source_index = proxy_model.mapToSource(selected_indexes[0])
        item = source_index.model().itemFromIndex(source_index)
        self.__set_project_from_item(item)

    def __set_project_from_id(self, project_id):
        if id == 0:
            return

        # find the project in the model
        model = self._project_selection_model.model()
        for i in xrange(model.rowCount()):
            index = model.index(i, 0)

            if hasattr(model, "mapToSource"):
                # if we are a proxy model, translate to source
                source_index = model.mapToSource(index)
                item = source_index.model().itemFromIndex(source_index)
            else:
                item = model.itemFromIndex(index)

            project = item.data(ShotgunModel.SG_DATA_ROLE)
            if project["id"] == project_id:
                # select it in the model
                self._project_selection_model.select(
                    index, self._project_selection_model.SelectCurrent)
                break

    def __get_icon_pixmap(self, icon, size):
        pixmap = icon.pixmap(512, 512)
        return pixmap.scaled(size, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)

    def __set_project_from_item(self, item):
        # slide in the project specific view
        self.slide_view(self.ui.project_page, "right")

        # update the project icon and name
        self.ui.project_icon.setPixmap(self.__get_icon_pixmap(item.icon(), self.ui.project_icon.size()))
        project = item.data(SgProjectModel.SG_DATA_ROLE)
        self.ui.project_name.setText(project.get("name", "No Name"))

        # launch the app proxy
        project = item.data(SgProjectModel.SG_DATA_ROLE)
        self.__launch_app_proxy_for_project(project)

    def _on_project_menu_about_to_show(self):
        """
        Called just before the project specific menu is shown to the user.
        """

        engine = sgtk.platform.current_engine()

        try:
            # Get the availability of the project locations.
            has_project_locations = engine.site_comm.call("test_project_locations")
        except Exception, exception:
            log.debug("Cannot get the availability of the project locations: %s" % exception)
            # Assume project locations are not available.
            has_project_locations = False

        # Show or hide project menu item "Project Filesystem Folder"
        # based on the availability of the project locations.
        self.ui.actionProject_Filesystem_Folder.setVisible(has_project_locations)

    def _on_project_menu_triggered(self, action):
        pc_id = action.property("project_configuration_id")

        if pc_id is not None:
            self.__launch_app_proxy_for_project(self.current_project, pc_id)

    def _on_setup_finished(self, success):
        if success:
            self.__launch_app_proxy_for_project(self.current_project)

    def _on_update_finished(self, success):
        if success:
            self.__launch_app_proxy_for_project(self.current_project)

    def _is_primary_pc(self, pc):
        """
        Tests if a pipeline configuration is a primary.

        :param pc: Pipeline configuration entity with key ``code``.

        :returns: True if the pipeline configuration is a primary, else otherwise.
        """
        return pc["name"] == constants.PRIMARY_PIPELINE_CONFIG_NAME

    def __get_server_version(self, connection):
        """
        Retrieves the server version from the connection.

        :param connection: Shotgun connection we want the server version from.
        :returns: Tuple of (major, minor, patch) versions.
        """
        sg_major_ver = connection.server_info["version"][0]
        sg_minor_ver = connection.server_info["version"][1]
        sg_patch_ver = connection.server_info["version"][2]
        return sg_major_ver, sg_minor_ver, sg_patch_ver

    def engine_startup_error(self, error, tb):
        """
        Handle an error starting up the engine for the app proxy.

        :param error: Exception object that was raised during bootstrap.
        :param tb: Traceback of the exception raised during bootstrap.
        """
        trigger_project_config = False
        # If missing engine init error, we're know we have to setup the project.
        if isinstance(error, sgtk.platform.TankMissingEngineError):
            message = "Error starting engine\n\n%s" % error.message
            trigger_project_config = True
        # However, this exception type hasn't always existed, so take care of that
        # case also.
        elif isinstance(error, sgtk.platform.TankEngineInitError):
            message = "Error starting engine\n\n%s" % error.message
            # match directly on the error message until something less fragile can be put in place
            if error.message.startswith("Cannot find an engine instance tk-desktop"):
                trigger_project_config = True
        else:
            message = "Error\n\n%s" % error.message

        if trigger_project_config and not self._current_pipeline_descriptor.is_immutable():
            # error is that the desktop engine hasn't been setup for the project
            # show the UI to configure it
            self.show_update_project_config()
        else:
            # just show the error in the window
            display_message = "%s\n\nSee the console for more details." % message
            self.project_overlay.show_error_message(display_message)

            # add the traceback if available
            if tb is not None:
                message += "\n\n%s" % tb
            log.error(message)

    def __launch_app_proxy_for_project(self, project, requested_pipeline_configuration_id=None):
        try:
            engine = sgtk.platform.current_engine()
            log.debug("launching app proxy for project: %s" % project)

            #############################
            # Phase 1: Get the UI pretty.

            # Make sure that not only the previous proxy is not running anymore
            # but that the UI has been cleared as well.
            engine = sgtk.platform.current_engine()
            engine.site_comm.shut_down()
            self.clear_app_uis()
            # Always hide the Refresh Projects menu item when launching the project engine
            # since no projects will be displayed in the app launcher pane.
            self.ui.actionRefresh_Projects.setVisible(False)

            self.current_project = project

            # trigger an update to the model to track this project access
            self.__set_project_just_accessed(project)
            QtGui.QApplication.instance().processEvents()

            ############################################################
            # Phase 2: Get information about the pipeline configuration.

            toolkit_manager = ToolkitManager(engine.get_current_user())
            # We need to cache all environments because we don't know which one the user will require.
            toolkit_manager.caching_policy = ToolkitManager.CACHE_FULL
            toolkit_manager.plugin_id = "basic.desktop"
            toolkit_manager.base_configuration = "sgtk:descriptor:app_store?name=tk-config-basic"
            toolkit_manager.bundle_cache_fallback_paths.extend(
                engine.sgtk.bundle_cache_fallback_paths
            )
            pipeline_configurations = toolkit_manager.get_pipeline_configurations(project)

            log.debug("The following pipeline configurations for this project have been found:")
            log.debug(pprint.pformat(pipeline_configurations))

            # No specific pipeline was requested, load the previously used one.
            setting_name = "pipeline_configuration_for_project_%d" % project["id"]
            if requested_pipeline_configuration_id is None:
                log.debug("Searching for the latest config that was used.")
                requested_pipeline_configuration_id = self._load_setting(setting_name, None, site_specific=True)

            # Pick a pipeline configuration from the list to use.
            pipeline_configuration_to_load = self._pick_pipeline_configuration(
                pipeline_configurations, requested_pipeline_configuration_id, project
            )

            # If we've found what we should be loading.
            if pipeline_configuration_to_load:
                # Remember what we just picked so we pick the same thing next time we launch the app.
                log.debug("Updating %s to %d.", setting_name, pipeline_configuration_to_load["id"])
                self._save_setting(setting_name, pipeline_configuration_to_load["id"], site_specific=True)

            # Add all the pipeline configurations to the menu.
            self.__populate_pipeline_configurations_menu(pipeline_configurations, pipeline_configuration_to_load)

            # If no pipeline configurations were found in Shotgun, show the
            # 'Advanced project setup...' menu item.
            # If there is no pipeline configuration set for the current project, add the Advanced Project Setup menu.
            if not any(True if pc["project"] else False for pc in pipeline_configurations):
                # If we have the new Shotgun that supports zero config, add the setup project entry in the menu
                if self.__get_server_version(engine.shotgun) >= (7, 2, 0):
                    self.ui.actionAdvanced_Project_Setup.setVisible(True)
                else:
                    # Otherwise hide the entry and provide the same old experience as before and quit, as we can't
                    # bootstrap.
                    self.ui.actionAdvanced_Project_Setup.setVisible(False)
                    self.setup_project_widget.project = project
                    self.setup_project_widget.show()
                    # Stop here, we don't want to launch Python at this point.
                    return
            else:
                self.ui.actionAdvanced_Project_Setup.setVisible(False)

            # From this point on, we don't touch the UI anymore.

            ##############################################
            # Phase 3: Prepare the pipeline configuration.

            # Bootstrap into the requested pipeline configuration or using the fallback.
            if pipeline_configuration_to_load is None:
                toolkit_manager.pipeline_configuration = None
                config_descriptor = toolkit_manager.resolve_descriptor(project)
            else:
                # We've loaded this project before and saved its pipeline configuration id, so
                # reload the same old one.
                toolkit_manager.pipeline_configuration = pipeline_configuration_to_load["id"]
                config_descriptor = pipeline_configuration_to_load["descriptor"]
        except Exception as error:
            log.exception(str(error))
            message = ("%s"
                       "\n\nTo resolve this, open Shotgun in your browser\n"
                       "and check the paths for this Pipeline Configuration."
                       "\n\nFor more details, see the console." % str(error))
            self.project_overlay.show_error_message(message)
            return

        # From this point on, we don't touch the UI anymore.
        self.project_overlay.start_progress()

        try:
            self._current_pipeline_descriptor = config_descriptor
            # Find the interpreter the config wants to use.
            try:
                path_to_python = config_descriptor.python_interpreter
            except TankFileDoesNotExistError:
                if sys.platform == "darwin":
                    path_to_python = os.path.join(sys.prefix, "bin", "python")
                elif sys.platform == "win32":
                    path_to_python = os.path.join(sys.prefix, "python.exe")
                else:
                    path_to_python = os.path.join(sys.prefix, "bin", "python")

            # Create a descriptor for the current core and gets its PYTHONPATH.
            core_python = sgtk.get_sgtk_module_path()

            config_path = engine.sgtk.configuration_descriptor.get_path()

            # startup server pipe to listen
            engine.startup_rpc()

            # pickle up the info needed to bootstrap the project python
            desktop_data = {
                "core_python_path": core_python,
                # Every settings that were used for discovering the pipeline configuration must be
                # passed down to the next process so it can launch the same pipeline.
                "manager_settings": toolkit_manager.extract_settings(),
                # We're passing down our implementation of the RPC module since the process
                # will want to communicate back with us during bootstrapping.
                # Get the source file, not __file__, since the background process will use imp.load_source
                # This is important because if we used __file__ we would need to call imp.load_compiled,
                # which will fail if the bytecode magic number is different between this process's
                # python and the one for the pipeline configuration.
                "rpc_lib_path": inspect.getsourcefile(rpc),
                "project": self.current_project,
                # Authentication credentials to connect back to this process.
                "proxy_data": {
                    "proxy_pipe": engine.site_comm.server_pipe,
                    "proxy_auth": engine.site_comm.server_authkey
                }
            }
            (_, pickle_data_file) = tempfile.mkstemp(suffix='.pkl')
            pickle.dump(desktop_data, open(pickle_data_file, "wb"))

            # update the values on the project updater in case they are needed
            self.update_project_config_widget.set_project_info(
                path_to_python, core_python, config_path, self.current_project)

            # get the path to the utilities module
            utilities_module_path = os.path.realpath(
                os.path.join(__file__, "..", "..", "utils", "bootstrap_utilities.py")
            )

            # Make sure the credentials are refreshed so the background process
            # has no problem launching.
            engine.refresh_user_credentials()
            # Ticket 26741: Avoid having odd DLL loading issues on windows
            self._push_dll_state()

            try:
                os.environ["SHOTGUN_DESKTOP_CURRENT_USER"] = sgtk.authentication.serialize_user(
                    engine.get_current_user()
                )
                engine.execute_hook(
                    "hook_launch_python",
                    project_python=path_to_python,
                    pickle_data_path=pickle_data_file,
                    utilities_module_path=utilities_module_path,
                )
            finally:
                self._pop_dll_state()
        except (TankInvalidInterpreterLocationError, TankFileDoesNotExistError) as e:
            log.exception("Problem locating interpreter file:")
            self.setup_new_os_widget.show()
            self.project_overlay.hide()
            return
        except Exception as e:
            log.exception("Unexpected error while launching Python:")
            self._launch_failed(str(e))
        else:
            # and remember what we launched for next time
            self._save_setting("project_id", self.current_project["id"], site_specific=True)
            # Banners might need to be updated, we might have picked a configuration that has been
            # updated.
            self._update_banners()
        finally:
            if "SHOTGUN_DESKTOP_CURRENT_USER" in os.environ:
                del os.environ["SHOTGUN_DESKTOP_CURRENT_USER"]

    def _launch_failed(self, message):
        """
        Invoked when the launch fails.

        :param message: Error message to display.
        """
        message = ("%s"
                   "\n\nFor more details, see the console." % message)
        self.project_overlay.show_error_message(message)

    def bootstrap_progress_callback(self, value, msg):
        """
        Reports progress on the project overlay.

        :param value: Value between 0 and 1 indicating progress.
        :param msg: Message to display in the overlay.
        """
        self.project_overlay.report_progress(value, msg)

    def _pick_pipeline_configuration(self, pipeline_configurations, requested_pipeline_configuration_id, project):
        """
        Picks which pipeline configuration to be loaded based on user input or previously used
        pipeline settings.

        :param list pipeline_configurations: List of dicionaries with keys 'id' and 'code'.
        :param dict project: Project entity dictionary with key 'id'.

        :returns: The pipeline configuration that should be loaded, or None.
        :rtype: dict
        """

        # No pipeline was found, so nothing to pick.
        if not pipeline_configurations:
            log.debug("No pipeline configuration to choose from.")
            return None

        log.debug("Looking for pipeline configuration %s.", requested_pipeline_configuration_id)

        # Find the matching pipeline configuration to launch against
        for pc in pipeline_configurations:
            # If the current pipeline matches the one we are looking for.
            if pc["id"] == requested_pipeline_configuration_id:
                return pc

        # We know there is at least one pipeline available, so pick the first. If we couldn't
        # find a given sandbox, this has the benefit of picking the primary, which is sensible
        # fallback.
        log.debug(
            "Requested pipeline configuration was not found. Falling back on %s",
            pprint.pformat(pipeline_configurations[0])
        )
        return pipeline_configurations[0]

    def slide_view(self, new_page, from_direction="right"):
        offsetx = self.ui.apps_tab.frameRect().width()
        offsety = self.ui.apps_tab.frameRect().height()
        current_page = self.ui.apps_tab.currentWidget()

        new_page.setGeometry(0, 0, offsetx, offsety)

        if from_direction == "left":
            offsetx = -offsetx

        curr_pos = new_page.pos()
        new_page.move(curr_pos.x() + offsetx, curr_pos.y())
        new_page.show()
        new_page.raise_()

        anim_old = QtCore.QPropertyAnimation(current_page, "pos", self)
        anim_old.setDuration(500)
        anim_old.setStartValue(QtCore.QPoint(curr_pos.x(), curr_pos.y()))
        anim_old.setEndValue(QtCore.QPoint(curr_pos.x() - offsetx, curr_pos.y()))
        anim_old.setEasingCurve(QtCore.QEasingCurve.OutBack)

        anim_new = QtCore.QPropertyAnimation(new_page, "pos", self)
        anim_new.setDuration(500)
        anim_new.setStartValue(QtCore.QPoint(curr_pos.x() + offsetx, curr_pos.y()))
        anim_new.setEndValue(QtCore.QPoint(curr_pos.x(), curr_pos.y()))
        anim_new.setEasingCurve(QtCore.QEasingCurve.OutBack)

        anim_group = QtCore.QParallelAnimationGroup(self)
        anim_group.addAnimation(anim_old)
        anim_group.addAnimation(anim_new)

        def slide_finished():
            self.ui.apps_tab.setCurrentWidget(new_page)
        anim_group.finished.connect(slide_finished)
        anim_group.start()

    def open_site_in_browser(self):
        url = shotgun.get_associated_sg_base_url()
        if self.current_project is not None:
            url = "%s/detail/Project/%d" % (url, self.current_project["id"])

        QtGui.QDesktopServices.openUrl(url)

    def handle_about(self):
        engine = sgtk.platform.current_engine()
        # If a Startup version was specified when engine.run was invoked
        # it's because we're running the new installer code and therefore
        # we have a startup version to show.

        versions = OrderedDict()
        versions["App Version"] = engine.app_version

        if engine.startup_version:
            versions["Startup Version"] = engine.startup_version

        versions["Engine Version"] = engine.version
        versions["Core"] = engine.sgtk.version

        if engine.sgtk.configuration_descriptor:
            # Certain versions of core don't like configuration's without an
            # info.yml, so tolerate it.
            try:
                versions[
                    engine.sgtk.configuration_descriptor.display_name
                ] = engine.sgtk.configuration_descriptor.version
            except Exception:
                pass

        body = "<center>"
        for name, version in versions.iteritems():
            body += "    {0} {1}<br/>".format(name, version)
        body += "</center>"

        about = AboutScreen(parent=self, body=body)
        about.exec_()
