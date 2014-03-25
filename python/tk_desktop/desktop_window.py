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

from .systray import SystrayWindow
from .model_project import SgProjectModel
from .model_project import SgProjectModelProxy
from .delegate_project import SgProjectDelegate

# import the shotgun_model module from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunModel = shotgun_model.ShotgunModel


class DesktopWindow(SystrayWindow):
    """ Dockable window for the Shotgun system tray """
    def __init__(self, parent=None):
        SystrayWindow.__init__(self, parent)
        import shotgun_desktop.login

        # initialize member variables
        self.current_project = None
        self.current_sub_python = None

        # setup the window
        self.ui = desktop_window.Ui_DesktopWindow()
        self.ui.setupUi(self)

        # setup systray behavior
        (_, anchor_height, _, _) = self.ui.border_layout.getContentsMargins()
        self.set_window_anchor_height(anchor_height)
        self.set_drag_widgets([self.ui.header, self.ui.footer])
        self.systray_state_changed.connect(self.handle_systray_state_changed)

        # start off pinned
        self.state = self.STATE_PINNED

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
            button.update()

        connection = shotgun_desktop.login.ShotgunLogin.get_connection()

        # User menu
        ###########################

        # grab user thumbnail
        user = shotgun_desktop.login.ShotgunLogin.get_login()
        thumbnail_url = connection.find_one('HumanUser',
            [['id', 'is', user['id']]], ['image']).get('image')
        if thumbnail_url is not None:
            (_, thumbnail_file) = tempfile.mkstemp(suffix='.jpg')
            try:
                shotgun.download_url(connection, thumbnail_url, thumbnail_file)
                pixmap = QtGui.QPixmap(thumbnail_file)
                self.ui.user_button.setIcon(QtGui.QIcon(pixmap))
            finally:
                os.remove(thumbnail_file)

        # populate user menu
        self.user_menu = QtGui.QMenu(self)
        self.user_menu.addAction(self.ui.actionPin_to_Menu)
        self.user_menu.addAction(self.ui.actionKeep_on_Top)
        self.user_menu.addAction(self.ui.actionSign_Out)
        self.user_menu.addSeparator()
        self.user_menu.addAction(self.ui.actionQuit)

        self.ui.actionQuit.triggered.connect(QtGui.QApplication.instance().quit)
        self.ui.actionPin_to_Menu.triggered.connect(self.toggle_pinned)
        self.ui.actionSign_Out.triggered.connect(self.sign_out)
        self.ui.actionKeep_on_Top.triggered.connect(self.toggle_keep_on_top)

        self.ui.user_button.setMenu(self.user_menu)

        # Project menu
        ###########################

        status_schema = connection.schema_field_read('Project', 'sg_status')['sg_status']
        status_values = status_schema['properties']['valid_values']['value']

        self.project_menu = QtGui.QMenu(self)
        self.project_menu.addAction(self.ui.actionAll_Projects)
        self.project_menu.addAction(self.ui.actionFavorite_Projects)
        self.project_menu.addAction(self.ui.actionRecent_Projects)
        self.project_menu.addSeparator()

        self.project_filter_options = QtGui.QActionGroup(self)
        self.project_filter_options.setExclusive(False)

        for value in status_values:
            action = QtGui.QAction(value, self.project_filter_options)
            action.setCheckable(True)
            action.setChecked(True)
            self.project_menu.addAction(action)
        self.project_filter_options.triggered.connect(self.project_filter_triggered)

        self.project_sort_options = QtGui.QActionGroup(self)
        self.project_sort_options.addAction(self.ui.actionAll_Projects)
        self.project_sort_options.addAction(self.ui.actionFavorite_Projects)
        self.project_sort_options.addAction(self.ui.actionRecent_Projects)

        self.project_sort_options.triggered.connect(self.project_sort_triggered)
        self.ui.project_button.setMenu(self.project_menu)

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

    def __del__(self):
        SystrayWindow.__del__(self)
        self.current_sub_python.terminate()

    ########################################################################################
    # Event handlers and slots
    def handle_systray_state_changed(self, state):
        if state == self.STATE_PINNED:
            self.ui.actionPin_to_Menu.setText("Undock from Menu")
        elif state == self.STATE_WINDOWED:
            self.ui.actionPin_to_Menu.setText("Pin to Menu")

    def search_button_clicked(self):
        if self.ui.search_frame.property("collapsed"):
            # expand
            self.ui.project_button.hide()
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
            self.ui.project_button.show()
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
        print "ACTION: %s" % action.text()
        print "GROUP: %s" % action.parent()

    def sign_out(self):
        raise NotImplementedError()

    def toggle_keep_on_top(self):
        flags = self.windowFlags()
        visible = self.isVisible()

        if flags & QtCore.Qt.WindowStaysOnTopHint:
            self.setWindowFlags(flags & ~QtCore.Qt.WindowStaysOnTopHint)
            self.ui.actionKeep_on_Top.setChecked(False)
        else:
            self.setWindowFlags(flags | QtCore.Qt.WindowStaysOnTopHint)
            self.ui.actionKeep_on_Top.setChecked(True)

        if visible:
            self.show()

    ########################################################################################
    # project view
    def get_app_widget(self, namespace=None):
        return self.ui.app_guis

    def get_app_menu(self):
        return self.project_menu

    def _on_all_projects_clicked(self):
        self._project_selection_model.clear()
        self._recent_project_selection_model.clear()

        self.slide_view(self.ui.project_browser_page, 'left')
        self.clear_app_uis()

    def clear_app_uis(self):
        engine = sgtk.platform.current_engine()
        engine.clear_app_groups()

        if self.current_sub_python is not None:
            self.current_sub_python.terminate()
            self.current_sub_python = None

        self.current_project = None

        # clear the project specific guis
        app_widget = self.get_app_widget()
        app_widget.setUpdatesEnabled(False)

        # empty the layout
        app_gui = app_widget.layout().takeAt(0)
        while app_gui is not None:
            widget = app_gui.widget()
            if widget is not None:
                widget.hide()
            app_widget.layout().removeItem(app_gui)
            app_gui = app_widget.layout().takeAt(0)

        # add the stretch back in
        self.ui.app_guis.layout().addStretch()

        app_widget.layout().invalidate()
        app_widget.setUpdatesEnabled(True)

        # clear the project specific menu
        self.project_menu = QtGui.QMenu(self)
        self.project_menu.addAction(self.ui.actionProject_Filesystem_Folder)
        self.ui.project_menu.setMenu(self.project_menu)

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

        # slide in the project specific view
        self.slide_view(self.ui.project_page, 'right')
        self._project_selection_model.clear()

        proxy_model = selected_indexes[0].model()
        source_index = proxy_model.mapToSource(selected_indexes[0])
        item = source_index.model().itemFromIndex(source_index)
        project = item.data(ShotgunModel.SG_DATA_ROLE)

        # update the project icon
        self.ui.project_icon.setIcon(item.icon())
        self.ui.project_name.setText(item.data(SgProjectModel.DISPLAY_NAME_ROLE))

        # now select on the recent projects view if it is in view
        index = self._recent_project_proxy.mapFromSource(source_index)
        if index is not None and index.isValid():
            # let the selection in the recent projects drive creation of
            # the app proxy
            self._recent_project_selection_model.select(
                index, self._recent_project_selection_model.Select)
        else:
            self._recent_project_selection_model.clear()
            # launch the app proxy
            self.__launch_app_proxy_for_project(project)

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

    def __launch_app_proxy_for_project(self, project):
        import shotgun_desktop.paths

        self.clear_app_uis()

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
            ["code", "is", constants.PRIMARY_PIPELINE_CONFIG_NAME],
            ["project", "is", project],
        ]

        fields = [path_field, 'users']

        engine = sgtk.platform.current_engine()
        connection = engine.shotgun
        pipeline_configuration = connection.find_one(
            'PipelineConfiguration',
            filters,
            fields=fields,
        )

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
            'win32': 'Windows,'
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
                raise RuntimeError("invalid configuration, no local interpreter or parent config")

            # Read the path to the parent configuration
            with open(parent_config_file, "r") as f:
                current_config_path = f.read().strip()

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
                "from PySide import QtGui",
                "sys.path.append('%s')" % core_python,
                "import sgtk",
                "sgtk.util.append_path_to_env_var('PYTHONPATH', '%s')" % core_python,
                "try:",
                "    tk = sgtk.sgtk_from_path('%s')" % config_path,
                "    tk._desktop_data = {",
                "      'proxy_pipe': '%s'," % server_pipe,
                "      'proxy_auth': '%s'," % server_auth,
                "    }",
                "    ctx = tk.context_from_entity('Project', %d)" % project['id'],
                "    engine = sgtk.platform.start_engine('tk-desktop', tk, ctx)",
                "    app = QtGui.QApplication(sys.argv)",
                "    app.exec_()",
                "except Exception, e:",
                "    import cPickle as pickle",
                "    from multiprocessing.connection import Client",
                "    connection = Client(address='%s', family='AF_UNIX', authkey='%s')" % (server_pipe, server_auth),
                "    connection.send(pickle.dumps(('engine_startup_error', [e], {})))",
                "    connection.close()",
            ]
            bootstrap_file.write("\n".join(lines))
            bootstrap_file.close()

            self.current_project = project
            engine.log_info("--- launching python subprocess")
            self.current_sub_python = subprocess.Popen([path_to_python, temp_bootstrap])
        finally:
            # clean up the bootstrap after a one second delay
            def remove_bootstrap():
                os.remove(temp_bootstrap)
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
        import shotgun_desktop.login

        connection = shotgun_desktop.login.ShotgunLogin.get_connection()
        url = connection.base_url
        if self.current_project is not None:
            url = "%s/detail/Project/%d" % (url, self.current_project['id'])

        QtGui.QDesktopServices.openUrl(url)
