# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


def get_engine_implementation(implementation_type):
    if implementation_type == "site":
        from .desktop_engine_site_implementation import DesktopEngineSiteImplementation
        return DesktopEngineSiteImplementation
    if implementation_type == "project":
        from .desktop_engine_project_implementation import DesktopEngineProjectImplementation
        return DesktopEngineProjectImplementation

    raise RuntimeError("unknown implementation_type: '%s'" % implementation_type)
