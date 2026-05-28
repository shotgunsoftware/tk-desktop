# Copyright (c) 2025 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class FlowDesktopFileCollector(HookBaseClass):
    """
    Collector that operates on the Flow Production Tracking Desktop publish
    workflow. Should inherit from the basic collector hook in the
    ``tk-multi-publish2`` app. The collector setting for this hook should look
    something like this::

        collector: "{self}/collector.py:{engine}/tk-multi-publish2/flowam/collector.py"

    """

    def process_file(self, settings, parent_item, path):
        """
        Analyzes the given file or folder and creates publish items.
        Blocks DCC-specific files that must be published from within their applications.

        Args:
            settings (dict): Configured settings for this collector
            parent_item: Root item instance
            path: Path of the file

        Returns:
            The created file item, or None if path is a folder or blocked DCC file
        """

        # Check if this is a DCC file that should not be published from desktop
        file_info = self.parent.util.get_file_path_components(path)
        extension = file_info["extension"]

        # Define DCC file extensions that cannot be published from desktop
        # These files require their specific DCC application to be open for proper publishing
        dcc_extensions = [
            # Maya
            "ma",
            "mb",
            # Nuke
            "nk",
            "nkple",
            # Houdini
            "hip",
            "hipnc",
            "hiplc",
            # 3ds Max
            "max",
            # Hiero
            "hrox",
            # Photoshop
            "psd",
            "psb",
            # VRED
            "vpb",
            "vpe",
            "osb",
            # Alias
            "wire",
            # After Effects
            "aep",
            "aet",
        ]

        if extension in dcc_extensions:
            # Get the file type display name
            file_type = "Unknown"
            for display_name, type_info in self.common_file_info.items():
                if extension in type_info["extensions"]:
                    file_type = display_name
                    break

            # Log an error message that will be visible to the user
            self.logger.error(
                "Cannot publish {file_type} files from Desktop. "
                "Please publish from within the application instead.".format(
                    file_type=file_type
                ),
                extra={
                    "action_show_more_info": {
                        "label": "Learn More",
                        "text": (
                            "<b>DCC files must be published from within their application.</b><br><br>"
                            "Files like Maya scenes (.ma, .mb), Nuke scripts (.nk, .nkple), Houdini scenes "
                            "(.hip, .hipnc, .hiplc), 3ds Max scenes (.max), Photoshop images (.psd, .psb), "
                            "and other DCC-specific formats contain application-specific data that requires "
                            "the DCC to be open for proper publishing.<br><br>"
                            "The Desktop Publisher is designed for publishing rendered images, textures, "
                            "Alembic caches, and other standalone files."
                        ),
                    }
                },
            )
            return None

        return self._collect_file(parent_item, path)

    def process_current_session(self, settings, parent_item):
        """
        Collect publishable items for desktop publishing from the current session.

        This method performs the following:
        1. Captures the current app context and locks it to this publisher instance
        2. Reads the revision_id from environment variables (if publishing a new revision of an existing asset)
        3. Collects publishable items based on the desktop workflow

        Args:
            settings (dict): Configured settings for this collector
            parent_item: Root item instance
        """

        # Get app context and set it to the parent item of current publish session
        app_context = self.parent.context
        parent_item.context = app_context

        # Determine the appropriate env var based on context level
        task = parent_item.context.task
        revision_id_env_var = None

        if task:
            # Task-level context
            task_id = task["id"]
            revision_id_env_var = f"TK_FLOWAM_REVISION_ID_{task_id}"
        else:
            # Project-level context
            project = parent_item.context.project
            if project:
                project_id = project["id"]
                revision_id_env_var = f"TK_FLOWAM_REVISION_ID_PROJECT_{project_id}"

        # Capture revision_id from environment variable and store it on root item (parent_item)
        # so all child file items can access it via item.parent.properties. This identifies
        # the existing AM asset we're publishing new revisions to.
        if revision_id_env_var and revision_id_env_var in os.environ:
            revision_id = os.environ[revision_id_env_var]
            parent_item.properties["am_revision_id"] = revision_id

            context_type = "task" if task else "project"
            context_id = task["id"] if task else project["id"]
            self.logger.debug(
                f"Captured revision_id {revision_id} from environment variable for {context_type} {context_id}"
            )

            # Clean up environment variable after capturing
            os.environ.pop(revision_id_env_var)
            self.logger.debug(
                f"Cleaned up environment variable {revision_id_env_var} after capturing revision_id"
            )
