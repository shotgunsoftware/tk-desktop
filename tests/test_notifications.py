# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from __future__ import with_statement
import os
import sys

from tank_test.tank_test_base import TankTestBase, SealedMock
from tank_test.tank_test_base import setUpModule # noqa

notifications_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), # tk-desktop/tests
        "..", # tk-desktop
        "python", # tk-desktop/python
        "tk_desktop" # tk-desktop/python/tk_desktop
    )
)
sys.path.insert(0, notifications_path)

import notifications


class MockUserSettings(dict):

    def store(self, key, value):
        self[key] = value

    def retrieve(self, key):
        return self.get(key)


class TestNotifications(TankTestBase):
    """
    Tests the startup logic for Nuke.
    """

    def setUp(self):
        super(TestNotifications, self).setUp()

        # Mocks ShotgunUtils UserSettings class.
        self._user_settings = MockUserSettings()

        # Mocks the descriptor class.
        self._mock_descriptor = SealedMock(
            changelog=("Text", "http://foo.bar"),
            get_uri=SealedMock()
        )
        # Later tests will set the get_uri mock's return_value.
        self._get_uri_mock = self._mock_descriptor.get_uri

        # Mocks the parts of the engine required by the notification system.
        self._mock_engine = SealedMock(
            startup_descriptor=None,
            get_setting=self._get_setting_mock
        )

        # Create the manager.
        self._notification_manager = notifications.NotificationsManager(
            self._user_settings,
            self._mock_descriptor,
            self._mock_descriptor,
            self._mock_engine
        )

        # Will be used by the _get_setting_mock method to mock engine settings.
        self._banner_id = None
        self._banner_message = None

    def _get_setting_mock(self, name, _=None):
        """
        Mocks the engine's get_setting method.
        """
        # Make sure we're not asking for something unexpected.
        self.assertIn(name, ["banner_id", "banner_message"])

        if name == "banner_id":
            return self._banner_id
        else:
            return self._banner_message

    def _dismiss_first_launch(self):
        """
        Because the user settings are clean at the start of each test, we need to dismiss
        the start notification.
        """
        # Make sure there's only one notif and its the first launch one.
        notifs = self._notification_manager.get_notifications()
        self._test_properties(notifs)
        self.assertEqual(len(notifs), 1)
        self.assertEqual(isinstance(notifs[0], notifications.FirstLaunchNotification), True)

        # Dismiss it!
        self._notification_manager.dismiss(notifs[0])

        # Should be empty now.
        self.assertListEqual(
            self._notification_manager.get_notifications(),
            []
        )

    def test_first_launch_notifs(self):
        """
        Test the first launch notification message.
        """
        notifs = self._notification_manager.get_notifications()
        self._test_properties(notifs)

        # Make sure there's only one notification the first time you launch the desktop. We don't
        # want to know about a configuration update.
        self.assertEqual(len(notifs), 1)
        self.assertEqual(isinstance(notifs[0], notifications.FirstLaunchNotification), True)

        # Dismiss the notification.
        self._notification_manager.dismiss(notifs[0])

        # Now there should be no more current notifications.
        self.assertListEqual(
            self._notification_manager.get_notifications(),
            []
        )

    def test_configuration_update_notifs(self):
        """
        Test the configuration update notification.
        """

        # Dismiss the first launch with a given configuration descriptor.
        self._dismiss_first_launch()

        # Change the configuration descriptor to simulate a configuration update.
        self._get_uri_mock.return_value = "xyz"

        # Now there should be an extra event.
        notifs = self._notification_manager.get_notifications()
        self._test_properties(notifs)

        self.assertEqual(len(notifs), 1)
        self.assertEqual(isinstance(notifs[0], notifications.ConfigurationUpdateNotification), True)

        # Dismiss the notification.
        self._notification_manager.dismiss(notifs[0])

        # Now there should be no more current notifications.
        self.assertListEqual(
            self._notification_manager.get_notifications(),
            []
        )

    def test_no_config_update_notifs_on_missing_doc(self):
        """
        Test the configuration update notification when no release url is available.
        """
        self._dismiss_first_launch()
        self._get_uri_mock.return_value = "xyz"

        self._mock_descriptor.changelog = (None, None)

        notifs = self._notification_manager.get_notifications()

        self.assertEqual(len(notifs), 0)

    def test_startup_update_config(self):
        """
        Test the configuration update notification when no release url is available.
        """
        self._dismiss_first_launch()
        self._mock_engine.startup_descriptor = SealedMock(
            version="v0.0.0",
            changelog=(None, "https://foo.bar"),
            has_remote_access=SealedMock(return_value=True)
        )

        self._mock_descriptor.changelog = (None, None)

        notifs = self._notification_manager.get_notifications()
        self._test_properties(notifs)
        self.assertEqual(len(notifs), 1)
        self.assertEqual(
            isinstance(notifs[0], notifications.StartupUpdateNotification),
            True
        )

        # Dismiss the notification.
        self._notification_manager.dismiss(notifs[0])

        # Now there should be no more current notifications.
        self.assertListEqual(
            self._notification_manager.get_notifications(),
            []
        )

    def _test_properties(self, notifications):
        """
        Ensures all properties returns strings.

        :param notifications: List of notitications to test.
        """
        for notif in notifications:
            self.assertTrue(isinstance(notif.message, str))
            self.assertTrue(isinstance(notif.unique_id, str))

    def test_desktop_notifs(self):
        """
        Test notifications that are stored as engine settings.
        """
        self._dismiss_first_launch()

        self._banner_id = "banner_id"
        self._banner_message = "banner_message"

        notifs = self._notification_manager.get_notifications()
        self._test_properties(notifs)
        self.assertEqual(len(notifs), 1)
        self.assertEqual(
            isinstance(notifs[0], notifications.DesktopNotification),
            True
        )

        # Dismiss the notification.
        self._notification_manager.dismiss(notifs[0])

        # Now there should be no more current notifications.
        self.assertListEqual(
            self._notification_manager.get_notifications(),
            []
        )
