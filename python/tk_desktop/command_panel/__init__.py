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

At the root sits the "CommandPanel" class. It contains a "RecentSection" and one or more
"CommandSection"s

The "RecentSection" contains a list of "RecentButton" while the "CommandSection" contains
a list of "CommandButton". Both have a "SectionHeader" which allows to expand and
collapse the section.

The section classes themselves hold either a "CommandList" and "RecentList", which are the
actual owners of the button objects.

There are also intermediary classes. "Section" is the base class of "RecentSection"
and "CommandSection", while "BaseIconList" is the base class of "CommandList" and "RecentList".

The following graph shows those relationships

|                                                          <- RecentSection  <- CommandPanel
| + Recent          <- SectionHeader                       <- RecentSection  <- CommandPanel
|                                            <- RecentList <- RecentSection  <- CommandPanel
|     logo       logo     <- 2 RecentButtons <- RecentList <- RecentSection  <- CommandPanel
|   Maya 2019   Nuke 12.0                    <- RecentList <- RecentSection  <- CommandPanel
|                                            <- RecentList <- RecentSection  <- CommandPanel
+--------------------------------------------------------- <- RecentSection  <- CommandPanel
|                                                          <- CommandSection <- CommandPanel
| + Creative Tools <- DefaultGroupingHandler               <- CommandSection <- CommandPanel
|                                          <- CommandList  <- CommandSection <- CommandPanel
|  Maya          Nuke <- 2 CommandButtons  <- CommandList  <- CommandSection <- CommandPanel
|  Nuke Studio        <- 1 CommandButtons  <- CommandList  <- CommandSection <- CommandPanel
|                                          <- CommandList  <- CommandSection <- CommandPanel
+--------------------------------------------------------  <- CommandSection <- CommandPanel
"""

from .command_panel import CommandPanel

__all__ = ("CommandPanel",)
