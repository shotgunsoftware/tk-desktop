# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

# import sys
# import os

# # Adds the python/tk_desktop folder to the python path so we can import
# # the notifications and rpc modules for testing.
# tk_desktop_path = os.path.abspath(
#     os.path.join(
#         os.path.dirname(__file__),  # tk-desktop/tests
#         "..",  # tk-desktop
#         "python",  # tk-desktop/python
#         "tk_desktop",  # tk-desktop/python/tk_desktop
#     )
# )
# sys.path.insert(0, tk_desktop_path)

# # Mock framework imports at module level before any test modules are imported
# # This prevents TankCurrentModuleNotFoundError during test collection
# try:
#     import sgtk.platform
#     from unittest.mock import Mock

#     # Create a mock framework that can be used for all framework calls
#     _mock_framework = Mock()
#     _mock_framework.shotgun = Mock()
#     _mock_framework.shotgun.connection = Mock()

#     def _mock_get_framework(*args, **kwargs):
#         return _mock_framework

#     def _mock_import_framework(*args, **kwargs):
#         return _mock_framework

#     # Replace the functions at module level
#     sgtk.platform.get_framework = _mock_get_framework
#     sgtk.platform.import_framework = _mock_import_framework
# except ImportError:
#     pass
