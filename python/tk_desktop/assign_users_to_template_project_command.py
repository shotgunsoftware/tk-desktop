# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk


name = "Assign users to Template Project"
properties = {
    "short_name": "assign_users_to_template_project",
    "description": "Assign all users to the Template Project. This allows the user to "
}


def is_available(engine):
    """
    Returns if this command should be available.

    :param engine: The current engine.

    :returns: True if the pipeline configuration stll has a Project assigned to it, False otherwise.
    """
    # If there is no project assigned, there's nothing to do.
    if engine.sgtk.pipeline_configuration.get_project_id() is None:
        return False
    return True


def callback():
    """
    Assigns all human users to the pipeline configuration's project.
    """

    engine = sgtk.platform.current_engine()
    pc = engine.sgtk.pipeline_configuration

    # Retrieve all the users.
    users = engine.shotgun.find("HumanUser", [])

    # Assign them to the current Project.
    engine.shotgun.update(
        "Project",
        pc.get_project_id(),
        {"users": users}
    )
