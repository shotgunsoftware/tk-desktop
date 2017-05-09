# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from abc import abstractproperty, abstractmethod


class Notification(object):
    """
    Base class for Notification classes.

    Requires the implementation of the ``message`` property and ``_dismiss`` method.
    """

    @abstractproperty
    def message(self):
        """
        Message to display.
        """

    @abstractmethod
    def _dismiss(self):
        """
        Updates the ``banner_settings`` so this notification does not come back in the future.

        :param banner_settings: Dictionary of the banners settings.
        """
