# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from .notification import Notification
import sgtk

logger = sgtk.platform.get_logger(__name__)


class Python2DeprecationNotification(Notification):
    """
    Notification for python 2 deprecation.
    """

    _PYTHON2_DEPRECATION_ID = "python2-deprecation-notification"

    def __init__(self, engine):
        """
        :param engine: Toolkit engine.
        """
        self._engine = engine

    @classmethod
    def create(cls, banner_settings, engine):
        """
        Notification factory for python 2 deprecation.

        :param banner_settings: Dictionary of banner settings.
        :param engine: Toolkit engine.

        :returns: A :class:`Python2DeprecationNotification` instance, or ``None``.
        """
        if banner_settings.get(cls._PYTHON2_DEPRECATION_ID, {}).get(
            "is_dismissed", False
        ):
            logger.debug("This banner has already been dismissed.")
            return None
        else:
            logger.debug("Python 2 deprecation banner available")
            return Python2DeprecationNotification(engine)

    @property
    def message(self):
        """
        Message to display.
        """
        url = "https://community.shotgridsoftware.com/t/important-notice-upcoming-removal-of-python-2-7-and-3-7-interpreter-in-shotgrid-desktop/15168"  # noqa
        msg = """
        ShotGrid is ending support for <b>Python 2</b> in SG Desktop on <b>Nov 1 2022</b>. Upgrade to <b>Python 3.9</b>
        before this date. Read more <a href='{}'>here</a>.
        """.format(
            url
        )

        return msg

    @property
    def unique_id(self):
        """
        Returns the unique identifier of a notification.
        """
        return self._PYTHON2_DEPRECATION_ID

    def _dismiss(self, banner_settings):
        """
        Updates the ``banner_settings`` so this notification does not come back in the future.

        :param banner_settings: Dictionary of the banners settings.
        """
        banner_settings.setdefault(self._PYTHON2_DEPRECATION_ID, {})[
            "is_dismissed"
        ] = True
