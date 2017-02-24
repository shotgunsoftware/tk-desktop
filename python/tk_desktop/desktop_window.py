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
from operator import itemgetter

from tank.platform.qt import QtCore, QtGui

import sgtk
from sgtk.util import shotgun
from sgtk.bootstrap import ToolkitManager
from sgtk.platform import constants
from tank_vendor import shotgun_authentication as sg_auth
from sgtk import TankInvalidInterpreterLocationError, TankFileDoesNotExistError
from sgtk.platform import get_logger
from sgtk.util import ShotgunPath

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

from .project_commands_model import ProjectCommandModel
from .project_commands_model import ProjectCommandProxyModel
from .project_commands_widget import ProjectCommandDelegate
from .project_synchronization_thread import ProjectSynchronizationThread

try:
    from .extensions import osutils
except Exception:
    osutils = None

# import our frameworks
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
overlay_widget = sgtk.platform.import_framework("tk-framework-qtwidgets", "overlay_widget")
settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")

ShotgunModel = shotgun_model.ShotgunModel

log = get_logger(__name__)


class DesktopWindow(SystrayWindow):
    """ Dockable window for the Shotgun system tray """

    ORGANIZATION = "Shotgun Software"
    APPLICATION = "tk-desktop"
    _BOOTSTRAP_END_RATIO = 0.9
    _LAUNCHING_PYTHON_RATIO = 0.95

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

        # setup systray behavior
        self.set_content_layout(self.ui.border_layout)
        self.set_drag_widgets([self.ui.header, self.ui.footer])

        self.systray_state_changed.connect(self.handle_systray_state_changed)
        QtGui.QApplication.instance().setQuitOnLastWindowClosed(False)

        # Setup header buttons
        self.ui.apps_button.setProperty("active", True)
        self.ui.apps_button.style().unpolish(self.ui.apps_button)
        self.ui.apps_button.style().polish(self.ui.apps_button)

        connection = engine.get_current_user().create_sg_connection()

        # Setup the console
        self.__console = Console()
        self.__console_handler = ConsoleLogHandler(self.__console)
        engine.add_logging_handler(self.__console_handler)

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
        self.user_menu.addAction(self.ui.actionPin_to_Menu)
        self.user_menu.addAction(self.ui.actionKeep_on_Top)
        self.user_menu.addAction(self.ui.actionShow_Console)
        self.user_menu.addAction(self.ui.actionRefresh_Projects)
        self.user_menu.addAction(self.ui.actionAdvanced_Project_Setup)
        about_action = self.user_menu.addAction("About...")
        self.user_menu.addSeparator()
        self.user_menu.addAction(self.ui.actionSign_Out)
        self.user_menu.addAction(self.ui.actionQuit)

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

        # Do not put anything after this line, this can kick-off a Python process launch, which should
        # be done only when the dialog is fully initialized.
        self._load_settings()

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
        '''
        Push current Dll Directory
        '''
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
        '''
        Pop the previously pushed DLL Directory
        '''
        if sys.platform == "win32":
            try:
                import win32api
                win32api.SetDllDirectory(self._previous_dll_directory)
            except StandardError:
                log.warning("Could not restore DllDirectory under Windows.")

    ########################################################################################
    # Event handlers and slots
    def contextMenuEvent(self, event):
        self.user_menu.exec_(event.globalPos())

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

    def sign_out(self):
        engine = sgtk.platform.current_engine()

        try:
            sg_auth.ShotgunAuthenticator().clear_default_user()
            if engine.uses_legacy_authentication():
                engine.create_legacy_login_instance().logout()
        except Exception:
            # if logout raises an exception, just log and don't crash
            log.exception("Error logging out.")

        # restart the application
        self.handle_quit_action()
        # Very important to set close_fds otherwise the websocket server file descriptor
        # will be shared with the child process and it prevent restarting the server
        # after the process closes.
        # Solution was found here: http://stackoverflow.com/a/13593715
        # Also tell the new shotgun to skip the tray and go directly to the login.
        subprocess.Popen(sys.argv + ["--show-login"], close_fds=True)

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

        # This is non-blocking and if the thread has already stopped running it has so side-effect.
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

        # Now it's time to add entries to the menu.

        # Step 1: Extract the primary and add it to the menu.
        primaries = filter(self._is_primary_pc, pipeline_configurations)
        if primaries:
            self._add_pipeline_group_to_menu(primaries, selected)

        # Step 2: Extract the sandboxes and add them to the menu.

        # Get all non primary configurations.
        sandboxes = filter(lambda pc: not self._is_primary_pc(pc), pipeline_configurations)

        # Sandboxes are sorted alphabetically. When two sandboxes have the same name,
        # sort on the project field so that site level configurations appear first. If multiple site level
        # configurations are also available, sort by id.
        sandboxes = sorted(sandboxes, key=itemgetter("name", "project", "id"))

        # Group every sandboxes by their name and add pipelines one at a time
        for pc_name, pc_group in itertools.groupby(sandboxes, lambda x: x["name"]):
            self._add_pipeline_group_to_menu(list(pc_group), selected)

        # Step 3: Profit!

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

    def _get_toolkit_classic_pipeline_configurations(self, connection, project):
        """
        Get all the pipeline configurations that are not using plugin ids.

        :param connection: Shotgun connection instance.
        :param dict project: Project entity link.

        :returns: List of pipeline configuration dictionaries with keys ``mac_path``, ``windows_path``,
            ``linux_path``, ``users`` and ``name``
        """
        found_pcs = connection.find(
            "PipelineConfiguration",
            [["project", "is", project]],
            fields=["mac_path", "windows_path", "linux_path", "users", "code", "sg_plugin_ids", "plugin_ids", "project"]
        )

        def is_pipeline_usable(pc):
            """
            Ensures that a pipeline is not zero-config based and that it is accessible for the current user.
            """
            # If there is a plugin id, can't use this.
            if pc.get("sg_plugin_ids") or pc.get("plugin_ids"):
                return False

            if not ShotgunPath.from_shotgun_dict(pc):
                log.warning("Skipping Toolkit Classic pipeline configuration '%s' without any path set." % pc["id"])
                return False

            # If there are no users assigned, this pipeline is accessible from for everyone.
            if not pc["users"]:
                return True

            # Search for ourselves.
            for user in pc["users"]:
                # We've found ourselves, awesome!
                if self._current_user_id == user["id"]:
                    return True

            return False

        # FIXME: We need to discuss what we do with multiple primaries with Toolkit classic. In zero config we keep
        # the earliest one. It follows that the new desktop should follow the same rules, but the behavior already
        # exists in the wild, so we may have to keep supporting that one.

        # Filter out pipelines that can't be accessed.
        accessible_pcs = filter(is_pipeline_usable, found_pcs)

        # Massage the dictionaries keys so it uses the same key names of the zero config pipelines.
        for pc in accessible_pcs:
            pc["name"] = pc["code"]
            del pc["code"]

        return accessible_pcs

    def _is_primary_pc(self, pc):
        """
        Tests if a pipeline configuration is a primary.

        :param pc: Pipeline configuration entity with key ``code``.

        :returns: True if the pipeline configuration is a primary, else otherwise.
        """
        return pc["name"] == constants.PRIMARY_PIPELINE_CONFIG_NAME

    def _merge_pipeline_configuration_lists(self, classic_pcs, bootstrap_pcs):
        """
        Merges the pipeline configurations lists while taking out boostrap pipeline configurations
        if a Toolkit classic pipeline configuration is also present.

        :param list classic_pcs: List of Toolkit Classic pipeline configuration entity dictionaries.
        :param list bootstrap_pcs: List of bootstrap pipeline configuration entity dictionaries.

        :returns: Merged list of pipeline configurations entities with a single primary
            pipeline configuration.
        :rtype: list
        """

        # Find if there is a primary pipeline configuration in the classic pipelines.
        has_classic_primary = any(self._is_primary_pc(pc) for pc in classic_pcs)
        has_zero_config_primary = any(self._is_primary_pc(pc) for pc in bootstrap_pcs)

        if has_classic_primary and has_zero_config_primary:
            log.warning(
                "Toolkit Classic 'Primary' pipeline configuration '%d' overrides "
                "bootstrap 'Primary' pipeline configuration '%d'.")
            # Only keep non-primaries
            bootstrap_pcs = filter(lambda pc: not self._is_primary_pc(pc), bootstrap_pcs)

        return classic_pcs + bootstrap_pcs

    def __launch_app_proxy_for_project(self, project, requested_pipeline_configuration_id=None):
        try:
            engine = sgtk.platform.current_engine()
            log.debug("launching app proxy for project: %s" % project)

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

            # Phase 2: Get information about the pipeline configuration.
            #
            # This phase is a two step process. First, get all the pipeline configurations that are
            # not using plugin ids. Those are classic Toolkit pipeline configurations using *_path fields.
            # Then, fetch the rest using the ToolkitManager, which honors the plugin_id flag.

            # Step 1: First get the legacy pipeline configurations, i.e. those using the *_path fields.
            connection = engine.shotgun
            pipeline_configurations = self._get_toolkit_classic_pipeline_configurations(connection, project)

            toolkit_manager = ToolkitManager(engine.get_current_user())
            # We need to cache all environments because we don't know which one the user will require.
            toolkit_manager.caching_policy = ToolkitManager.CACHE_FULL
            toolkit_manager.plugin_id = "basic.desktop"
            toolkit_manager.base_configuration = "sgtk:descriptor:app_store?name=tk-config-basic"
            toolkit_manager.bundle_cache_fallback_paths.extend(
                engine.sgtk.bundle_cache_fallback_paths
            )
            # Step 2: Retrieves the pipeline configurations that use plugin ids usable by the current user.
            # and merge that list with the toolkit classic ones.
            pipeline_configurations = self._merge_pipeline_configuration_lists(
                pipeline_configurations,
                toolkit_manager.get_pipeline_configurations(project)
            )

            log.debug("The following pipeline configurations for this project have been found:")
            log.debug(pprint.pformat(pipeline_configurations))

            pipeline_configuration_to_load = self._pick_pipeline_configuration(
                pipeline_configurations, requested_pipeline_configuration_id, project
            )

            # going to launch the configuration, update the project menu if needed
            self.__populate_pipeline_configurations_menu(pipeline_configurations, pipeline_configuration_to_load)

            # If no pipeline configurations were found in Shotgun, show the
            # 'Advanced project setup...' menu item.
            if not pipeline_configurations:
                # Enable user menu item to launch classic Project Setup wizard
                self.ui.actionAdvanced_Project_Setup.setVisible(True)
            else:
                # Disable user menu item that launches classic Project Setup wizard
                self.ui.actionAdvanced_Project_Setup.setVisible(False)

            # From this point on, we don't touch the UI anymore.

            # Phase 3: Prepare the pipeline configuration.

            # If no pipeline configuration is in the user settings, we will let the bootstrap
            # pick the right pipeline configuration for the first launch.
            if pipeline_configuration_to_load is None:
                toolkit_manager.pipeline_configuration = None
            else:
                # We've loaded this project before and saved its pipeline configuration id, so
                # reload the same old one.
                toolkit_manager.pipeline_configuration = pipeline_configuration_to_load["id"]
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

        self._sync_thread = ProjectSynchronizationThread(toolkit_manager, project)
        self._sync_thread.sync_failed.connect(self._launch_failed)
        self._sync_thread.report_progress.connect(
            lambda pct, msg: self.project_overlay.report_progress(pct * self._BOOTSTRAP_END_RATIO, msg)
        )
        self._sync_thread.sync_success.connect(self._sync_success)
        self._sync_thread.start()

    def _pick_pipeline_configuration(self, pipeline_configurations, requested_pipeline_configuration_id, project):
        """
        Picks which pipeline configuration to be loaded based on user input or previously used
        pipeline settings.

        :param list pipeline_configurations: List of dicionaries with keys 'id' and 'code'.
        :param dict project: Project entity dictionary with key 'id'.

        :returns: The pipeline configuration that should be loaded, or None.
        :rtype: dict
        """
        setting_name = "pipeline_configuration_for_project_%d" % project["id"]

        # No specific pipeline was requested, load the previously used one.
        if requested_pipeline_configuration_id is None:
            log.debug("Searching for the latest config that was used.")
            requested_pipeline_configuration_id = self._load_setting(setting_name, None, site_specific=True)

        log.debug("Looking for pipeline configuration %s.", requested_pipeline_configuration_id)

        # Find the matching pipeline configuration to launch against
        pipeline_configuration_to_load = None
        primary_pipeline_configuration = None
        for pc in pipeline_configurations:
            # If we've stumbled upon the Primary.
            if self._is_primary_pc(pc):
                primary_pipeline_configuration = pc

            # If the current pipeline matches the one we are looking for.
            if pc["id"] == requested_pipeline_configuration_id:
                pipeline_configuration_to_load = pc

            # If we've found everything, we can stop looking.
            if primary_pipeline_configuration and pipeline_configuration_to_load:
                break

        # If we haven't found something to load.
        if not pipeline_configuration_to_load:
            # If there's a primary available, fall back to that.
            if primary_pipeline_configuration:
                log.warning(
                    "Pipeline configuration id %s was not found, falling back to primary.",
                    requested_pipeline_configuration_id
                )
                pipeline_configuration_to_load = primary_pipeline_configuration
            elif requested_pipeline_configuration_id:
                log.warning("Pipeline configuration id %s was not found.", requested_pipeline_configuration_id)
            else:
                log.debug("No primary was found nor was a specific pipeline requested.")

        if pipeline_configuration_to_load is None:
            log.debug("Updating %s to None.", setting_name)
            # Save requested_pipeline_configuration_id as last accessed
            self._save_setting(setting_name, None, site_specific=True)
        else:
            log.debug("Updating %s to %d.", setting_name, pipeline_configuration_to_load["id"])
            # Save requested_pipeline_configuration_id as last accessed
            self._save_setting(setting_name, pipeline_configuration_to_load["id"], site_specific=True)

        return pipeline_configuration_to_load

    def _launch_failed(self, message):
        message = ("%s"
                   "\n\nTo resolve this, open Shotgun in your browser\n"
                   "and check the paths for this Pipeline Configuration."
                   "\n\nFor more details, see the console." % message)
        self.project_overlay.show_error_message(message)

    def _sync_success(self, config_path):
        try:

            engine = sgtk.platform.current_engine()
            # Phase 4: Find the interpreter and launch it.
            path_to_python = sgtk.get_python_interpreter_for_config(config_path)

            # startup server pipe to listen
            engine.startup_rpc()

            core_python = os.path.join(
                config_path,
                "install", "core", "python"
            )

            # pickle up the info needed to bootstrap the project python
            desktop_data = {
                "core_python_path": core_python,
                "config_path": config_path,
                "project": self.current_project,
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

            self.project_overlay.report_progress(
                self._LAUNCHING_PYTHON_RATIO,
                "Launching Python subprocess (%s)" % path_to_python
            )
            log.info("--- launching python subprocess (%s)" % path_to_python)
            engine.execute_hook(
                "hook_launch_python",
                project_python=path_to_python,
                pickle_data_path=pickle_data_file,
                utilities_module_path=utilities_module_path,
            )

            self._pop_dll_state()

            # and remember it for next time
            self._save_setting("project_id", self.current_project["id"], site_specific=True)
        except (TankInvalidInterpreterLocationError, TankFileDoesNotExistError) as e:
            log.exception("Problem locating interpreter file:")
            self.setup_new_os_widget.show()
            self.project_overlay.hide()
            return
        except Exception as e:
            self.log_exception("Unexpected error while launching Python:")
            self._launch_failed(str(e))

    def slide_view(self, new_page, from_direction="right"):
        offsetx = self.ui.stack.frameRect().width()
        offsety = self.ui.stack.frameRect().height()
        current_page = self.ui.stack.currentWidget()

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
            self.ui.stack.setCurrentWidget(new_page)
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
        if engine.startup_version:
            about = AboutScreen(parent=self, body="""
                <center>
                    App Version %s<br/>
                    Startup Version %s<br/>
                    Engine Version %s<br/>
                    Core Version %s
                </center>
            """ % (
                engine.app_version,
                engine.startup_version,
                engine.version,
                engine.sgtk.version)
            )
        else:
            about = AboutScreen(parent=self, body="""
                <center>
                    App Version %s<br/>
                    Engine Version %s<br/>
                    Core Version %s
                </center>
            """ % (
                engine.app_version,
                engine.version,
                engine.sgtk.version)
            )
        about.exec_()
