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

from tank.platform.qt import QtCore, QtGui

import sgtk
from sgtk.util import shotgun
from sgtk import util
from sgtk.platform import constants
from tank_vendor import shotgun_authentication as sg_auth
from sgtk import pipelineconfig_utils

from .ui import resources_rc
from .ui import desktop_window

from .console import Console
from .console import ConsoleLogHandler
from .systray import SystrayWindow
from .about_screen import AboutScreen
from .setup_project import SetupProject
from .setup_new_os import SetupNewOS
from .project_model import SgProjectModel
from .project_model import SgProjectModelProxy
from .project_delegate import SgProjectDelegate
from .update_project_config import UpdateProjectConfig

from .project_commands_model import ProjectCommandModel
from .project_commands_model import ProjectCommandProxyModel
from .project_commands_widget import ProjectCommandDelegate

try:
    from .extensions import osutils
except Exception:
    osutils = None

# import our frameworks
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
overlay_widget = sgtk.platform.import_framework("tk-framework-qtwidgets", "overlay_widget")
settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")

ShotgunModel = shotgun_model.ShotgunModel


class DesktopWindow(SystrayWindow):
    """ Dockable window for the Shotgun system tray """

    ORGANIZATION = "Shotgun Software"
    APPLICATION = "tk-desktop"

    def __init__(self, parent=None):
        SystrayWindow.__init__(self, parent)

        # initialize member variables
        self.current_project = None
        self.__activation_hotkey = None
        self.__pipeline_configuration_separator = None
        self._settings_manager = settings.UserSettings(sgtk.platform.current_bundle())

        # setup the window
        self.ui = desktop_window.Ui_DesktopWindow()
        self.ui.setupUi(self)
        self.project_overlay = overlay_widget.ShotgunOverlayWidget(self.ui.project_commands)
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

        engine = sgtk.platform.current_engine()

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
        about_action = self.user_menu.addAction("About...")
        self.user_menu.addSeparator()
        self.user_menu.addAction(self.ui.actionSign_Out)
        self.user_menu.addAction(self.ui.actionQuit)

        name_action.triggered.connect(self.open_site_in_browser)
        url_action.triggered.connect(self.open_site_in_browser)
        about_action.triggered.connect(self.handle_about)

        QtGui.QApplication.instance().aboutToQuit.connect(self.handle_quit_action)

        self.ui.actionPin_to_Menu.triggered.connect(self.toggle_pinned)
        self.ui.actionKeep_on_Top.triggered.connect(self.toggle_keep_on_top)
        self.ui.actionShow_Console.triggered.connect(self.__console.show_and_raise)
        self.ui.actionRefresh_Projects.triggered.connect(self.handle_project_refresh_action)
        self.ui.actionSign_Out.triggered.connect(self.sign_out)
        self.ui.actionQuit.triggered.connect(self.handle_quit_action)

        self.ui.user_button.setMenu(self.user_menu)

        # Initialize the model to track project commands
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

        self._load_settings()

    def _load_settings(self):
        # last window position
        pos = self._settings_manager.retrieve("pos", QtCore.QPoint(200, 200), self._settings_manager.SCOPE_SITE)
        self.move(pos)
        # Force update so the project selection happens if the window is shown by default
        QtGui.QApplication.processEvents()

        # load up last project
        project_id = self._settings_manager.retrieve("project_id", 0, self._settings_manager.SCOPE_SITE)
        self.__set_project_from_id(project_id)

        # settings that apply across any instance (after site specific, so pinned can reset pos)
        self.set_on_top(self._settings_manager.retrieve("on_top", False))

        # always start pinned and hidden
        self.state = self.STATE_PINNED

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
                engine = sgtk.platform.current_engine()
                engine.log_warning('Could not push DllDirectory under Windows.')

    def _pop_dll_state(self):
        '''
        Pop the previously pushed DLL Directory
        '''
        if sys.platform == "win32":
            try:
                import win32api
                win32api.SetDllDirectory(self._previous_dll_directory)
            except StandardError:
                engine = sgtk.platform.current_engine()
                engine.log_warning('Could not restore DllDirectory under Windows.')

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

    def sign_out(self):
        engine = sgtk.platform.current_engine()

        try:
            sg_auth.ShotgunAuthenticator().clear_default_user()
            if engine.uses_legacy_authentication():
                engine.create_legacy_login_instance().logout()
        except Exception:
            # if logout raises an exception, just log and don't crash
            engine.log_exception("Error logging out.")

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

    def _handle_project_data_changed(self):
        self._project_selection_model.clear()
        self._project_proxy.invalidate()
        self._project_proxy.sort(0)

    def _on_back_to_projects_clicked(self):
        """
        Invoked when the user leaves a project.
        """
        engine = sgtk.platform.current_engine()
        engine.site_comm.shut_down()

        self._project_selection_model.clear()
        self._project_proxy.invalidate()
        self._project_proxy.sort(0)

        self.slide_view(self.ui.project_browser_page, "left")

        # remember that we are back at the browser
        self.current_project = None
        self._save_setting("project_id", 0, site_specific=True)

        # We switching back to the project list, so need to show the
        # "Refresh Projects" once again.
        self.ui.actionRefresh_Projects.setVisible(True)

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
        primary_pc = None
        extra_pcs = []
        for pc in pipeline_configurations:
            # track primary separate
            if pc["code"] == constants.PRIMARY_PIPELINE_CONFIG_NAME:
                primary_pc = pc
                continue

            # add shared pcs
            if not pc["users"]:
                extra_pcs.append(pc)
                continue

            # add pcs for this user
            for user in pc["users"]:
                if self._current_user_id == user["id"]:
                    extra_pcs.append(pc)
                    continue

        if not extra_pcs:
            # only one configuration choice
            return

        # Show configuration frame, add a separator, the primary config and then the rest
        self.__pipeline_configuration_separator = self.project_menu.addSeparator()

        label = QtGui.QLabel("CONFIGURATION")
        label.setObjectName("project_menu_configuration_label")
        action = QtGui.QWidgetAction(self)
        action.setDefaultWidget(label)
        self.project_menu.addAction(action)

        action = self.project_menu.addAction(primary_pc["code"])
        action.setCheckable(True)
        action.setProperty("project_configuration_id", 0)
        if selected["id"] == primary_pc["id"]:
            action.setChecked(True)
            self.ui.configuration_name.setText(primary_pc["code"])

        extra_pcs.sort(key=lambda pc: pc["code"])
        for pc in extra_pcs:
            action = self.project_menu.addAction(pc["code"])
            action.setCheckable(True)
            action.setProperty("project_configuration_id", pc["id"])
            if selected["id"] == pc["id"]:
                self.ui.configuration_frame.show()
                action.setChecked(True)
                self.ui.configuration_name.setText(pc["code"])

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
            engine.log_debug("Cannot get the availability of the project locations: %s" % exception)
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

    def __launch_app_proxy_for_project(self, project, pipeline_configuration_id=None):
        try:
            engine = sgtk.platform.current_engine()
            engine.log_debug("launching app proxy for project: %s" % project)

            # Make sure that not only the previous proxy is not running anymore
            # but that the UI has been cleared as well.
            engine = sgtk.platform.current_engine()
            engine.site_comm.shut_down()
            self.clear_app_uis()
            # Always hide the Refresh Projects menu item when launching the project engine
            # since no projects will be displayed in the app launcher pane.
            self.ui.actionRefresh_Projects.setVisible(False)

            self.project_overlay.start_spin()

            self.current_project = project

            # trigger an update to the model to track this project access
            self.__set_project_just_accessed(project)
            QtGui.QApplication.instance().processEvents()

            if sys.platform == "darwin":
                path_field = "mac_path"
            elif sys.platform == "win32":
                path_field = "windows_path"
            elif sys.platform.startswith("linux"):
                path_field = "linux_path"
            else:
                raise SystemError("Unsupported platform: %s" % sys.platform)

            filters = [
                ["project", "is", project],
            ]

            fields = [path_field, "users", "code"]

            connection = engine.shotgun
            pipeline_configurations = connection.find(
                "PipelineConfiguration",
                filters,
                fields=fields,
            )

            setting = "pipeline_configuration_for_project_%d" % project["id"]
            if pipeline_configuration_id is None:
                # Load up last accessed project if it hasn't been specified
                pipeline_configuration_id = self._load_setting(setting, 0, site_specific=True)
            else:
                # Save pipeline_configuration_id as last accessed
                self._save_setting(setting, pipeline_configuration_id, site_specific=True)

            # Find the matching pipeline configuration to launch against
            pipeline_configuration = None
            primary_pipeline_configuration = None
            for pc in pipeline_configurations:
                if pc["code"] == constants.PRIMARY_PIPELINE_CONFIG_NAME:
                    primary_pipeline_configuration = pc
                    if pipeline_configuration_id == 0:
                        pipeline_configuration = pc

                    if pipeline_configuration is not None:
                        break

                if pipeline_configuration_id != 0 and pc["id"] == pipeline_configuration_id:
                    pipeline_configuration = pc
                    if primary_pipeline_configuration is not None:
                        break

            if pipeline_configuration is None:
                if primary_pipeline_configuration is None:
                    # Show the Setup Project widget
                    self.setup_project_widget.project = project
                    self.setup_project_widget.show()
                    self.project_overlay.hide()
                    return
                else:
                    engine.log_warning(
                        "Pipeline configuration id %d not found, "
                        "falling back to primary." % pipeline_configuration_id)
                    pipeline_configuration = primary_pipeline_configuration

            # going to launch the configuration, update the project menu if needed
            self.__populate_pipeline_configurations_menu(pipeline_configurations, pipeline_configuration)

            config_path = pipeline_configuration[path_field]

            # Now find out the appropriate python to launch
            if sys.platform == "darwin":
                current_platform = "Darwin"
            elif sys.platform == "win32":
                current_platform = "Windows"
            elif sys.platform.startswith("linux"):
                current_platform = "Linux"
            else:
                raise RuntimeError("Unknown platform: %s." % sys.platform)

            if config_path is None:
                engine.log_error("No path set for %s on the Pipeline "
                                 "Configuration \"%s\" (id %d)." %
                                 (current_platform,
                                  pipeline_configuration["code"],
                                  pipeline_configuration_id))

                raise RuntimeError("The Toolkit configuration path has not\n"
                                   "been set for your operating system.")

            current_config_path = config_path
            while True:
                # First see if we have a local configuration for which interpreter
                interpreter_config_file = os.path.join(
                    current_config_path, "config", "core", "interpreter_%s.cfg" % current_platform)

                if os.path.exists(interpreter_config_file):
                    # Found the file that says where the interpreter is
                    with open(interpreter_config_file, "r") as f:
                        path_to_python = f.read().strip()
                        core_root = current_config_path

                    if not path_to_python or not os.path.exists(path_to_python):
                        # python not specified for this os, show the setup new os widget
                        engine.log_error("Cannot find interpreter '%s' defined in "
                                         "config file %s. Will show the special "
                                         "'no python' UI screen." % (path_to_python, interpreter_config_file))
                        self.setup_new_os_widget.show()
                        self.project_overlay.hide()
                        return

                    # found it
                    break

                # look for a parent config to see if it has an interpreter
                parent_config_file = os.path.join(
                    current_config_path, "install", "core", "core_%s.cfg" % current_platform)

                if not os.path.exists(parent_config_file):
                    engine.log_error("No parent or interpreter found at '%s'."
                                     % current_config_path)
                    raise RuntimeError("The Toolkit configuration path points\n"
                                       "to an invalid configuration.")

                # Read the path to the parent configuration
                with open(parent_config_file, "r") as f:
                    current_config_path = f.read().strip()
        except Exception, error:
            engine.log_exception(str(error))
            message = ("%s"
                       "\n\nTo resolve this, open Shotgun in your browser\n"
                       "and check the paths for this Pipeline Configuration."
                       "\n\nFor more details, see the console." % str(error))
            self.project_overlay.show_error_message(message)
            return

        core_python = os.path.join(core_root, "install", "core", "python")

        # startup server pipe to listen
        engine.startup_rpc()

        # pickle up the info needed to bootstrap the project python
        desktop_data = {
            "core_python_path": core_python,
            "config_path": config_path,
            "project": project,
            "proxy_data": {
                "proxy_pipe": engine.site_comm.server_pipe,
                "proxy_auth": engine.site_comm.server_authkey
            }
        }
        (_, pickle_data_file) = tempfile.mkstemp(suffix='.pkl')
        pickle.dump(desktop_data, open(pickle_data_file, "wb"))

        # update the values on the project updater in case they are needed
        self.update_project_config_widget.set_project_info(
            path_to_python, core_python, config_path, project)

        # get the path to the utilities module
        utilities_module_path = os.path.realpath(os.path.join(__file__, "..", "..", "utils", "bootstrap_utilities.py"))

        # Check if the pipeline configuration is login based.
        engine.check_login_based(core_root)
        # Make sure the credentials are refreshed so the background process
        # has no problem launching.
        engine.refresh_user_credentials()

        # Ticket 26741: Avoid having odd DLL loading issues on windows
        self._push_dll_state()

        engine.log_info("--- launching python subprocess (%s)" % path_to_python)
        engine.execute_hook(
            "hook_launch_python",
            project_python=path_to_python,
            pickle_data_path=pickle_data_file,
            utilities_module_path=utilities_module_path,
        )

        self._pop_dll_state()

        # and remember it for next time
        self._save_setting("project_id", self.current_project["id"], site_specific=True)

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
                pipelineconfig_utils.get_currently_running_api_version())
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
                pipelineconfig_utils.get_currently_running_api_version())
            )
        about.exec_()
