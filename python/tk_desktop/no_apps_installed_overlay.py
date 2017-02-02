# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import pprint

import sgtk

from sgtk.platform.qt import QtCore
from sgtk.platform.qt import QtGui

from .ui import no_apps_installed_overlay

shotgun_data = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_data")

class NoAppsInstalledOverlay(QtGui.QWidget):
    """
    Widget displayed in the desktop Window's project_commands wiget when no
    "button" commands are found for the current project. Displays site
    Software entity icons and a link to a Shotgun Support article detailing
    how to configure Software entities.
    """
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.ui = no_apps_installed_overlay.Ui_NoAppsInstalledOverlay()
        self.ui.setupUi(self)

        # Assign magic numbers and such
        self._icon_size = QtCore.QSize(64, 64)
        self._icon_layout_spacing = 5
        self._icon_layout_stretch = 1
        self._icon_column_count = 4
        self._config_link_color = "#0000FF"
        self._config_link_text = "here"

        # Hide this widget by default.
        self.setVisible(False)

    def build_software_entity_config_widget(self, project):
        """
        Query Shotgun for a list of Software images to display and
        set the Software configuration link value

        :param project: Current Shotgun Project instance (dict)
        """
        # Get a handle to the current engine, which is primarily
        # used for logging purposes.
        engine = sgtk.platform.current_engine()
        self._load_software_icons(engine, project)
        self._set_configuration_link(engine)

    def _clear_icons(self):
        """
        Remove exising icons to prepare for new icons.
        This is necessary because the list of icons may not
        be the same from project to project, or can change
        if Software entities are reconfigured in Shotgun.
        """
        while self.ui.icon_rows.count():
            qt_layout = self.ui.icon_rows.takeAt(0)
            while qt_layout.count():
                qt_item = qt_layout.takeAt(0)
                qt_widget = qt_item.widget()
                if qt_widget is not None:
                    qt_widget.deleteLater()
            qt_layout.deleteLater()

    def _load_software_icons(self, engine, project=None):
        """
        Displays thumbnails downloaded from Software entities for a
        specified Project in the ui.icon_rows layout.

        :param engine: Toolkit engine instance.
        :param project: Shotgun Project instance or None
        """
        # Get the list of Software entities for this Project from Shotgun
        sg_softwares = self._get_sg_software_entities(engine, project)
        if not sg_softwares:
            return

        # Clear out any existing icons
        self._clear_icons()

        # Arrange the icons in a grid with self._icon_column_count
        # columns and N rows based on the total number of icons
        col_num = 0
        icon_row_layout = None
        last_software = len(sg_softwares) - 1
        for i in range(len(sg_softwares)):
            # Download the thumbnail source file from Shotgun, which preserves
            # transparency and alpha values.
            sg_icon = shotgun_data.ShotgunDataRetriever.download_thumbnail_source(
                sg_softwares[i]["type"], sg_softwares[i]["id"], engine
            )

            if not sg_icon:
                engine.logger.warning(
                    "Could not download thumbnail for %s entity [%s]" %
                    (sg_softwares[i]["type"], sg_softwares[i]["id"])
                )
                continue

            # Create a label and set its pixmap to the downloaded
            # thumbnail scaled to self._icon_size.
            qt_label = QtGui.QLabel(self)
            qt_label.setPixmap(
                QtGui.QPixmap(sg_icon).scaled(
                    self._icon_size, mode=QtCore.Qt.SmoothTransformation
                )
            )

            # Add the label to this widget, constructing necessary
            # layouts as needed.
            if col_num == 0:
                icon_row_layout = QtGui.QHBoxLayout()
                icon_row_layout.setSpacing(self._icon_layout_spacing)
                icon_row_layout.addStretch(self._icon_layout_stretch)

            icon_row_layout.addWidget(qt_label)
            col_num += 1
            if col_num == self._icon_column_count or i == last_software:
                icon_row_layout.addStretch(self._icon_layout_stretch)
                self.ui.icon_rows.addLayout(icon_row_layout)
                col_num = 0

        # Set the spacing on the parent layout so the icons appear
        # evenly spaced out.
        self.ui.icon_rows.setSpacing(self._icon_layout_spacing)

    def _set_configuration_link(self, engine):
        """
        Update the ui.link_label with the appropriate link to open
        directing the user to a Shotgun Support article explaining
        how to configure Software entities for a site.

        :param engine: Toolkit engine instance to retrieve link from
        """
        # Get the link from the specified engine.
        config_link = engine.get_setting("software_entity_config_link")
        if not config_link:
            engine.logger.debug(
                "No 'software_entity_config_link' specified for engine %s." %
                engine.name
            )
            return

        # Add the link to the link_label text
        link_text = ("<a href='%s'><span style='color: %s;'>%s</span></a>" %
                    (config_link, self._config_link_color, self._config_link_text))
        current_text = self.ui.link_label.text()
        if link_text not in current_text:
            # Updae the ui.link_label with the engine's doc link and make
            # sure it's clickable.
            self.ui.link_label.setText(current_text.replace(
                self._config_link_text, link_text
            ))
            self.ui.link_label.setOpenExternalLinks(True)

    def _get_sg_software_entities(self, engine, project=None):
        """
        Retrieve Software entities from Shotgun for the specified Project.

        :param engine: Toolkit engine instance
        :param project: Shotgun Project instance.
        """
        # @TODO: Remove this when Software entities are native.
        sw_entity = engine.get_setting("sg_software_entity")
        if not sw_entity:
            engine.logger.warning("Unable to determine Software CustomEntity.")
            return

        # Use filters to retrieve Software entities that match specified
        # Project, HumanUser, and Group restrictions. The filter specification
        # is broken up to allow for empty Project and or HumanUser values in
        # the current context. The resolved filter can be found in the log
        # files with "debug_logging" toggled on.

        # First, make sure to only include active entries with assigned icons.
        sw_filters = [
            ["sg_status_list", "is", "act"],
            ["image", "is_not", None],
        ]

        # Next handle Project restrictions. Always include Software entities
        # that have no Project restrictions.
        project_filters = [["sg_projects", "is", None]]
        current_project = project or engine.context.project
        if current_project:
            # If a Project is defined in the current context, retrieve
            # Software entities that have either no Project restrictions OR
            # include the context Project as a restriction.
            project_filters.append(
                ["sg_projects", "in", current_project],
            )
            sw_filters.append({
                "filter_operator": "or",
                "filters": project_filters,
            })
        else:
            # If no context Project is defined, then only retrieve
            # Software entities that do not have any Project restrictions.
            sw_filters.extend(project_filters)

        # Now Group and User restrictions. Always retrieve Software entities
        # that have no Group or User restrictions.
        current_user = engine.context.user
        user_group_filters = [
            ["sg_user_restrictions", "is", None],
            ["sg_group_restrictions", "is", None],
        ]
        if current_user:
            # If a current User is defined, then retrieve Software
            # entities that either have A) no Group AND no User
            # restrictions OR B) current User is included in Group
            # OR User restrictions.
            sw_filters.append({
                "filter_operator": "or",
                "filters": [
                    {"filter_operator": "and",
                     "filters": user_group_filters},
                    {"filter_operator": "or",
                     "filters": [
                        ["sg_user_restrictions", "in", current_user],
                        ["sg_group_restrictions.Group.users", "in", current_user],
                     ]},
                ]
            })
        else:
            # If no User is defined, then only retrieve Software
            # entities that do not have any Group or User restrictions.
            sw_filters.extend(user_group_filters)

        # Get the list of matching Software entities
        sg_softwares = engine.shotgun.find(sw_entity, sw_filters)
        engine.logger.debug("Found [%d] Software entities matching filters: %s" %
            (len(sg_softwares), pprint.pformat(sw_filters))
        )
        if not sg_softwares:
            engine.logger.warning("No Software entities found in Shotgun.")
            return

        return sg_softwares
