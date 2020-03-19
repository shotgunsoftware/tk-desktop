# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
This module implements the project commands panel.

The panel is comprised of a hierarchy of graphical elements. Every quoted term
in the description below is a class name.

At the root sits the "ProjectCommands" class. It contains a "RecentSection" and one or more
"CommandSection"s

The "RecentSection" contains a list of "RecentButton" while the "CommandSection" contains
a list of "CommandButton". Both have a "DefaultGroupingHeader" which allows to expand and
collapse the section.

The section classes themselves hold either a "CommandList" and "RecentList", which are the
actual owners of the button objects.

There are also intermediary classes. "Section" is the base class of "RecentSection"
and "CommandSection", while "BaseIconList" is the base class of "CommandList" and "RecentList".

The following graph shows those relationships

|                                                          <- RecentSection  <- ProjectCommands
| + Recent  <- DefaultGroupingHeader                       <- RecentSection  <- ProjectCommands
|                                            <- RecentList <- RecentSection  <- ProjectCommands
|     logo       logo     <- 2 RecentButtons <- RecentList <- RecentSection  <- ProjectCommands
|   Maya 2019   Nuke 12.0                    <- RecentList <- RecentSection  <- ProjectCommands
|                                            <- RecentList <- RecentSection  <- ProjectCommands
+--------------------------------------------------------- <- RecentSection  <- ProjectCommands
|                                                          <- CommandSection <- ProjectCommands
| + Creative Tools <- DefaultGroupingHandler               <- CommandSection <- ProjectCommands
|                                          <- CommandList  <- CommandSection <- ProjectCommands
|  Maya          Nuke <- 2 CommandButtons  <- CommandList  <- CommandSection <- ProjectCommands
|  Nuke Studio        <- 1 CommandButtons  <- CommandList  <- CommandSection <- ProjectCommands
|                                          <- CommandList  <- CommandSection <- ProjectCommands
+--------------------------------------------------------  <- CommandSection <- ProjectCommands
"""

from .project_commands import ProjectCommands
