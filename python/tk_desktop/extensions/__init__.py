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
if sys.platform.startswith("linux"):

    # The PTR desktop app that comes with PySide2 does not require
    # any helper code to have the application move the foreground
    # properly.
    try:
        import PySide2  # noqa
    except Exception as e:
        logger.warning("Could not load PySide2: %s", e, exc_info=True)
elif sys.platform == "darwin":
    # On macOS, the osutils are required to make the app move to the foreground
    # or background in certain cases.
    try:
        # This library does not link against qt, so the names are not suffixed
        # with the qt version.
        if sys.version_info[0] == 2:
            from .darwin_python2 import osutils
        elif sys.version_info[0:2] == (3, 7):
            from .darwin_python37 import osutils
        elif sys.version_info[0:2] == (3, 9):
            from .darwin_python39 import osutils
        elif sys.version_info[0:2] >= (3, 10):
            from .darwin_python310 import osutils
        use_mocked_osutils = False
    except Exception as e:
        logger.warning("Could not load osutils: %s", e, exc_info=True)
else:
    # Not only has Windows' osutils been broken for years since it
    # was a 32-bit compiled version of the extension, in practice
    # none of the code has been necessary to get both PySide and PySide2
    # versions of desktop running, so there's no need to test for Windows
    # here.
    pass

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
