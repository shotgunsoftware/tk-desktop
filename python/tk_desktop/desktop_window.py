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

from PySide import QtGui
from PySide import QtCore

import sgtk
from sgtk.util import shotgun
from sgtk.platform import constants

from .ui import resources_rc
from .ui import desktop_window

from .login import ShotgunLogin
from .systray import SystrayWindow
from .preferences import Preferences
from .model_project import SgProjectModel
from .model_project import SgProjectModelProxy
from .delegate_project import SgProjectDelegate

try:
    from .extensions import osutils
except Exception:
    osutils = None

# import the shotgun_model module from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
overlay_widget = sgtk.platform.import_framework("tk-framework-shotgunutils", "overlay_widget")
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

        # setup the window
        self.ui = desktop_window.Ui_DesktopWindow()
        self.ui.setupUi(self)
        self.project_overlay = overlay_widget.ShotgunOverlayWidget(self.ui.project_commands)

        # setup systray behavior
        self.set_content_layout(self.ui.border_layout)
        self.set_drag_widgets([self.ui.header, self.ui.footer])

        self.systray_state_changed.connect(self.handle_systray_state_changed)
        QtGui.QApplication.instance().setQuitOnLastWindowClosed(False)

        # Setup header buttons
        button_states = [
            (self.ui.apps_button, True),
            (self.ui.inbox_button, False),
            (self.ui.my_tasks_button, False),
            (self.ui.versions_button, False),
        ]
        for (button, state) in button_states:
            button.setProperty("active", state)
            button.style().unpolish(button)
            button.style().polish(button)
            if not state:
                # do not show disabled interfaces
                button.hide()
        connection = ShotgunLogin.get_connection()

        # User menu
        ###########################
        user = ShotgunLogin.get_login()
        thumbnail_url = connection.find_one('HumanUser',
            [['id', 'is', user['id']]], ['image']).get('image')
        if thumbnail_url is not None:
            (_, thumbnail_file) = tempfile.mkstemp(suffix='.jpg')
            try:
                shotgun.download_url(connection, thumbnail_url, thumbnail_file)
                pixmap = QtGui.QPixmap(thumbnail_file)
                self.ui.user_button.setIcon(QtGui.QIcon(pixmap))
            finally:
                try:
                    os.remove(thumbnail_file)
                except Exception:
                    pass

        # populate user menu
        self.user_menu = QtGui.QMenu(self)
        self.user_menu.addAction(self.ui.actionPin_to_Menu)
        self.user_menu.addAction(self.ui.actionKeep_on_Top)
        self.user_menu.addAction(self.ui.actionSign_Out)
        self.user_menu.addSeparator()
        self.user_menu.addAction(self.ui.actionPreferences)
        self.user_menu.addAction(self.ui.actionQuit)
        QtGui.QApplication.instance().aboutToQuit.connect(self.handle_quit_action)

        self.ui.actionPin_to_Menu.triggered.connect(self.toggle_pinned)
        self.ui.actionKeep_on_Top.triggered.connect(self.toggle_keep_on_top)
        self.ui.actionSign_Out.triggered.connect(self.sign_out)
        self.ui.actionQuit.triggered.connect(self.handle_quit_action)
        self.ui.actionPreferences.triggered.connect(self.handle_preferences_action)

        self.ui.user_button.setMenu(self.user_menu)

        # load and initialize cached projects
        self._project_model = SgProjectModel(self, self.ui.projects)
        self._project_proxy = SgProjectModelProxy(self)

        # hook up sorting/filtering GUI
        self._project_proxy.sort_fields = [
            ('last_accessed_by_current_user', SgProjectModelProxy.DESCENDING),
            ('name', SgProjectModelProxy.ASCENDING),
        ]

        self._project_proxy.setSourceModel(self._project_model)
        self._project_proxy.setDynamicSortFilter(True)
        self._project_proxy.sort(0)
        self.ui.projects.setModel(self._project_proxy)

        # load and initialize cached recent projects
        self._recent_project_proxy = SgProjectModelProxy(self)
        self._recent_project_proxy.limit = 3
        self._recent_project_proxy.sort_fields = [
            ('last_accessed_by_current_user', SgProjectModelProxy.DESCENDING),
            ('name', SgProjectModelProxy.ASCENDING),
        ]
        self._recent_project_proxy.setSourceModel(self._project_model)
        self._recent_project_proxy.setDynamicSortFilter(True)
        self._recent_project_proxy.sort(0)
        self.ui.recent_projects.setModel(self._recent_project_proxy)

        # tell our project view to use a custom delegate to produce widgets
        self._project_delegate = \
            SgProjectDelegate(self.ui.projects, QtCore.QSize(120, 130))
        self.ui.projects.setItemDelegate(self._project_delegate)

        self._recent_project_delegate = \
            SgProjectDelegate(self.ui.recent_projects, QtCore.QSize(100, 100))
        self.ui.recent_projects.setItemDelegate(self._recent_project_delegate)

        # handle project selection change
        self._project_selection_model = self.ui.projects.selectionModel()
        self._project_selection_model.selectionChanged.connect(self._on_project_selection)
        self._recent_project_selection_model = self.ui.recent_projects.selectionModel()
        self._recent_project_selection_model.selectionChanged.connect(
            self._on_recent_project_selection)

        self.ui.all_projects_button.clicked.connect(self._on_all_projects_clicked)
        self.ui.actionProject_Filesystem_Folder.triggered.connect(
            self.on_project_filesystem_folder_triggered)

        # setup project search
        self._search_x_icon = QtGui.QIcon(":res/x.png")
        self._search_magnifier_icon = QtGui.QIcon(":res/search.png")
        self.ui.search_text.hide()
        self.ui.search_magnifier.hide()
        self.ui.search_button.setIcon(self._search_magnifier_icon)
        self.ui.search_frame.setProperty("collapsed", True)
        self.ui.search_frame.style().unpolish(self.ui.search_frame)
        self.ui.search_frame.style().polish(self.ui.search_frame)
        self.ui.search_frame.update()
        self.ui.search_button.clicked.connect(self.search_button_clicked)
        self.ui.search_text.textChanged.connect(self.search_text_changed)

        # recent projects shelf
        self.ui.project_arrow.clicked.connect(self.toggle_recent_projects_shelf)
        self.ui.project_icon.clicked.connect(self.toggle_recent_projects_shelf)
        self.ui.project_name.clicked.connect(self.toggle_recent_projects_shelf)

        self.project_carat_up = QtGui.QIcon(":res/up_carat.png")
        self.project_carat_down = QtGui.QIcon(":res/down_carat.png")
        self.down_arrow = QtGui.QIcon(":res/down_arrow.png")
        self.right_arrow = QtGui.QIcon(":res/right_arrow.png")

        self.toggle_recent_projects_shelf()

        self.clear_app_uis()

        self.ui.shotgun_button.clicked.connect(self.shotgun_button_clicked)
        self.ui.shotgun_arrow.clicked.connect(self.shotgun_button_clicked)

        self._project_model.thumbnail_updated.connect(self.handle_project_thumbnail_updated)

        self._load_settings()

    def _load_settings(self):
        engine = sgtk.platform.current_engine()
        connection = engine.shotgun
        site = connection.base_url

        settings = QtCore.QSettings(self.ORGANIZATION, self.APPLICATION)

        # site specific settings
        settings.beginGroup(site)
        try:
            self.__set_project_from_id(settings.value("project_id", 0))
        except Exception:
            pass
        self.move(settings.value("pos", QtCore.QPoint(200, 200)))
        settings.endGroup()

        # Force update so the project selection happens if the window is shown by default
        QtGui.QApplication.processEvents()

        # settings that apply across any instance (after site specific, so pinned can reset pos)
        try:
            self.state = settings.value("systray_state", self.STATE_PINNED)
        except Exception:
            self.state = self.STATE_PINNED

        self.set_on_top(settings.value("on_top", False))

        # restore hotkey
        (key, native_modifiers, native_key) = settings.value("activation_hotkey", (None, None, None))
        if key:
            shortcut = QtGui.QKeySequence(key)
            self.set_activation_hotkey(shortcut, native_modifiers, native_key)

    def _save_setting(self, key, value, site_specific):
        engine = sgtk.platform.current_engine()
        connection = engine.shotgun
        site = connection.base_url

        settings = QtCore.QSettings(self.ORGANIZATION, self.APPLICATION)

        if site_specific:
            settings.beginGroup(site)

        settings.setValue(key, value)
        settings.sync()

    ########################################################################################
    # Event handlers and slots
    def handle_project_thumbnail_updated(self, item):
        project = item.data(ShotgunModel.SG_DATA_ROLE)
        if self.current_project is None or project["id"] != self.current_project["id"]:
            # nothing needs updating
            return

        self.ui.project_icon.setIcon(item.icon())

    def handle_systray_state_changed(self, state):
        if state == self.STATE_PINNED:
            self.ui.actionPin_to_Menu.setText("Undock from Menu")
        elif state == self.STATE_WINDOWED:
            self.ui.actionPin_to_Menu.setText("Pin to Menu")
        self._save_setting("systray_state", state, site_specific=False)

    def handle_quit_action(self):
        # disconnect from the current proxy
        engine = sgtk.platform.current_engine()
        engine.disconnect_app_proxy()

        self._save_setting("pos", self.pos(), site_specific=True)

        self.close()
        QtGui.QApplication.instance().quit()

    def handle_hotkey_triggered(self):
        self.toggle_activate()

    def set_activation_hotkey(self, shortcut, native_modifiers, native_key):
        if osutils is None:
            return

        if shortcut.isEmpty():
            self._save_setting("activation_hotkey", ('', '', ''), False)
            if self.__activation_hotkey is not None:
                osutils.unregister_global_hotkey(self.__activation_hotkey)
                self.__activation_hotkey = None
        else:
            if self.__activation_hotkey is not None:
                osutils.unregister_global_hotkey(self.__activation_hotkey)
            self.__activation_hotkey = osutils.register_global_hotkey(native_modifiers, native_key, self.handle_hotkey_triggered)
            self._save_setting("activation_hotkey", (shortcut[0], native_modifiers, native_key), False)

    def handle_auto_start_changed(self, state):
        if osutils is None:
            return

        if state == QtCore.Qt.Checked:
            osutils.set_launch_at_login(True)
        if state == QtCore.Qt.Unchecked:
            osutils.set_launch_at_login(False)

    def handle_preferences_action(self):
        # create the dialog
        prefs = Preferences()

        # setup current prefs
        settings = QtCore.QSettings(self.ORGANIZATION, self.APPLICATION)
        (key, native_modifiers, native_key) = settings.value("activation_hotkey", (None, None, None))
        if key:
            shortcut = QtGui.QKeySequence(key)
            prefs.ui.hotkey.key_sequence = shortcut

        if osutils is not None:
            start_on_login = osutils.get_launch_at_login()
            if start_on_login:
                prefs.ui.auto_start_checkbox.setCheckState(QtCore.Qt.Checked)
            else:
                prefs.ui.auto_start_checkbox.setCheckState(QtCore.Qt.Unchecked)

        # handle changes
        prefs.ui.hotkey.key_sequence_changed.connect(self.set_activation_hotkey)
        prefs.ui.auto_start_checkbox.stateChanged.connect(self.handle_auto_start_changed)

        # and run it
        prefs.exec_()

    def search_button_clicked(self):
        if self.ui.search_frame.property("collapsed"):
            # expand
            # do not show the project menu for the time being
            # self.ui.project_button.hide()
            self.ui.search_text.show()
            self.ui.search_magnifier.show()
            self.ui.search_button.setIcon(self._search_x_icon)
            self.ui.search_frame.setProperty("collapsed", False)
            self.ui.search_text.setFocus(QtCore.Qt.MouseFocusReason)
        else:
            # collapse
            self.ui.search_text.hide()
            self.ui.search_magnifier.hide()

            # Force update to keep from seeing the button flash
            QtGui.QApplication.processEvents()

            self.ui.search_text.setText('')
            # do not show the project menu for the time being
            # self.ui.project_button.show()
            self.ui.search_button.setIcon(self._search_magnifier_icon)
            self.ui.search_frame.setProperty("collapsed", True)

        self.ui.search_frame.style().unpolish(self.ui.search_frame)
        self.ui.search_frame.style().polish(self.ui.search_frame)
        self.ui.search_frame.update()

    def search_text_changed(self, text):
        self._project_proxy.search_text = text

    def toggle_recent_projects_shelf(self):
        if self.ui.recents_shelf.isHidden():
            self.ui.recents_shelf.show()
            self.ui.project_arrow.setIcon(self.project_carat_up)

            self.ui.recents_shelf.adjustSize()
            QtGui.QApplication.processEvents()
        else:
            self.ui.recents_shelf.hide()
            self.ui.project_arrow.setIcon(self.project_carat_down)

    def on_project_filesystem_folder_triggered(self):
        engine = sgtk.platform.current_engine()
        engine.proxy.open_project_locations()

    def project_sort_triggered(self, action):
        button_label = " ".join(action.text().split(" ")[0:-1])
        self.ui.project_button.setText(button_label)

    def project_filter_triggered(self, action):
        raise NotImplementedError("ACTION: %s, GROUP %s" % (action.text(), action.parent()))

    def sign_out(self):
        ShotgunLogin.logout()
        self.hide()

        # shot the login dialog again
        login = ShotgunLogin.get_login()

        if login is not None:
            self.show()
        else:
            self.close()

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

    def _on_all_projects_clicked(self):
        self._project_selection_model.clear()
        self._recent_project_selection_model.clear()

        self.slide_view(self.ui.project_browser_page, "left")
        self.clear_app_uis()

        # remember that we are back at the browser
        self.current_project = None
        self._save_setting("project_id", 0, site_specific=True)

    def clear_app_uis(self):
        engine = sgtk.platform.current_engine()
        engine.clear_app_groups()

        # empty the project commands
        self.ui.project_commands.clear()

        # clear the project specific menu
        self.project_menu = QtGui.QMenu(self)
        self.project_menu.triggered.connect(self._on_project_menu_triggered)
        self.project_menu.addAction(self.ui.actionProject_Filesystem_Folder)
        self.ui.project_menu.setMenu(self.project_menu)
        self.__pipeline_configuration_separator = None

    def __populate_pipeline_configurations_menu(self, pipeline_configurations, selected):
        user = ShotgunLogin.get_login()

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
            for u in pc["users"]:
                if user["id"] == u["id"]:
                    extra_pcs.append(pc)
                    continue

        self.ui.configuration_frame.hide()

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
        # This isn't doable via the API yet
        pass

        # self._project_model.update_project_accessed_time(project)
        # self._project_proxy.invalidate()
        # self._recent_project_proxy.invalidate()

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

            if hasattr(model, 'mapToSource'):
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

    def __set_project_from_item(self, item):
        self.current_project = item.data(ShotgunModel.SG_DATA_ROLE)
        self._save_setting("project_id", self.current_project["id"], site_specific=True)

        # slide in the project specific view
        self.slide_view(self.ui.project_page, "right")
        self._project_selection_model.clear()

        # update the project icon
        self.ui.project_icon.setIcon(item.icon())
        self.ui.project_name.setText(item.data(SgProjectModel.DISPLAY_NAME_ROLE))

        # clear any selection in the recent projects
        self._recent_project_selection_model.clear()

        # launch the app proxy
        self.__launch_app_proxy_for_project(self.current_project)

        # and remember this project
        self._save_setting("project_id", self.current_project["id"], site_specific=True)

    def _on_recent_project_selection(self, selected, deselected):
        selected_indexes = selected.indexes()

        if len(selected_indexes) == 0:
            return

        # pull the Shotgun information for the project corresponding to this item
        proxy_model = selected_indexes[0].model()
        source_index = proxy_model.mapToSource(selected_indexes[0])
        item = source_index.model().itemFromIndex(source_index)

        # update the project icon
        self.ui.project_icon.setIcon(item.icon())
        self.ui.project_name.setText(item.data(SgProjectModel.DISPLAY_NAME_ROLE))

        # launch the app proxy
        project = item.data(ShotgunModel.SG_DATA_ROLE)
        self.__launch_app_proxy_for_project(project)

    def _on_project_menu_triggered(self, action):
        pc_id = action.property("project_configuration_id")

        if pc_id is not None:
            if pc_id == 0:
                pc_id = None
            self.__launch_app_proxy_for_project(self.current_project, pc_id)

    def __launch_app_proxy_for_project(self, project, pipeline_configuration_id=None):
        try:
            engine = sgtk.platform.current_engine()
            engine.log_debug("launch app proxy: %s" % project)

            # disconnect from the current proxy
            engine.disconnect_app_proxy()

            # clear the current gui
            self.clear_app_uis()
            self.project_overlay.start_spin()

            # trigger an update to the model to track this project access
            self.__set_project_just_accessed(project)
            QtGui.QApplication.instance().processEvents()

            platform_fields = {
                'darwin': 'mac_path',
                'linux': 'linux_path',
                'win32': 'windows_path',
            }
            path_field = platform_fields.get(sys.platform)

            if path_field is None:
                raise SystemError("Unsupported platform: %s" % sys.platform)

            filters = [
                ["project", "is", project],
            ]

            fields = [path_field, "users", "code"]

            connection = engine.shotgun
            pipeline_configurations = connection.find(
                'PipelineConfiguration',
                filters,
                fields=fields,
            )

            # Find the matching pipeline configuration to launch against
            pipeline_configuration = None
            for pc in pipeline_configurations:
                if pipeline_configuration_id is None and pc["code"] == constants.PRIMARY_PIPELINE_CONFIG_NAME:
                    pipeline_configuration = pc
                    break
                if pipeline_configuration_id is not None and pc["id"] == pipeline_configuration_id:
                    pipeline_configuration = pc
                    break;

            if pipeline_configuration is None:
                # If the Project has not been setup for Toolkit
                # call it an error until we implement the setup
                # project
                error = RuntimeError("No pipeline configuration found")
                engine.app_proxy_startup_error(error)
                return
            else:
                config_path = pipeline_configuration[path_field]

            # Now find out the appropriate python to launch
            current_platform = {
                'darwin': 'Darwin',
                'linux': 'Linux',
                'win32': 'Windows',
            }[sys.platform]

            current_config_path = config_path
            while True:
                # First see if we have a local configuration for which interpreter
                interpreter_config_file = os.path.join(
                    current_config_path, 'config', 'core', 'interpreter_%s.cfg' % current_platform)

                if os.path.exists(interpreter_config_file):
                    # Found the file that says where the interpreter is
                    with open(interpreter_config_file, "r") as f:
                        path_to_python = f.read().strip()
                        core_root = current_config_path

                    if not os.path.exists(path_to_python):
                        raise RuntimeError("Cannot find interpreter %s defined in "
                            "config file %s!" % (path_to_python, interpreter_config_file))

                    # found it
                    break

                # look for a parent config to see if it has an interpreter
                parent_config_file = os.path.join(
                    current_config_path, 'install', 'core', 'core_%s.cfg' % current_platform)

                if not os.path.exists(parent_config_file):
                    raise RuntimeError("invalid configuration, no parent or interpreter found at '%s'" % current_config_path)

                # Read the path to the parent configuration
                with open(parent_config_file, "r") as f:
                    current_config_path = f.read().strip()
        except Exception, error:
            parent = self.get_app_widget("___error")
            label = QtGui.QLabel("Error setting up engine environment\n\n%s" % error.message)

            label.setWordWrap(True)
            label.setMargin(15)
            index = parent.layout().count() - 1
            parent.layout().insertWidget(index, label)
            return

        # going to launch the configuration, update the project menu if needed
        self.__populate_pipeline_configurations_menu(pipeline_configurations, pipeline_configuration)

        (_, temp_bootstrap) = tempfile.mkstemp(suffix=".py")
        bootstrap_file = open(temp_bootstrap, "w")
        try:
            core_python = os.path.join(core_root, "install", "core", "python")

            # startup server pipe to listen
            engine.start_gui_server()
            server_pipe = engine.msg_server.pipe
            server_auth = engine.msg_server.authkey

            lines = [
                "import os",
                "import sys",
                "import traceback",
                "sys.path.append('%s')" % core_python,
                "try:",
                "    from PySide import QtGui",
                "    import sgtk",
                "    sgtk.util.append_path_to_env_var('PYTHONPATH', '%s')" % core_python,
                "    tk = sgtk.sgtk_from_path('%s')" % config_path,
                "    tk._desktop_data = {",
                "      'proxy_pipe': r'%s'," % server_pipe,
                "      'proxy_auth': '%s'," % server_auth,
                "    }",
                "    ctx = tk.context_from_entity('Project', %d)" % project['id'],
                "    engine = sgtk.platform.start_engine('tk-desktop', tk, ctx)",
                "    QtGui.QApplication.setStyle('cleanlooks')",
                "    app = QtGui.QApplication(sys.argv)",
                "    app.setStyleSheet(engine._get_standard_qt_stylesheet())",
                "    app.setQuitOnLastWindowClosed(False)",
                "    app.exec_()",
                "except Exception, e:",
                "    import cPickle as pickle",
                "    from multiprocessing.connection import Client",
                "    if sys.platform == 'win32':",
                "        family = 'AF_PIPE'",
                "    else:",
                "        family = 'AF_UNIX'",
                "    connection = Client(address=r'%s', family=family, authkey='%s')" % (server_pipe, server_auth),
                "    connection.send(pickle.dumps(('engine_startup_error',",
                "                  [e, traceback.format_exc()],",
                "                  {'__proxy_expected_return': False})))",
                "    connection.close()",
            ]
            bootstrap_file.write("\n".join(lines))
            bootstrap_file.close()

            self.current_project = project
            engine.log_info("--- launching python subprocess")
            engine.log_debug(" ---- %s %s" % (path_to_python, temp_bootstrap))

            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                subprocess.Popen([path_to_python, temp_bootstrap], startupinfo=startupinfo)
            else:
                subprocess.Popen([path_to_python, temp_bootstrap])
        finally:
            # clean up the bootstrap after a one second delay
            def remove_bootstrap():
                try:
                    os.remove(temp_bootstrap)
                except Exception:
                    pass
            QtCore.QTimer.singleShot(1000, remove_bootstrap)

    def slide_view(self, new_page, from_direction='right'):
        offsetx = self.ui.stack.frameRect().width()
        offsety = self.ui.stack.frameRect().height()
        current_page = self.ui.stack.currentWidget()

        new_page.setGeometry(0, 0, offsetx, offsety)

        if from_direction == 'left':
            offsetx = -offsetx

        curr_pos = new_page.pos()
        new_page.move(curr_pos.x()+offsetx, curr_pos.y())
        new_page.show()
        new_page.raise_()

        anim_old = QtCore.QPropertyAnimation(current_page, "pos", self)
        anim_old.setDuration(500)
        anim_old.setStartValue(QtCore.QPoint(curr_pos.x(), curr_pos.y()))
        anim_old.setEndValue(QtCore.QPoint(curr_pos.x()-offsetx, curr_pos.y()))
        anim_old.setEasingCurve(QtCore.QEasingCurve.OutBack)

        anim_new = QtCore.QPropertyAnimation(new_page, "pos", self)
        anim_new.setDuration(500)
        anim_new.setStartValue(QtCore.QPoint(curr_pos.x()+offsetx, curr_pos.y()))
        anim_new.setEndValue(QtCore.QPoint(curr_pos.x(), curr_pos.y()))
        anim_new.setEasingCurve(QtCore.QEasingCurve.OutBack)

        anim_group = QtCore.QParallelAnimationGroup(self)
        anim_group.addAnimation(anim_old)
        anim_group.addAnimation(anim_new)

        def slide_finished():
            self.ui.stack.setCurrentWidget(new_page)
        anim_group.finished.connect(slide_finished)
        anim_group.start()

    def shotgun_button_clicked(self):
        connection = ShotgunLogin.get_connection()
        url = connection.base_url
        if self.current_project is not None:
            url = "%s/detail/Project/%d" % (url, self.current_project['id'])

        QtGui.QDesktopServices.openUrl(url)
