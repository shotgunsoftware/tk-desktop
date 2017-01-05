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
    "description": "This will assign all active users to the 'Template Project'. Users who couldn't "
    "launch the Shotgun Desktop due to permission errors will now be able to do so."
}


def is_available(engine):
    """
    Returns if this command should be available.

    :param engine: The current engine.

    :returns: True if the pipeline configuration still has a Project assigned to it, False otherwise.
    """
    # If we have the site configuration, there's nothing to do here.
    # is_site_configuration is not introduced in core at the time of this writing, so check for the
    # None project id instead.
    if engine.sgtk.pipeline_configuration.get_project_id() is None:
        return False
    return True


def callback(dialog):
    """
    Assigns all human users to the pipeline configuration's project.
    """
    qt_gui = sgtk.platform.qt.QtGui

    # First confirm that the user wants to indeed run this command.
    result = qt_gui.QMessageBox.question(
        dialog,
        name,
        "%s\n\nDo you want to continue?" % properties["description"],
        qt_gui.QMessageBox.Yes | qt_gui.QMessageBox.No
    )

    if result == qt_gui.QMessageBox.No:
        return

    engine = sgtk.platform.current_engine()
    pc = engine.sgtk.pipeline_configuration

    # Retrieve all the active users.
    users = engine.shotgun.find("HumanUser", [["sg_status_list", "is", "act"]])

    # Assign them to the current Project.
    engine.shotgun.update(
        "Project",
        pc.get_project_id(),
        {"users": users}
    )

    # Inform the user of what happened.
    msg = "%d users were assigned to the 'Template Project'." % len(users)
    sgtk.platform.qt.QtGui.QMessageBox.information(dialog, name, msg)
