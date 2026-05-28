# Copyright (c) 2025 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import pprint
import os

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class DesktopFlowPublishPlugin(HookBaseClass):
    """
    Plugin for publishing files from Flow Production Tracking Desktop to
    Flow Asset Management. This hook relies on functionality found in the
    Flow AM base publish hook in the ``tk-multi-publish2`` app and should
    inherit from it in the configuration. The hook setting for this plugin
    should look something like this::

        hook: "{self}/publish_file.py:{self}/flowam/publish_to_flow.py:{engine}/tk-multi-publish2/flowam/publish_to_flow.py"

    """

    def accept(self, settings, item):
        """
        We tell the publisher to skip publishing Maya files
        by checking the file extension of the item being published.
        These files won't be displayed in the UI.

        PS: This can be also defined in `publish_to_flow.py`.
        """
        path = item.get_property("path")
        if path is None:
            raise AttributeError("'PublishData' object has no attribute 'path'")

        # Get the extension of the file
        ext = os.path.splitext(path)[-1].lower()
        if ext in [".ma", ".mb"]:
            self.logger.warning("Maya dependencies will not be tracked in Flow AM.")
            return {"accepted": False}

        return super().accept(settings, item)

    def validate(self, settings, item):
        """
        Desktop-specific validation for publishing to Flow AM.
        Does not require a draft - supports both new asset creation and revision publishing.
        """
        if not super().validate(settings, item):
            return False

        # Desktop publishing uses self.flow_module set by parent class
        am = self.flow_module.asset_management

        # Read from parent item - revision_id applies to entire publish session
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

    def _get_generic_inputs(self, item) -> dict:
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
            sg_entity_type=sg_entity_type,
            sg_entity_name=sg_entity_name,
            sg_pipeline_step=sg_pipeline_step,
            sg_task_name=sg_task_name,
            am_project_id=sg_flow_am_id,
            source_path=item.get_property("path"),
        )

    def _publish_revision(self, item, flow_args, revision_id):
        """Publish new revision of existing generic asset."""
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

        # Note: If this fails, the exception propagates to the parent publish() method
        # which handles error logging.
        pub_info = self.flow_module.asset_management.publish_generic_revision(
            publish_inputs,
        )
        return pub_info

    def _create_new_asset(self, item, flow_args):
        """Create new generic asset."""
        self.logger.info("Creating new generic asset")

        create_args = self._get_generic_inputs(item)
        create_args.update(
            {
                "thumbnail_path": flow_args.get("thumbnail_path", ""),
                "comment": flow_args.get("comment", ""),
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

        # Note: If this fails, the exception propagates to the parent publish() method
        # which handles error logging.
        pub_info = self.flow_module.asset_management.create_generic_workfile(
            create_inputs,
        )
        return pub_info

    def _publish_to_flow(self, settings, item):
        flow_args = self._get_flow_args(item)

        # Read from parent item - revision_id applies to entire publish session
        revision_id = None
        if item.parent:
            revision_id = item.parent.properties.get("am_revision_id")

        # If revision_id is present, we are publishing a new revision of an existing asset, otherwise we are creating a new asset
        if revision_id:
            pub_info = self._publish_revision(item, flow_args, revision_id)
        else:
            pub_info = self._create_new_asset(item, flow_args)

        # Return framework data
        return pub_info
