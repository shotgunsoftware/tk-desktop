# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from .desktop_notification import DesktopNotification
from .configuration_update_notification import ConfigurationUpdateNotification
from .first_launch_notification import FirstLaunchNotification
from .startup_update_notification import StartupUpdateNotification
from .python2_deprecation_notification import Python2DeprecationNotification

import sgtk

logger = sgtk.platform.get_logger(__name__)


class NotificationsManager(object):
    """
    Allows to retrieve and dismiss notifications for the Shotgun Desktop.
    """

    _BANNERS = "banners"
    NOTIFS_TO_BE_INCLUDED_IN_FIRST_LAUNCH = [
        Python2DeprecationNotification,
    ]

    def __init__(self, user_settings, site_descriptor, project_descriptor, engine):
        """
        :param user_settings. ``UserSettings`` instance.
        :param site_descriptor: Descriptor obtained from the site pipeline configuration.
        :param project_descriptor: Descriptor obtained from the project's pipeline configuration.
        :param engine: tk-desktop engine instance.
        """
        self._user_settings = user_settings
        self._site_descriptor = site_descriptor
        self._project_descriptor = project_descriptor
        self._engine = engine

    def get_notifications(self):
        """
        Returns a list of notifications.

        If the FirstLaunchNotitification hasn't been dismissed yet, every other notification
        will be dismissed.

        :returns: An array on :class:``Notification`` objects.
        """
        logger.debug("Retrieving the list of notifications...")
        banner_settings = self._get_banner_settings()

        # notifications

        # Check if this is the first launch.
        first_launch_notif = FirstLaunchNotification.create(banner_settings)
        # Python 2 deprecation notif
        python2_notif = Python2DeprecationNotification.create(banner_settings)
        # startup update and desktop notifs
        startup_update_notif = StartupUpdateNotification.create(
            banner_settings, self._engine
        )  # noqa
        desktop_notif = DesktopNotification.create(
            banner_settings, self._engine
        )  # noqa

        # Get all other notification types. Filter out those who are not set.
        other_notifs = [
            startup_update_notif,
            desktop_notif,
            python2_notif,
        ]

        # If both descriptors are set and they have the same uri, we only want one notification.
        if (
            self._site_descriptor
            and self._project_descriptor
            and self._site_descriptor.get_uri() == self._project_descriptor.get_uri()
        ):
            logger.debug("Site and project both have the same descriptor.")
            other_notifs.append(
                ConfigurationUpdateNotification.create(
                    banner_settings, self._site_descriptor
                )
            )
        else:
            logger.debug("Creating site notification.")
            other_notifs.append(
                ConfigurationUpdateNotification.create(
                    banner_settings, self._site_descriptor
                )
            )
            logger.debug("Creating project notification.")
            other_notifs.append(
                ConfigurationUpdateNotification.create(
                    banner_settings, self._project_descriptor
                )
            )

        other_notifs = list(filter(None, other_notifs))

        # If this is the first launch, suppress all other notifications not
        # present in include_in_first_launch
        if first_launch_notif:
            logger.debug(
                "First launch notification to be displayed, dismiss all other notifications."
            )
            to_return = [first_launch_notif]
            for notif in other_notifs:
                accepted = True
                for notif_class in self.NOTIFS_TO_BE_INCLUDED_IN_FIRST_LAUNCH:
                    if not isinstance(notif, notif_class):
                        self.dismiss(notif)
                        accepted = False
                        break
                if accepted:
                    to_return.append(notif)
            return to_return
        else:
            logger.debug("Notifications to display: %s", other_notifs)
            return other_notifs

    def dismiss(self, notification):
        """
        Marks a notification as dismiss to that it is not shown in the future.
        """
        settings = self._get_banner_settings()
        notification._dismiss(settings)
        self._user_settings.store(self._BANNERS, settings)

    def _get_banner_settings(self):
        """
        Retrieves the banner settings section from the ``UserSettings``.

        :returns: Dictionary of settings.
        """
        return self._user_settings.retrieve(self._BANNERS) or {}
