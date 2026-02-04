# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sys
import os
import pytest

# Adds the python/tk_desktop folder to the python path so we can import
# the notifications and rpc modules for testing.
tk_desktop_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),  # tk-desktop/tests
        "..",  # tk-desktop
        "python",  # tk-desktop/python
        "tk_desktop",  # tk-desktop/python/tk_desktop
    )
)
sys.path.insert(0, tk_desktop_path)


# Configure pytest to mock framework imports before test collection
def pytest_configure(config):
    """
    Pytest hook called before test collection.
    Mock sgtk framework imports to prevent TankCurrentModuleNotFoundError.
    """
    try:
        import sgtk.platform
        from unittest.mock import Mock

        # Create a mock framework that can be used for all framework calls
        mock_framework = Mock()
        mock_framework.shotgun = Mock()
        mock_framework.shotgun.connection = Mock()

        # Store originals in case we need them
        _original_get_framework = sgtk.platform.get_framework
        _original_import_framework = sgtk.platform.import_framework

        def mock_get_framework(*args, **kwargs):
            return mock_framework

        def mock_import_framework(*args, **kwargs):
            return mock_framework

        # Replace the functions at module level
        sgtk.platform.get_framework = mock_get_framework
        sgtk.platform.import_framework = mock_import_framework
    except ImportError:
        pass
