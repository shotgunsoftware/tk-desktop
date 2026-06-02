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
import pprint

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class DesktopFlowPublishPlugin(HookBaseClass):
    """
    Self-contained desktop publish plugin for Flow Asset Management integration.

    Subclasses ``publish_file.py`` directly via the hook chain::

        hook: "{self}/publish_file.py:{engine}/tk-multi-publish2/flowam/publish_to_flow.py"

    Handles the full desktop publish workflow: framework loading, project
    validation, revision validation, and publishing via
    ``create_generic_workfile`` (new asset) or ``publish_generic_revision``
    (existing asset) in the Flow AM SDK.

    The DCC counterpart lives in
    ``tk-multi-publish2/hooks/flowam/publish_to_flow.py``
    (``DccFlowPublishPlugin``). Shared logic (properties, ``publish``,
    ``finalize``, ``get_publish_user``) is duplicated between the two so
    each plugin can evolve independently across separate release cycles.
    When updating shared logic, apply the change to both files.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the plugin."""
        super().__init__(*args, **kwargs)
        self.flow_module = None
        self.sg_flow_am_id = None

    ############################################################################
    # standard publish plugin properties

    @property
    def icon(self):
        return os.path.join(self.disk_location, "icons", "flow.png")

    @property
    def name(self):
        return "Publish to Flow AM"

    @property
    def description(self):
        return """
        Publishes the file to Flow Production Tracking and Asset Manager. A <b>Publish</b> entry
        will be created in Flow Production Tracking which will include a reference
        to the file's current path on disk. Other users will be able to access the
        published file via the <b><a href='%s'>Loader</a></b> so long as they have
        access to the file's location on disk.

        <h3>Overwriting an existing publish</h3>
        A file can be published multiple times however only the most recent
        publish will be available to other users. Warnings will be provided
        during validation if there are previous publishes.
        """

    ############################################################################
    # standard publish plugin methods

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.

        Maya files (.ma/.mb) are rejected - Maya dependencies are not tracked
        in Flow AM from the desktop context.
        """
        path = item.get_property("path")
        if path is None:
            raise AttributeError("'PublishData' object has no attribute 'path'")

        ext = os.path.splitext(path)[-1].lower()
        if ext in [".ma", ".mb"]:
            self.logger.warning("Maya dependencies will not be tracked in Flow AM.")
            return {"accepted": False}

        # log the accepted file and display a button to reveal it in the fs
        self.logger.info(
            "File publisher plugin accepted: %s" % (path,),
            extra={"action_show_folder": {"path": path}},
        )

        return {"accepted": True}

    def validate(self, settings, item):
        """
        Validates project configuration, AM project ID, and (if present)
        revision asset type. Combines base project validation with desktop-
        specific revision validation - no super() call needed.
        """
        # FlowAM framework import
        # TODO: We have an issue on FPTR desktop where the `adsk` cannot be found
        flow_am_fw = self.load_framework("tk-framework-flowam_v1.x.x")
        self.flow_module = flow_am_fw.import_module("flow")

        publisher = self.parent

        # Get the project's sg_flow_am_id
        sg_flow_project_id = sgtk.platform.current_engine().context.project["id"]
        project = publisher.shotgun.find_one(
            "Project", [["id", "is", sg_flow_project_id]], ["sg_flow_am_id"]
        )
        self.sg_flow_am_id = project.get("sg_flow_am_id")
        if not self.sg_flow_am_id:
            self.logger.error(
                "Project {} has no sg_flow_am_id set. "
                "Please set the sg_flow_am_id field on the project.".format(
                    project["name"]
                )
            )
            return False

        self.logger.info("Validating AM Project ID")
        am = self.flow_module.asset_management
        project_valid, project_err = am.validate_project(self.sg_flow_am_id)
        if not project_valid:
            self.logger.error(
                f"No Flow project associated with current SG project: {project_err}"
            )
            return False

        # Desktop publishing: validate revision asset type if publishing to
        # an existing asset (revision_id present on parent item)
        revision_id = None
        if item.parent:
            revision_id = item.parent.properties.get("am_revision_id")

        if revision_id:
            asset_id = self.flow_module.data.Asset.get_asset_id(revision_id)
            is_generic_asset, error_msg = am.validate_generic_asset(asset_id)
            if not is_generic_asset:
                self.logger.error(
                    "Cannot publish new revision of this asset",
                    extra={
                        "action_show_more_info": {
                            "label": "Error Details",
                            "text": "<pre>" f"{error_msg}\n" "</pre>",
                        }
                    },
                )
                return False

        return True

    def publish(self, settings, item):
        """Publish the item to Flow AM."""
        try:
            pub_info = self._publish_to_flow(item)

            # Check if user cancelled (child process return None)
            if pub_info is None:
                raise self.parent.base_hooks.PublishCancelledException(
                    "User cancelled the publish to Flow AM."
                )
            self.logger.info("Publish to Flow AM successful")

            # Store publish info for downstream plugins (e.g., alembic derivative)
            item.properties["am_publish_info"] = pub_info
            item.properties["entity"] = item.context.entity or item.context.project
            item.properties["task"] = item.context.task

            self.logger.info("Publish registered!")
            self.logger.debug(
                "Flow AM Publish info...",
                extra={
                    "action_show_more_info": {
                        "label": "Flow AM Publish Info",
                        "tooltip": "Show the complete Flow AM Publish info",
                        "text": "<pre>%s</pre>" % (pprint.pformat(pub_info.__dict__),),
                    }
                },
            )
        except self.parent.base_hooks.PublishCancelledException:
            # Re-raise cancellation exception without logging as error
            # The dialog will handle this and show "Publish Cancelled"
            raise
        except Exception as e:
            self.logger.error(
                "Failed to publish to Flow AM",
                extra={
                    "action_show_more_info": {
                        "label": "Error Details",
                        "text": "<pre>" f"{e}\n" "</pre>",
                    }
                },
            )
            raise

    def finalize(self, settings, item):
        # Override base class no-op: Flow AM publishes do not produce
        # sg_publish_data, so the base finalize (which reads it) would fail.
        pass

    def get_publish_user(self, settings, item):
        """
        Get the user that will be associated with this publish.

        If publish_user is not defined as a ``property`` or ``local_property``,
        this method will return ``None``.

        :param settings: This plugin instance's configured settings
        :param item: The item to determine the publish template for

        :return: A user entity dictionary or ``None`` if not defined.
        """
        return item.context.user

    ############################################################################
    # protected methods

    def _publish_to_flow(self, item):
        """
        Delegates to ``_publish_revision`` or ``_create_new_asset`` depending
        on whether a revision ID is present on the parent item.
        """
        flow_args = dict(
            comment=item.description or "",
            thumbnail_path=item.get_thumbnail_as_path(),
        )

        # Read from parent item - revision_id applies to entire publish session
        revision_id = None
        if item.parent:
            revision_id = item.parent.properties.get("am_revision_id")

        if revision_id:
            pub_info = self._publish_revision(item, flow_args, revision_id)
        else:
            pub_info = self._create_new_asset(item, flow_args)

        return pub_info

    def _get_generic_inputs(self, item) -> dict:
        """
        Build the SG entity inputs required by the Flow AM SDK for generic
        asset creation. Called by ``_create_new_asset`` to populate
        ``CreateGenericInputs``.
        """
        sg_flow_am_id = sgtk.platform.current_engine().context.project["sg_flow_am_id"]
        entity = item.context.entity or item.context.project
        entity_type = entity["type"]
        # When creating from project context, sg entity related parameters are not relevant
        sg_entity_type = entity_type if entity_type != "Project" else None
        sg_entity_name = entity["name"] if entity_type != "Project" else None
        sg_pipeline_step = (
            item.context.step["name"] if entity_type != "Project" else None
        )
        sg_task_name = item.context.task["name"] if entity_type != "Project" else None

        return dict(
            am_project_id=sg_flow_am_id,
            sg_entity_name=sg_entity_name,
            sg_entity_type=sg_entity_type,
            sg_pipeline_step=sg_pipeline_step,
            sg_task_name=sg_task_name,
            source_path=item.get_property("path"),
        )

    def _publish_revision(self, item, flow_args: dict, revision_id: str):
        """
        Publish a new revision of an existing generic asset via the Flow AM SDK.
        Called by ``_publish_to_flow`` when a revision ID is present on the
        parent item, indicating we are updating an existing asset rather than
        creating a new one.
        """
        self.logger.info(
            f"Publishing new revision of existing generic asset (revision_id: {revision_id})"
        )

        # Prepare GenericPublishInputs
        flow_args.update(
            {
                "am_asset_id": revision_id,  # Revision id can be used as an asset id in MEDM
                "source_path": item.get_property("path"),
            }
        )
        publish_inputs = self.flow_module.asset_management.GenericPublishInputs(
            **flow_args
        )

        self.logger.debug(
            "Calling publish_generic_revision with:",
            extra={
                "action_show_more_info": {
                    "label": "See contents",
                    "text": "<pre>" f"{pprint.pformat(flow_args)}\n" "</pre>",
                }
            },
        )

        # Note: If this fails, the exception propagates to publish() which
        # handles error logging.
        pub_info = self.flow_module.asset_management.publish_generic_revision(
            publish_inputs,
        )
        return pub_info

    def _create_new_asset(self, item, flow_args: dict):
        """
        Create a new generic asset via the Flow AM SDK. Called by
        ``_publish_to_flow`` when no revision ID is present on the parent
        item, indicating this is a first-time publish rather than a revision.
        Delegates SG entity resolution to ``_get_generic_inputs``.
        """
        self.logger.info("Creating new generic asset")

        create_args = self._get_generic_inputs(item)
        create_args.update(
            {
                "comment": flow_args.get("comment", ""),
                "thumbnail_path": flow_args.get("thumbnail_path", ""),
            }
        )
        create_inputs = self.flow_module.asset_management.CreateGenericInputs(
            **create_args
        )

        self.logger.debug(
            "Calling create_generic_workfile with:",
            extra={
                "action_show_more_info": {
                    "label": "See contents",
                    "text": "<pre>" f"{pprint.pformat(create_inputs)}\n" "</pre>",
                }
            },
        )

        # Note: If this fails, the exception propagates to publish() which
        # handles error logging.
        pub_info = self.flow_module.asset_management.create_generic_workfile(
            create_inputs,
        )
        return pub_info
