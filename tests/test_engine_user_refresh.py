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
Unit tests for user credential refresh and change detection in engine.

These tests verify the security fix at the engine level that detects when
a different user re-authenticates and notifies the UI to refresh.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Ensure the tk_desktop module path is available
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

# Mock sgtk.platform methods before importing tk_desktop modules
# This prevents TankCurrentModuleNotFoundError during module import
with patch('sgtk.platform.import_framework') as mock_import_framework, \
     patch('sgtk.platform.get_framework') as mock_get_framework:
    # Create mock framework modules
    mock_import_framework.return_value = MagicMock()
    mock_get_framework.return_value = MagicMock()
    
    # Now it's safe to import tk_desktop modules
    from tk_desktop.desktop_engine_site_implementation import DesktopEngineSiteImplementation


class TestEngineRefreshUserCredentials:
    """Tests for refresh_user_credentials() method."""

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_refresh_captures_previous_login(self, mock_sgtk, mock_auth):
        """
        Verify refresh_user_credentials() captures previous login before refreshing.
        """
        # Setup mock engine implementation
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "usera@test.com"}
        engine_impl._user = Mock()
        engine_impl._user.login = "usera@test.com"
        engine_impl._engine = Mock()
        engine_impl.desktop_window = Mock()
        
        mock_sgtk.util.CoreDefaultsManager = Mock
        mock_auth.return_value.get_default_user.return_value = engine_impl._user
        
        # Track the previous_login passed to _check_and_update_current_user
        captured_previous_login = None
        
        def capture_check(previous_login=None):
            nonlocal captured_previous_login
            captured_previous_login = previous_login
            return False
        
        engine_impl._check_and_update_current_user = capture_check
        
        # Call the method
        DesktopEngineSiteImplementation.refresh_user_credentials(engine_impl)
        
        # Verify previous login was captured
        assert captured_previous_login == "usera@test.com"

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_refresh_calls_user_refresh_credentials(self, mock_sgtk, mock_auth):
        """
        Verify refresh_user_credentials() calls refresh_credentials on the user.
        """
        
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "user@test.com"}
        engine_impl._user = Mock()
        engine_impl._engine = Mock()
        engine_impl._check_and_update_current_user = Mock(return_value=False)
        
        mock_sgtk.util.CoreDefaultsManager = Mock
        
        DesktopEngineSiteImplementation.refresh_user_credentials(engine_impl)
        
        # Verify credentials were refreshed
        engine_impl._user.refresh_credentials.assert_called_once()

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_refresh_calls_check_after_credential_refresh(self, mock_sgtk, mock_auth):
        """
        Verify _check_and_update_current_user is called after credential refresh.
        """
        
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "user@test.com"}
        engine_impl._user = Mock()
        engine_impl._engine = Mock()
        engine_impl._check_and_update_current_user = Mock(return_value=False)
        
        mock_sgtk.util.CoreDefaultsManager = Mock
        
        DesktopEngineSiteImplementation.refresh_user_credentials(engine_impl)
        
        # Verify check was called
        engine_impl._check_and_update_current_user.assert_called_once_with(
            "user@test.com"
        )


class TestEngineCheckAndUpdateCurrentUser:
    """Tests for _check_and_update_current_user() method."""

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_check_detects_user_change(self, mock_sgtk, mock_auth):
        """
        Verify _check_and_update_current_user() detects when a different user logs in.
        """
        
        # Setup: User A was logged in
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "usera@test.com"}
        engine_impl._user = Mock()
        engine_impl._user.login = "usera@test.com"
        engine_impl._engine = Mock()
        engine_impl._engine.sgtk = Mock()
        engine_impl._engine.sgtk.shotgun = Mock()
        engine_impl.desktop_window = Mock()
        
        # User B is now authenticated
        new_user = Mock()
        new_user.login = "userb@test.com"
        mock_sgtk.util.CoreDefaultsManager = Mock
        mock_auth.return_value.get_default_user.return_value = new_user
        
        engine_impl._engine.sgtk.shotgun.find_one.return_value = {
            "id": 456,
            "login": "userb@test.com"
        }
        
        # Call the method
        result = DesktopEngineSiteImplementation._check_and_update_current_user(
            engine_impl, "usera@test.com"
        )
        
        # Verify user change was detected
        assert result is True

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_check_updates_cached_user_info(self, mock_sgtk, mock_auth):
        """
        Verify _check_and_update_current_user() updates cached user information.
        """
        
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "usera@test.com"}
        engine_impl._user = Mock()
        engine_impl._engine = Mock()
        engine_impl._engine.sgtk = Mock()
        engine_impl._engine.sgtk.shotgun = Mock()
        engine_impl.desktop_window = Mock()
        
        # New user
        new_user = Mock()
        new_user.login = "userb@test.com"
        mock_sgtk.util.CoreDefaultsManager = Mock
        mock_auth.return_value.get_default_user.return_value = new_user
        
        new_login_data = {"id": 456, "login": "userb@test.com"}
        engine_impl._engine.sgtk.shotgun.find_one.return_value = new_login_data
        
        DesktopEngineSiteImplementation._check_and_update_current_user(
            engine_impl, "usera@test.com"
        )
        
        # Verify cached data was updated
        assert engine_impl._user == new_user
        assert engine_impl._current_login == new_login_data

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_check_notifies_desktop_window(self, mock_sgtk, mock_auth):
        """
        Verify _check_and_update_current_user() notifies desktop window on user change.
        """
        
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "usera@test.com"}
        engine_impl._user = Mock()
        engine_impl._engine = Mock()
        engine_impl._engine.sgtk = Mock()
        engine_impl._engine.sgtk.shotgun = Mock()
        engine_impl.desktop_window = Mock()
        
        new_user = Mock()
        new_user.login = "userb@test.com"
        mock_sgtk.util.CoreDefaultsManager = Mock
        mock_auth.return_value.get_default_user.return_value = new_user
        
        engine_impl._engine.sgtk.shotgun.find_one.return_value = {
            "id": 456,
            "login": "userb@test.com"
        }
        
        DesktopEngineSiteImplementation._check_and_update_current_user(
            engine_impl, "usera@test.com"
        )
        
        # Verify desktop window was notified
        engine_impl.desktop_window.on_user_changed.assert_called_once()

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_check_returns_false_when_user_unchanged(self, mock_sgtk, mock_auth):
        """
        Verify _check_and_update_current_user() returns False when user hasn't changed.
        """
        
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "user@test.com"}
        engine_impl._user = Mock()
        engine_impl._user.login = "user@test.com"
        engine_impl._engine = Mock()
        engine_impl.desktop_window = Mock()
        
        # Same user re-authenticates
        same_user = Mock()
        same_user.login = "user@test.com"
        mock_sgtk.util.CoreDefaultsManager = Mock
        mock_auth.return_value.get_default_user.return_value = same_user
        
        result = DesktopEngineSiteImplementation._check_and_update_current_user(
            engine_impl, "user@test.com"
        )
        
        # Should return False (no user change)
        assert result is False
        
        # Desktop window should NOT be notified
        engine_impl.desktop_window.on_user_changed.assert_not_called()

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_check_handles_none_desktop_window(self, mock_sgtk, mock_auth):
        """
        Verify _check_and_update_current_user() handles missing desktop_window gracefully.
        """
        
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "usera@test.com"}
        engine_impl._user = Mock()
        engine_impl._engine = Mock()
        engine_impl._engine.sgtk = Mock()
        engine_impl._engine.sgtk.shotgun = Mock()
        engine_impl.desktop_window = None
        
        new_user = Mock()
        new_user.login = "userb@test.com"
        mock_sgtk.util.CoreDefaultsManager = Mock
        mock_auth.return_value.get_default_user.return_value = new_user
        
        engine_impl._engine.sgtk.shotgun.find_one.return_value = {
            "id": 456,
            "login": "userb@test.com"
        }
        
        # Should not raise exception even though desktop_window is None
        result = DesktopEngineSiteImplementation._check_and_update_current_user(
            engine_impl, "usera@test.com"
        )
        
        # Should still detect user change
        assert result is True

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_check_handles_none_authenticated_user(self, mock_sgtk, mock_auth):
        """
        Verify _check_and_update_current_user() handles None authenticated user.
        """
        
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "user@test.com"}
        engine_impl._user = Mock()
        engine_impl._engine = Mock()
        
        # No authenticated user
        mock_sgtk.util.CoreDefaultsManager = Mock
        mock_auth.return_value.get_default_user.return_value = None
        
        result = DesktopEngineSiteImplementation._check_and_update_current_user(
            engine_impl, "user@test.com"
        )
        
        # Should return False and not crash
        assert result is False

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_check_handles_exception(self, mock_sgtk, mock_auth):
        """
        Verify _check_and_update_current_user() handles exceptions gracefully.
        """
        
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "user@test.com"}
        engine_impl._user = Mock()
        engine_impl._engine = Mock()
        
        # Simulate exception during user check
        mock_sgtk.util.CoreDefaultsManager = Mock
        mock_auth.return_value.get_default_user.side_effect = Exception("Connection error")
        
        # Should not raise exception
        result = DesktopEngineSiteImplementation._check_and_update_current_user(
            engine_impl, "user@test.com"
        )
        
        assert result is False

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_check_handles_first_time_check_none_previous_login(self, mock_sgtk, mock_auth):
        """
        Verify _check_and_update_current_user() handles first-time check (no previous_login).
        """
        
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "user@test.com"}
        engine_impl._user = Mock()
        engine_impl._user.login = "olduser@test.com"  # Out of sync
        engine_impl._engine = Mock()
        engine_impl._engine.sgtk = Mock()
        engine_impl._engine.sgtk.shotgun = Mock()
        
        current_user = Mock()
        current_user.login = "user@test.com"
        mock_sgtk.util.CoreDefaultsManager = Mock
        mock_auth.return_value.get_default_user.return_value = current_user
        
        engine_impl._engine.sgtk.shotgun.find_one.return_value = {
            "id": 123,
            "login": "user@test.com"
        }
        
        # Call with None previous_login
        result = DesktopEngineSiteImplementation._check_and_update_current_user(
            engine_impl, None
        )
        
        # Should update cached info even though previous_login is None
        assert engine_impl._user == current_user
        
        # Should not trigger desktop window refresh (no confirmed user change)
        assert result is False

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_check_logs_user_change(self, mock_sgtk, mock_auth):
        """
        Verify _check_and_update_current_user() logs when user changes.
        """
        
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "usera@test.com"}
        engine_impl._user = Mock()
        engine_impl._engine = Mock()
        engine_impl._engine.sgtk = Mock()
        engine_impl._engine.sgtk.shotgun = Mock()
        engine_impl.desktop_window = Mock()
        
        new_user = Mock()
        new_user.login = "userb@test.com"
        mock_sgtk.util.CoreDefaultsManager = Mock
        mock_auth.return_value.get_default_user.return_value = new_user
        
        engine_impl._engine.sgtk.shotgun.find_one.return_value = {
            "id": 456,
            "login": "userb@test.com"
        }
        
        # The method should log the user change (we can't easily test logging,
        # but we can verify it doesn't crash and returns the correct value)
        result = DesktopEngineSiteImplementation._check_and_update_current_user(
            engine_impl, "usera@test.com"
        )
        
        assert result is True


class TestEngineUserRefreshIntegration:
    """Integration tests for the complete credential refresh flow."""

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_complete_user_change_flow(self, mock_sgtk, mock_auth):
        """
        Test the complete flow: User A session expires, User B re-authenticates,
        engine detects change and notifies desktop window.
        """
        
        # Setup: User A is logged in
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "usera@test.com"}
        user_a = Mock()
        user_a.login = "usera@test.com"
        engine_impl._user = user_a
        engine_impl._engine = Mock()
        engine_impl._engine.sgtk = Mock()
        engine_impl._engine.sgtk.shotgun = Mock()
        engine_impl.desktop_window = Mock()
        
        # User B re-authenticates
        user_b = Mock()
        user_b.login = "userb@test.com"
        mock_sgtk.util.CoreDefaultsManager = Mock
        mock_auth.return_value.get_default_user.return_value = user_b
        
        engine_impl._engine.sgtk.shotgun.find_one.return_value = {
            "id": 456,
            "login": "userb@test.com"
        }
        
        # Call refresh_user_credentials (simulating credential refresh)
        DesktopEngineSiteImplementation.refresh_user_credentials(engine_impl)
        
        # Verify User B is now cached
        assert engine_impl._user == user_b
        assert engine_impl._current_login["login"] == "userb@test.com"
        
        # Verify desktop window was notified
        engine_impl.desktop_window.on_user_changed.assert_called_once()

    @patch('tk_desktop.desktop_engine_site_implementation.ShotgunAuthenticator')
    @patch('tk_desktop.desktop_engine_site_implementation.sgtk')
    def test_same_user_reauth_no_window_notification(self, mock_sgtk, mock_auth):
        """
        Test that when the same user re-authenticates, desktop window is NOT notified.
        """
        
        # Setup: User A is logged in
        engine_impl = Mock()
        engine_impl._current_login = {"id": 123, "login": "usera@test.com"}
        user_a = Mock()
        user_a.login = "usera@test.com"
        engine_impl._user = user_a
        engine_impl._engine = Mock()
        engine_impl._engine.sgtk = Mock()
        engine_impl._engine.sgtk.shotgun = Mock()
        engine_impl.desktop_window = Mock()
        
        # User A re-authenticates (same user)
        mock_sgtk.util.CoreDefaultsManager = Mock
        mock_auth.return_value.get_default_user.return_value = user_a
        
        # Call refresh_user_credentials
        DesktopEngineSiteImplementation.refresh_user_credentials(engine_impl)
        
        # Verify desktop window was NOT notified (no user change)
        engine_impl.desktop_window.on_user_changed.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
