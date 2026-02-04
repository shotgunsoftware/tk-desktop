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
Unit tests for user authentication and UI refresh functionality.

These tests verify the security fix that prevents user data from persisting
when a different user re-authenticates after session expiry.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import tempfile
import os
import sys

# Ensure the tk_desktop module path is available
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

# Mock sgtk.platform methods before importing tk_desktop modules
# This prevents TankCurrentModuleNotFoundError during module import
with patch('sgtk.platform.import_framework') as mock_import_framework, \
     patch('sgtk.platform.get_framework') as mock_get_framework:
    # Create mock framework modules
    mock_shotgun_model = MagicMock()
    mock_shotgun_model.ShotgunModel = MagicMock
    
    mock_import_framework.return_value = mock_shotgun_model
    mock_get_framework.return_value = MagicMock()
    
    # Now it's safe to import tk_desktop modules
    from tk_desktop.desktop_window import DesktopWindow


class TestDesktopWindowOnUserChanged:
    """Tests for the on_user_changed() method."""

    @patch('sgtk.platform.current_engine')
    def test_on_user_changed_calls_refresh_methods(self, mock_engine):
        """
        Verify on_user_changed() calls both _refresh_user_info and
        _refresh_project_model_for_new_user.
        """
        # Create a mock window
        window = Mock(spec=DesktopWindow)
        window._refresh_user_info = Mock()
        window._refresh_project_model_for_new_user = Mock()
        
        # Call the actual method
        DesktopWindow.on_user_changed(window)
        
        # Verify both refresh methods were called
        window._refresh_user_info.assert_called_once()
        window._refresh_project_model_for_new_user.assert_called_once()

    @patch('sgtk.platform.current_engine')
    def test_on_user_changed_handles_refresh_user_info_exception(self, mock_engine):
        """
        Verify on_user_changed() handles exceptions from _refresh_user_info gracefully.
        """
        window = Mock(spec=DesktopWindow)
        window._refresh_user_info = Mock(side_effect=Exception("Connection error"))
        window._refresh_project_model_for_new_user = Mock()
        
        # Should not raise exception
        DesktopWindow.on_user_changed(window)

    @patch('sgtk.platform.current_engine')
    def test_on_user_changed_handles_refresh_projects_exception(self, mock_engine):
        """
        Verify on_user_changed() handles exceptions from project refresh gracefully.
        """
        window = Mock(spec=DesktopWindow)
        window._refresh_user_info = Mock()
        window._refresh_project_model_for_new_user = Mock(
            side_effect=Exception("API error")
        )
        
        # Should not raise exception
        DesktopWindow.on_user_changed(window)


class TestDesktopWindowRefreshUserInfo:
    """Tests for the _refresh_user_info() method."""

    @patch('sgtk.platform.current_engine')
    def test_refresh_user_info_updates_all_user_fields(self, mock_engine):
        """
        Verify _refresh_user_info() updates user ID, name, URL, and thumbnail.
        """
        # Setup mock engine and connections
        mock_user = Mock()
        mock_connection = Mock()
        mock_connection.base_url = "https://test.shotgrid.autodesk.com"
        mock_connection.find_one.return_value = {
            "id": 456,
            "name": "New User",
            "image": None
        }
        mock_user.create_sg_connection.return_value = mock_connection
        mock_engine.return_value.get_current_user.return_value = mock_user
        mock_engine.return_value.get_current_login.return_value = {
            "id": 456,
            "login": "newuser@test.com"
        }
        
        # Create mock window
        window = Mock(spec=DesktopWindow)
        window._current_user_id = 123
        window._user_name_action = Mock()
        window._user_url_action = Mock()
        window.ui = Mock()
        window.ui.user_button = Mock()
        
        # Call the actual method
        DesktopWindow._refresh_user_info(window)
        
        # Verify all fields were updated
        assert window._current_user_id == 456
        window._user_name_action.setText.assert_called_once_with("New User")
        window._user_url_action.setText.assert_called_once_with(
            "test.shotgrid.autodesk.com"
        )

    @patch('sgtk.platform.current_engine')
    @patch('tk_desktop.desktop_window.shotgun.download_url')
    @patch('tk_desktop.desktop_window.QtGui.QPixmap')
    @patch('tempfile.mkstemp', return_value=(None, '/tmp/test_thumb.jpg'))
    @patch('os.remove')
    def test_refresh_user_info_downloads_thumbnail(
        self, mock_remove, mock_mkstemp, mock_pixmap, mock_download, mock_engine
    ):
        """
        Verify _refresh_user_info() downloads and sets user thumbnail when available.
        """
        # Setup mock with thumbnail URL
        mock_user = Mock()
        mock_connection = Mock()
        mock_connection.base_url = "https://test.shotgrid.autodesk.com"
        mock_connection.find_one.return_value = {
            "id": 456,
            "name": "User With Avatar",
            "image": "https://test.com/avatar.jpg"
        }
        mock_user.create_sg_connection.return_value = mock_connection
        mock_engine.return_value.get_current_user.return_value = mock_user
        mock_engine.return_value.get_current_login.return_value = {
            "id": 456,
            "login": "user@test.com"
        }
        
        window = Mock(spec=DesktopWindow)
        window._current_user_id = 123
        window._user_name_action = Mock()
        window._user_url_action = Mock()
        window.ui = Mock()
        window.ui.user_button = Mock()
        
        # Call the method
        DesktopWindow._refresh_user_info(window)
        
        # Verify thumbnail was downloaded
        mock_download.assert_called_once_with(
            mock_connection,
            "https://test.com/avatar.jpg",
            '/tmp/test_thumb.jpg'
        )
        
        # Verify temp file was cleaned up
        mock_remove.assert_called()

    @patch('sgtk.platform.current_engine')
    @patch('tk_desktop.desktop_window.shotgun.download_url', side_effect=Exception("Download failed"))
    @patch('tempfile.mkstemp', return_value=(None, '/tmp/test_thumb.jpg'))
    @patch('os.remove')
    def test_refresh_user_info_handles_thumbnail_download_failure(
        self, mock_remove, mock_mkstemp, mock_download, mock_engine
    ):
        """
        Verify _refresh_user_info() handles thumbnail download failures gracefully.
        """
        mock_user = Mock()
        mock_connection = Mock()
        mock_connection.base_url = "https://test.shotgrid.autodesk.com"
        mock_connection.find_one.return_value = {
            "id": 456,
            "name": "User",
            "image": "https://test.com/avatar.jpg"
        }
        mock_user.create_sg_connection.return_value = mock_connection
        mock_engine.return_value.get_current_user.return_value = mock_user
        mock_engine.return_value.get_current_login.return_value = {
            "id": 456,
            "login": "user@test.com"
        }
        
        window = Mock(spec=DesktopWindow)
        window._current_user_id = 123
        window._user_name_action = Mock()
        window._user_url_action = Mock()
        window.ui = Mock()
        window.ui.user_button = Mock()
        
        # Should not raise exception despite download failure
        DesktopWindow._refresh_user_info(window)
        
        # User info should still be updated
        assert window._current_user_id == 456


class TestDesktopWindowRefreshProjectModel:
    """Tests for _refresh_project_model_for_new_user() method."""

    def test_refresh_project_model_calls_hard_refresh(self):
        """
        Verify _refresh_project_model_for_new_user() calls hard_refresh on model.
        """
        window = Mock(spec=DesktopWindow)
        window._project_model = Mock()
        
        DesktopWindow._refresh_project_model_for_new_user(window)
        
        window._project_model.hard_refresh.assert_called_once()

    def test_refresh_project_model_handles_none_model(self):
        """
        Verify _refresh_project_model_for_new_user() handles None model gracefully.
        """
        window = Mock(spec=DesktopWindow)
        window._project_model = None
        
        # Should not raise exception
        DesktopWindow._refresh_project_model_for_new_user(window)

    def test_refresh_project_model_handles_hard_refresh_exception(self):
        """
        Verify _refresh_project_model_for_new_user() handles hard_refresh exceptions.
        """
        window = Mock(spec=DesktopWindow)
        window._project_model = Mock()
        window._project_model.hard_refresh.side_effect = Exception("API error")
        
        # Should not raise exception (logged but handled)
        try:
            DesktopWindow._refresh_project_model_for_new_user(window)
        except Exception:
            pytest.fail("Should not raise exception")


class TestDesktopWindowValidateCurrentUser:
    """Tests for _validate_current_user() method."""

    @patch('sgtk.platform.current_engine')
    def test_validate_detects_user_mismatch_and_refreshes(self, mock_engine):
        """
        Verify _validate_current_user() detects user mismatch and calls _refresh_user_info.
        """
        # Setup: cached user is 123, but current is 456
        mock_engine.return_value.get_current_login.return_value = {
            "id": 456,
            "login": "different@test.com"
        }
        
        window = Mock(spec=DesktopWindow)
        window._current_user_id = 123
        window._refresh_user_info = Mock()
        
        DesktopWindow._validate_current_user(window)
        
        # Should call refresh due to mismatch
        window._refresh_user_info.assert_called_once()

    @patch('sgtk.platform.current_engine')
    def test_validate_no_refresh_when_users_match(self, mock_engine):
        """
        Verify _validate_current_user() doesn't refresh when users match.
        """
        # Setup: cached and current user match
        mock_engine.return_value.get_current_login.return_value = {
            "id": 123,
            "login": "same@test.com"
        }
        
        window = Mock(spec=DesktopWindow)
        window._current_user_id = 123
        window._refresh_user_info = Mock()
        
        DesktopWindow._validate_current_user(window)
        
        # Should NOT call refresh
        window._refresh_user_info.assert_not_called()

    @patch('sgtk.platform.current_engine')
    def test_validate_handles_none_current_login(self, mock_engine):
        """
        Verify _validate_current_user() handles None login gracefully.
        """
        mock_engine.return_value.get_current_login.return_value = None
        
        window = Mock(spec=DesktopWindow)
        window._current_user_id = 123
        window._refresh_user_info = Mock()
        
        # Should not raise exception or call refresh
        DesktopWindow._validate_current_user(window)
        window._refresh_user_info.assert_not_called()

    @patch('sgtk.platform.current_engine')
    def test_validate_handles_exception(self, mock_engine):
        """
        Verify _validate_current_user() handles exceptions without crashing.
        """
        mock_engine.return_value.get_current_login.side_effect = Exception("API error")
        
        window = Mock(spec=DesktopWindow)
        window._current_user_id = 123
        window._refresh_user_info = Mock()
        
        # Should not raise exception
        DesktopWindow._validate_current_user(window)

    @patch('sgtk.platform.current_engine')
    def test_validate_handles_none_cached_user_id(self, mock_engine):
        """
        Verify _validate_current_user() handles None cached user ID.
        """
        mock_engine.return_value.get_current_login.return_value = {
            "id": 456,
            "login": "user@test.com"
        }
        
        window = Mock(spec=DesktopWindow)
        window._current_user_id = None
        window._refresh_user_info = Mock()
        
        # Should not raise exception or call refresh (no baseline to compare)
        DesktopWindow._validate_current_user(window)


class TestDesktopWindowHandleProjectDataChanged:
    """Tests for _handle_project_data_changed() integration."""

    @patch('sgtk.platform.current_engine')
    def test_handle_project_data_changed_calls_validate(self, mock_engine):
        """
        Verify _handle_project_data_changed() calls _validate_current_user.
        """
        mock_engine.return_value.get_current_login.return_value = {
            "id": 123,
            "login": "user@test.com"
        }
        
        window = Mock(spec=DesktopWindow)
        window._project_command_count = 5
        window._project_selection_model = Mock()
        window._project_proxy = Mock()
        window._current_user_id = 123
        window._validate_current_user = Mock()
        
        DesktopWindow._handle_project_data_changed(window)
        
        # Verify validation was called
        window._validate_current_user.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
