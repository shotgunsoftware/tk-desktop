# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Unit tests for user authentication and UI refresh functionality in desktop_window.py

These tests verify that when a user re-authenticates after session expiry with a
different account, the UI correctly updates to show the new user's information
and prevents the security issue where previous user data was displayed.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import tempfile
import os
import sys

# Ensure the tk_desktop module path is available
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))


class TestDesktopWindowUserAuthentication:
    """
    Test suite for desktop_window.py user authentication refresh functionality.
    """

    @pytest.fixture
    def mock_engine(self):
        """
        Creates a mock SGTK engine with necessary methods.
        """
        engine = Mock()
        engine.get_current_login.return_value = {"id": 123, "login": "user@example.com"}

        mock_user = Mock()
        mock_connection = Mock()
        mock_connection.base_url = "https://example.shotgrid.autodesk.com"
        mock_connection.find_one.return_value = {
            "id": 123,
            "name": "Test User",
            "image": None,
        }
        mock_user.create_sg_connection.return_value = mock_connection
        engine.get_current_user.return_value = mock_user

        return engine

    @pytest.fixture
    def mock_desktop_window(self, mock_engine):
        """
        Creates a mock DesktopWindow instance with necessary attributes.
        """
        with patch("sgtk.platform.current_engine", return_value=mock_engine):
            window = Mock()
            window._current_user_id = 123
            window._user_name_action = Mock()
            window._user_url_action = Mock()
            window._project_model = Mock()
            window.ui = Mock()
            window.ui.user_button = Mock()

            # Import the actual methods we want to test
            from tk_desktop.desktop_window import DesktopWindow

            # Bind the methods to the mock instance
            window.on_user_changed = DesktopWindow.on_user_changed.__get__(
                window, type(window)
            )
            window._refresh_user_info = DesktopWindow._refresh_user_info.__get__(
                window, type(window)
            )
            window._refresh_project_model_for_new_user = (
                DesktopWindow._refresh_project_model_for_new_user.__get__(
                    window, type(window)
                )
            )
            window._validate_current_user = (
                DesktopWindow._validate_current_user.__get__(window, type(window))
            )

            return window

    def test_on_user_changed_refreshes_user_info_and_projects(
        self, mock_desktop_window, mock_engine
    ):
        """
        Test that on_user_changed() calls both refresh methods.

        When a user change is detected, the UI should refresh both user information
        (name, email, thumbnail) and the project list.
        """
        with patch("sgtk.platform.current_engine", return_value=mock_engine):
            # Setup mocks for the methods we'll check were called
            mock_desktop_window._refresh_user_info = Mock()
            mock_desktop_window._refresh_project_model_for_new_user = Mock()

            # Call the method under test
            mock_desktop_window.on_user_changed()

            # Verify both refresh methods were called
            mock_desktop_window._refresh_user_info.assert_called_once()
            mock_desktop_window._refresh_project_model_for_new_user.assert_called_once()

    def test_refresh_user_info_updates_user_name_action(
        self, mock_desktop_window, mock_engine
    ):
        """
        Test that _refresh_user_info() updates the user name in the menu.

        This ensures the new user's name is displayed in the UI menu after re-authentication.
        """
        new_user_name = "New User"
        mock_engine.get_current_login.return_value = {
            "id": 456,
            "login": "newuser@example.com",
        }
        mock_connection = mock_engine.get_current_user().create_sg_connection()
        mock_connection.find_one.return_value = {
            "id": 456,
            "name": new_user_name,
            "image": None,
        }

        with patch("sgtk.platform.current_engine", return_value=mock_engine):
            mock_desktop_window._refresh_user_info()

            # Verify the user name action was updated with the new user's name
            mock_desktop_window._user_name_action.setText.assert_called_once_with(
                new_user_name
            )

    def test_refresh_user_info_updates_cached_user_id(
        self, mock_desktop_window, mock_engine
    ):
        """
        Test that _refresh_user_info() updates the cached user ID.

        This ensures the cached user ID matches the authenticated user after re-authentication.
        """
        new_user_id = 456
        mock_engine.get_current_login.return_value = {
            "id": new_user_id,
            "login": "newuser@example.com",
        }

        with patch("sgtk.platform.current_engine", return_value=mock_engine):
            mock_desktop_window._refresh_user_info()

            # Verify the cached user ID was updated
            assert mock_desktop_window._current_user_id == new_user_id

    def test_refresh_user_info_updates_site_url(self, mock_desktop_window, mock_engine):
        """
        Test that _refresh_user_info() updates the site URL in the menu.

        This handles cases where the site URL might change (though rare).
        """
        new_site_url = "https://newsite.shotgrid.autodesk.com"
        mock_connection = mock_engine.get_current_user().create_sg_connection()
        mock_connection.base_url = new_site_url

        with patch("sgtk.platform.current_engine", return_value=mock_engine):
            mock_desktop_window._refresh_user_info()

            # Verify the site URL was updated (without the https:// prefix)
            mock_desktop_window._user_url_action.setText.assert_called_once_with(
                "newsite.shotgrid.autodesk.com"
            )

    def test_refresh_user_info_with_thumbnail(self, mock_desktop_window, mock_engine):
        """
        Test that _refresh_user_info() updates the user thumbnail when available.

        This ensures the new user's avatar is displayed in the UI.
        """
        thumbnail_url = "https://example.com/thumbnail.jpg"
        mock_connection = mock_engine.get_current_user().create_sg_connection()
        mock_connection.find_one.return_value = {
            "id": 456,
            "name": "New User",
            "image": thumbnail_url,
        }

        with patch("sgtk.platform.current_engine", return_value=mock_engine), patch(
            "tempfile.mkstemp", return_value=(None, "/tmp/test.jpg")
        ), patch(
            "tk_desktop.desktop_window.shotgun.download_url"
        ) as mock_download, patch(
            "tk_desktop.desktop_window.QtGui.QPixmap"
        ) as mock_pixmap, patch(
            "os.remove"
        ):

            mock_desktop_window._refresh_user_info()

            # Verify thumbnail download was attempted
            mock_download.assert_called_once_with(
                mock_connection, thumbnail_url, "/tmp/test.jpg"
            )

    def test_refresh_project_model_for_new_user_calls_hard_refresh(
        self, mock_desktop_window
    ):
        """
        Test that _refresh_project_model_for_new_user() calls hard_refresh on the model.

        hard_refresh() clears the cache and reloads from the server, ensuring the
        project list shows only projects the new user has access to with correct
        user-specific data (favorites, last accessed times).
        """
        mock_desktop_window._refresh_project_model_for_new_user()

        # Verify hard_refresh was called on the project model
        mock_desktop_window._project_model.hard_refresh.assert_called_once()

    def test_refresh_project_model_handles_none_model(self, mock_desktop_window):
        """
        Test that _refresh_project_model_for_new_user() handles None model gracefully.

        This ensures no error occurs if the project model hasn't been initialized yet.
        """
        mock_desktop_window._project_model = None

        # Should not raise any exception
        mock_desktop_window._refresh_project_model_for_new_user()

    def test_validate_current_user_detects_user_mismatch(
        self, mock_desktop_window, mock_engine
    ):
        """
        Test that _validate_current_user() detects when cached user doesn't match authenticated user.

        This is the proactive check that catches user changes even when credential
        refresh hasn't been explicitly called.
        """
        # Setup: cached user is 123, but authenticated user is now 456
        mock_desktop_window._current_user_id = 123
        mock_engine.get_current_login.return_value = {
            "id": 456,
            "login": "newuser@example.com",
        }

        with patch("sgtk.platform.current_engine", return_value=mock_engine):
            mock_desktop_window._refresh_user_info = Mock()

            mock_desktop_window._validate_current_user()

            # Verify that _refresh_user_info was called due to the mismatch
            mock_desktop_window._refresh_user_info.assert_called_once()

    def test_validate_current_user_no_refresh_when_users_match(
        self, mock_desktop_window, mock_engine
    ):
        """
        Test that _validate_current_user() doesn't refresh when users match.

        If the cached user matches the authenticated user, no refresh is needed.
        """
        # Setup: cached user matches authenticated user
        mock_desktop_window._current_user_id = 123
        mock_engine.get_current_login.return_value = {
            "id": 123,
            "login": "user@example.com",
        }

        with patch("sgtk.platform.current_engine", return_value=mock_engine):
            mock_desktop_window._refresh_user_info = Mock()

            mock_desktop_window._validate_current_user()

            # Verify that _refresh_user_info was NOT called
            mock_desktop_window._refresh_user_info.assert_not_called()

    def test_validate_current_user_handles_exceptions_gracefully(
        self, mock_desktop_window, mock_engine
    ):
        """
        Test that _validate_current_user() handles exceptions without crashing the UI.

        Validation errors should be logged but not break the user experience.
        """
        mock_engine.get_current_login.side_effect = Exception("Connection error")

        with patch("sgtk.platform.current_engine", return_value=mock_engine):
            # Should not raise any exception
            mock_desktop_window._validate_current_user()

    def test_validate_current_user_handles_none_login(
        self, mock_desktop_window, mock_engine
    ):
        """
        Test that _validate_current_user() handles None login gracefully.

        If no user is logged in, validation should exit early without errors.
        """
        mock_engine.get_current_login.return_value = None

        with patch("sgtk.platform.current_engine", return_value=mock_engine):
            mock_desktop_window._refresh_user_info = Mock()

            mock_desktop_window._validate_current_user()

            # Should not attempt to refresh
            mock_desktop_window._refresh_user_info.assert_not_called()


# class TestDesktopWindowIntegration:
#     """
#     Integration tests verifying the complete user change flow.
#     """

    # def test_complete_user_change_flow(self):
    #     """
    #     Test the complete flow when a user changes after re-authentication.

    #     This simulates the real scenario:
    #     1. User A is logged in and using Desktop
    #     2. Session expires after 1 hour
    #     3. User B re-authenticates
    #     4. Desktop UI should update to show User B's info and projects
    #     """
    #     from tk_desktop.desktop_window import DesktopWindow

    #     with patch("sgtk.platform.current_engine") as mock_engine:
    #         # Setup initial state - User A is logged in
    #         mock_engine.return_value.get_current_login.return_value = {
    #             "id": 123,
    #             "login": "usera@example.com",
    #         }

    #         mock_connection_a = Mock()
    #         mock_connection_a.base_url = "https://example.shotgrid.autodesk.com"
    #         mock_connection_a.find_one.return_value = {
    #             "id": 123,
    #             "name": "User A",
    #             "image": None,
    #         }

    #         mock_user_a = Mock()
    #         mock_user_a.create_sg_connection.return_value = mock_connection_a
    #         mock_engine.return_value.get_current_user.return_value = mock_user_a

    #         window = Mock()
    #         window._current_user_id = 123
    #         window._user_name_action = Mock()
    #         window._user_url_action = Mock()
    #         window._project_model = Mock()
    #         window.ui = Mock()
    #         window.ui.user_button = Mock()

    #         # Bind the actual methods
    #         window._refresh_user_info = DesktopWindow._refresh_user_info.__get__(
    #             window, type(window)
    #         )
    #         window._refresh_project_model_for_new_user = (
    #             DesktopWindow._refresh_project_model_for_new_user.__get__(
    #                 window, type(window)
    #             )
    #         )
    #         window.on_user_changed = DesktopWindow.on_user_changed.__get__(
    #             window, type(window)
    #         )

    #         # Simulate User B re-authenticating
    #         mock_engine.return_value.get_current_login.return_value = {
    #             "id": 456,
    #             "login": "userb@example.com",
    #         }

    #         mock_connection_b = Mock()
    #         mock_connection_b.base_url = "https://example.shotgrid.autodesk.com"
    #         mock_connection_b.find_one.return_value = {
    #             "id": 456,
    #             "name": "User B",
    #             "image": None,
    #         }

    #         mock_user_b = Mock()
    #         mock_user_b.create_sg_connection.return_value = mock_connection_b
    #         mock_engine.return_value.get_current_user.return_value = mock_user_b

    #         # Call on_user_changed() which should refresh everything
    #         window.on_user_changed()

    #         # Verify User B's name is now displayed
    #         window._user_name_action.setText.assert_called_with("User B")

    #         # Verify cached user ID was updated to User B
    #         assert window._current_user_id == 456

    #         # Verify project model was refreshed
    #         window._project_model.hard_refresh.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
