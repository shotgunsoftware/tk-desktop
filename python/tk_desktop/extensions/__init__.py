# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sys

import sgtk

logger = sgtk.platform.get_logger(__name__)

use_mocked_osutils = True
# The osutils extension modules from the PTR desktop app's private repo.
if sys.platform == "darwin":
    # On macOS, the osutils are required to make the app move to the foreground
    # or background in certain cases.
    try:
        # This library does not link against qt, so the names are not suffixed
        # with the qt version.
        from .darwin_python3 import osutils

        use_mocked_osutils = False
    except Exception as e:
        logger.warning("Could not load osutils: %s", e, exc_info=True)

if use_mocked_osutils:

    class osutils:
        @staticmethod
        def activate_application():
            pass

        @staticmethod
        def make_app_foreground():
            pass

        @staticmethod
        def make_app_background():
            pass
