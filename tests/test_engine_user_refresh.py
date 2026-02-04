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
Unit tests for user credential refresh and change detection in desktop_engine_site_implementation.py

These tests verify that when credentials are refreshed (potentially with a different user),
the engine correctly detects the user change and notifies the desktop window to update the UI.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import sys
import os

# Ensure the tk_desktop module path is available
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))


class TestEngineUserRefresh:
    """
    Test suite for desktop_engine_site_implementation.py user refresh functionality.
    """

    @pytest.fixture
    def mock_engine_impl(self):
        """
        Creates a mock DesktopEngineSiteImplementation instance.
        """
        from tk_desktop.desktop_engine_site_implementation import (
            DesktopEngineSiteImplementation,
        )

        # Create mock engine
        mock_engine = Mock()
        mock_engine.sgtk = Mock()
        mock_engine.sgtk.shotgun = Mock()

        # Create the implementation instance
        engine_impl = Mock()
        engine_impl._engine = mock_engine
        engine_impl._current_login = {"id": 123, "login": "usera@example.com"}
        engine_impl._user = Mock()
        engine_impl._user.login = "usera@example.com"
        engine_impl.desktop_window = Mock()

        # Bind the actual methods we want to test
        engine_impl.refresh_user_credentials = (
            DesktopEngineSiteImplementation.refresh_user_credentials.__get__(
                engine_impl, type(engine_impl)
            )
        )
        engine_impl._check_and_update_current_user = (
            DesktopEngineSiteImplementation._check_and_update_current_user.__get__(
                engine_impl, type(engine_impl)
            )
        )

        return engine_impl

    @pytest.fixture
    def mock_shotgun_authenticator(self):
        """
        Creates a mock ShotgunAuthenticator.
        """
        with patch(
            "tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator"
        ) as mock_auth:
            yield mock_auth

    def test_refresh_user_credentials_stores_previous_login(self, mock_engine_impl):
        """
        Test that refresh_user_credentials() captures the previous login before refreshing.

        This is necessary to detect if the user changed after credential refresh.
        """
        previous_login = "usera@example.com"
        mock_engine_impl._current_login = {"id": 123, "login": previous_login}

        with patch.object(mock_engine_impl._user, "refresh_credentials"), patch.object(
            mock_engine_impl, "_check_and_update_current_user"
        ) as mock_check:

            mock_engine_impl.refresh_user_credentials()

            # Verify _check_and_update_current_user was called with the previous login
            mock_check.assert_called_once_with(previous_login)

    def test_refresh_user_credentials_calls_check_after_refresh(self, mock_engine_impl):
        """
        Test that refresh_user_credentials() checks for user changes after refreshing credentials.

        This ensures user changes are detected immediately after credential refresh.
        """
        with patch.object(
            mock_engine_impl._user, "refresh_credentials"
        ) as mock_refresh, patch.object(
            mock_engine_impl, "_check_and_update_current_user"
        ) as mock_check:

            mock_engine_impl.refresh_user_credentials()

            # Verify credentials were refreshed first
            mock_refresh.assert_called_once()

            # Then user change check was performed
            mock_check.assert_called_once()

    def test_check_and_update_current_user_detects_user_change(
        self, mock_engine_impl, mock_shotgun_authenticator
    ):
        """
        Test that _check_and_update_current_user() detects when a different user authenticates.

        This is the core security fix - detecting when User A logs out and User B logs in.
        """
        # Setup: User A was logged in
        previous_login = "usera@example.com"

        # User B is now authenticated
        new_user = Mock()
        new_user.login = "userb@example.com"
        mock_shotgun_authenticator.return_value.get_default_user.return_value = new_user

        mock_engine_impl._engine.sgtk.shotgun.find_one.return_value = {
            "id": 456,
            "login": "userb@example.com",
        }

        with patch("tk_desktop.desktop_engine_site_implementation.sgtk") as mock_sgtk:
            mock_sgtk.util.CoreDefaultsManager = Mock

            result = mock_engine_impl._check_and_update_current_user(previous_login)

            # Verify user change was detected
            assert result is True

    def test_check_and_update_current_user_updates_cached_user(
        self, mock_engine_impl, mock_shotgun_authenticator
    ):
        """
        Test that _check_and_update_current_user() updates the cached user info when user changes.

        The engine must cache the new user's information for subsequent operations.
        """
        previous_login = "usera@example.com"

        # User B is now authenticated
        new_user = Mock()
        new_user.login = "userb@example.com"
        mock_shotgun_authenticator.return_value.get_default_user.return_value = new_user

        new_login_data = {"id": 456, "login": "userb@example.com"}
        mock_engine_impl._engine.sgtk.shotgun.find_one.return_value = new_login_data

        with patch("tk_desktop.desktop_engine_site_implementation.sgtk") as mock_sgtk:
            mock_sgtk.util.CoreDefaultsManager = Mock

            mock_engine_impl._check_and_update_current_user(previous_login)

            # Verify cached user was updated
            assert mock_engine_impl._user == new_user
            assert mock_engine_impl._current_login == new_login_data

    def test_check_and_update_current_user_notifies_desktop_window(
        self, mock_engine_impl, mock_shotgun_authenticator
    ):
        """
        Test that _check_and_update_current_user() notifies the desktop window when user changes.

        The desktop window needs to refresh its UI to show the new user's information.
        """
        previous_login = "usera@example.com"

        # User B is now authenticated
        new_user = Mock()
        new_user.login = "userb@example.com"
        mock_shotgun_authenticator.return_value.get_default_user.return_value = new_user

        mock_engine_impl._engine.sgtk.shotgun.find_one.return_value = {
            "id": 456,
            "login": "userb@example.com",
        }

        with patch("tk_desktop.desktop_engine_site_implementation.sgtk") as mock_sgtk:
            mock_sgtk.util.CoreDefaultsManager = Mock

            mock_engine_impl._check_and_update_current_user(previous_login)

            # Verify desktop window was notified
            mock_engine_impl.desktop_window.on_user_changed.assert_called_once()

    def test_check_and_update_current_user_no_change_same_user(
        self, mock_engine_impl, mock_shotgun_authenticator
    ):
        """
        Test that _check_and_update_current_user() returns False when user hasn't changed.

        If the same user re-authenticates, no UI refresh is needed.
        """
        previous_login = "usera@example.com"

        # Same user re-authenticates
        same_user = Mock()
        same_user.login = "usera@example.com"
        mock_shotgun_authenticator.return_value.get_default_user.return_value = (
            same_user
        )

        with patch("tk_desktop.desktop_engine_site_implementation.sgtk") as mock_sgtk:
            mock_sgtk.util.CoreDefaultsManager = Mock

            result = mock_engine_impl._check_and_update_current_user(previous_login)

            # Verify no user change was detected
            assert result is False

            # Verify desktop window was NOT notified
            mock_engine_impl.desktop_window.on_user_changed.assert_not_called()

    def test_check_and_update_current_user_handles_none_desktop_window(
        self, mock_engine_impl, mock_shotgun_authenticator
    ):
        """
        Test that _check_and_update_current_user() handles missing desktop window gracefully.

        During initialization, desktop_window might not be set yet.
        """
        previous_login = "usera@example.com"
        mock_engine_impl.desktop_window = None

        # User B is now authenticated
        new_user = Mock()
        new_user.login = "userb@example.com"
        mock_shotgun_authenticator.return_value.get_default_user.return_value = new_user

        mock_engine_impl._engine.sgtk.shotgun.find_one.return_value = {
            "id": 456,
            "login": "userb@example.com",
        }

        with patch("tk_desktop.desktop_engine_site_implementation.sgtk") as mock_sgtk:
            mock_sgtk.util.CoreDefaultsManager = Mock

            # Should not raise any exception
            result = mock_engine_impl._check_and_update_current_user(previous_login)

            # User change should still be detected
            assert result is True

    def test_check_and_update_current_user_handles_none_authenticated_user(
        self, mock_engine_impl, mock_shotgun_authenticator
    ):
        """
        Test that _check_and_update_current_user() handles None authenticated user.

        If authentication fails or no user is authenticated, handle gracefully.
        """
        previous_login = "usera@example.com"

        # No authenticated user
        mock_shotgun_authenticator.return_value.get_default_user.return_value = None

        with patch("tk_desktop.desktop_engine_site_implementation.sgtk") as mock_sgtk:
            mock_sgtk.util.CoreDefaultsManager = Mock

            result = mock_engine_impl._check_and_update_current_user(previous_login)

            # Should return False and not crash
            assert result is False

    def test_check_and_update_current_user_first_time_check(
        self, mock_engine_impl, mock_shotgun_authenticator
    ):
        """
        Test that _check_and_update_current_user() handles first-time checks (no previous login).

        When previous_login is None, just update cached info to sync with authenticated user.
        """
        previous_login = None

        current_user = Mock()
        current_user.login = "user@example.com"
        mock_shotgun_authenticator.return_value.get_default_user.return_value = (
            current_user
        )

        mock_engine_impl._engine.sgtk.shotgun.find_one.return_value = {
            "id": 123,
            "login": "user@example.com",
        }

        # Setup cached user with different login to simulate out-of-sync state
        mock_engine_impl._user = Mock()
        mock_engine_impl._user.login = "olduser@example.com"

        with patch("tk_desktop.desktop_engine_site_implementation.sgtk") as mock_sgtk:
            mock_sgtk.util.CoreDefaultsManager = Mock

            result = mock_engine_impl._check_and_update_current_user(previous_login)

            # Should update cached info even though previous_login is None
            assert mock_engine_impl._user == current_user

            # Should not trigger desktop window refresh (no confirmed user change)
            assert result is False

    def test_check_and_update_current_user_handles_exceptions(
        self, mock_engine_impl, mock_shotgun_authenticator
    ):
        """
        Test that _check_and_update_current_user() handles exceptions without crashing.

        Network errors or authentication errors shouldn't break the application.
        """
        previous_login = "usera@example.com"

        # Simulate an exception during authentication check
        mock_shotgun_authenticator.return_value.get_default_user.side_effect = (
            Exception("Connection error")
        )

        with patch("tk_desktop.desktop_engine_site_implementation.sgtk") as mock_sgtk:
            mock_sgtk.util.CoreDefaultsManager = Mock

            # Should not raise any exception
            result = mock_engine_impl._check_and_update_current_user(previous_login)

            # Should return False
            assert result is False


class TestEngineUserRefreshIntegration:
    """
    Integration tests for the complete credential refresh and user change detection flow.
    """

    def test_complete_credential_refresh_flow_with_user_change(self):
        """
        Test the complete flow when credentials are refreshed with a different user.

        This simulates the real scenario:
        1. User A is working in Desktop
        2. Session expires after 1 hour
        3. User B re-authenticates through the session launcher
        4. Engine detects the user change and notifies Desktop window
        5. Desktop window refreshes UI to show User B's info
        """
        from tk_desktop.desktop_engine_site_implementation import (
            DesktopEngineSiteImplementation,
        )

        # Create mock engine
        mock_engine = Mock()
        mock_engine.sgtk = Mock()
        mock_engine.sgtk.shotgun = Mock()

        engine_impl = Mock()
        engine_impl._engine = mock_engine

        # Setup User A as initially logged in
        user_a = Mock()
        user_a.login = "usera@example.com"
        engine_impl._user = user_a
        engine_impl._current_login = {"id": 123, "login": "usera@example.com"}
        engine_impl.desktop_window = Mock()

        # Bind the actual methods
        engine_impl.refresh_user_credentials = (
            DesktopEngineSiteImplementation.refresh_user_credentials.__get__(
                engine_impl, type(engine_impl)
            )
        )
        engine_impl._check_and_update_current_user = (
            DesktopEngineSiteImplementation._check_and_update_current_user.__get__(
                engine_impl, type(engine_impl)
            )
        )

        # Simulate User B re-authenticating
        user_b = Mock()
        user_b.login = "userb@example.com"

        with patch(
            "tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator"
        ) as mock_auth, patch(
            "tk_desktop.desktop_engine_site_implementation.sgtk"
        ) as mock_sgtk:

            mock_sgtk.util.CoreDefaultsManager = Mock
            mock_auth.return_value.get_default_user.return_value = user_b

            mock_engine.sgtk.shotgun.find_one.return_value = {
                "id": 456,
                "login": "userb@example.com",
            }

            # Call refresh_user_credentials
            engine_impl.refresh_user_credentials()

            # Verify User B is now cached
            assert engine_impl._user == user_b
            assert engine_impl._current_login["login"] == "userb@example.com"

            # Verify desktop window was notified of the user change
            engine_impl.desktop_window.on_user_changed.assert_called_once()
        """
        Test credential refresh when the same user re-authenticates.

        If User A's session expires and they re-authenticate as User A,
        no UI refresh is needed.
        """
        from tk_desktop.desktop_engine_site_implementation import (
            DesktopEngineSiteImplementation,
        )

        # Create mock engine
        mock_engine = Mock()
        mock_engine.sgtk = Mock()
        mock_engine.sgtk.shotgun = Mock()

        engine_impl = Mock()
        engine_impl._engine = mock_engine

        # Setup User A as initially logged in
        user_a = Mock()
        user_a.login = "usera@example.com"
        engine_impl._user = user_a
        engine_impl._current_login = {"id": 123, "login": "usera@example.com"}
        engine_impl.desktop_window = Mock()

        # Bind the actual methods
        engine_impl.refresh_user_credentials = (
            DesktopEngineSiteImplementation.refresh_user_credentials.__get__(
                engine_impl, type(engine_impl)
            )
        )
        engine_impl._check_and_update_current_user = (
            DesktopEngineSiteImplementation._check_and_update_current_user.__get__(
                engine_impl, type(engine_impl)
            )
        )

        # User A re-authenticates (same user)
        with patch(
            "tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator"
        ) as mock_auth, patch(
            "tk_desktop.desktop_engine_site_implementation.sgtk"
        ) as mock_sgtk:

            mock_sgtk.util.CoreDefaultsManager = Mock
            mock_auth.return_value.get_default_user.return_value = user_a

            # Call refresh_user_credentials
            engine_impl.refresh_user_credentials()

            # Verify desktop window was NOT notified (no user change)
            engine_impl.desktop_window.on_user_changed.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
