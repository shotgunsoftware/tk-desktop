# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import itertools
import sgtk

from tank.platform.qt import QtGui
from sgtk.platform import get_logger

log = get_logger(__name__)


class ProjectMenu(object):
    """
    Encapsulate specific functionality relating of the project menu.
    This class was created to lighten the `DesktopWindow` class.
    """
    def __init__(self, parent):
        """
        Initialise a `ProjectMenu` instance with a reference to it's parent object:
        a DesktopWindow instance
        :param parent: A reference to a `DesktopWindow` instance.
        """
        self._parent = parent
        self._project_menu = None
        self._pipeline_configuration_separator = None

    def add(self, action):
        """
        Add an child item to the menu (QAction)
        :param action: A valid QAction object
        """
        self._project_menu.insertAction(self._pipeline_configuration_separator, action)

    def reset(self):
        """
        Clears the project specific related QT menu and add basic menu actions
        and pipeline configuration section divider.
        """
        if self._project_menu:
            self._pipeline_configuration_separator = None
            self._project_menu.clear()

        self._project_menu = QtGui.QMenu(self._parent)

        self._project_menu.aboutToShow.connect(self._on_project_menu_about_to_show)
        self._project_menu.triggered.connect(self._on_project_menu_triggered)
        self._parent.ui.actionProject_Filesystem_Folder.setVisible(True)
        self._project_menu.addAction(self._parent.ui.actionProject_Filesystem_Folder)
        self._parent.ui.project_menu.setMenu(self._project_menu)

        # Add a section separator that will be above the pipeline configurations.
        # The context menu actions will be inserted above this saparator.
        self._pipeline_configuration_separator = self._project_menu.addSeparator()

    def clear_actions(self):
        """
        Clears actions from the project menu but keeps pipeline configurations if any
        """
        actions = self._project_menu.actions()

        # Loop through actions and delete the ones listed before the separator
        for action in actions:
            # Do not delete the Jump To Filesystem menu. This one is hidden on demand instead.
            if action == self._parent.ui.actionProject_Filesystem_Folder:
                continue

            if action == self._pipeline_configuration_separator:
                # Found the separator, entering the pipeline
                # config section, stop deleting items
                break

            self._project_menu.removeAction(action)

    def populate_pipeline_configurations_menu(self, pipeline_configurations, selected):
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

        # Build the configuration section header.
        label = QtGui.QLabel("CONFIGURATION")
        label.setObjectName("project_menu_configuration_label")
        action = QtGui.QWidgetAction(self._parent)
        action.setDefaultWidget(label)
        self._project_menu.addAction(action)
        pipelineConfigsMenuGroup = QtGui.QActionGroup(self._parent)
        pipelineConfigsMenuGroup.setExclusive(True)
        # Group every sandboxes by their name and add pipelines one at a time
        for pc_name, pc_group in itertools.groupby(pipeline_configurations, lambda x: x["name"]):
            self._add_pipeline_group_to_menu(pipelineConfigsMenuGroup, list(pc_group), selected)

    def _add_pipeline_group_to_menu(self, parent_action_group, pc_group, selected):
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

            action = self._project_menu.addAction(unique_pc_name)
            action.setActionGroup(parent_action_group)
            action.setCheckable(True)
            action.setProperty("project_configuration_id", pc["id"])

            # If this pipeline is the one that was selected, mark it in the
            # menu and update the configuration name widget.
            if selected and selected["id"] == pc["id"]:
                action.setChecked(True)
                self._parent.ui.configuration_name.setText(unique_pc_name)

                # If we haven't picked a primary, show the sandbox header.
                if not self._parent._is_primary_pc(pc):
                    self._parent.ui.configuration_frame.show()

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
        self._parent.ui.actionProject_Filesystem_Folder.setVisible(has_project_locations)

    def _on_project_menu_triggered(self, action):
        """
        Called just after user has selected a project menu option or pipeline configuration

        Forwards to `parent` so the `__launch_app_proxy_for_project` private methods
        can proceed with setting up project and request ui update as required.

        NOTE: The parent version of the this method only acts on a pipeline configuration choice.

        :param action: a QAction as selected by user.
        """
        self._parent._on_project_menu_triggered(action)
