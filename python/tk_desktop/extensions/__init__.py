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
# The osutils extension modules from the Shotgun Desktop's private repo.
if sys.platform.startswith("linux"):

    # The Shotgun Desktop that comes with PySide2 does not require
    # any helper code to have the application move the foreground
    # properly.
    try:
        import PySide2  # noqa
    except Exception:
        # We're in a PySide 1 version of Shotgun Desktop, so try
        # to import the old osutils
        try:
            # This library links againts Qt, so the version number is
            # suffixed to the module. If in the future we need to
            # have an extension for qt5, we'll avoid a name clash.
            from .linux_python2_qt4 import osutils

            use_mocked_osutils = False
        except Exception as e:
            logger.warning("Could not load osutils: %s", e, exc_info=True)
    else:
        # PySide 2 build of desktop does not require help
        # making the application go in the foreground/background, so we
        # don't need to import an extension module.
        pass
elif sys.platform == "darwin":
    # On macOS, the osutils are required to make the app move to the foreground
    # or background in certain cases.
    try:
        # This library does not link against qt, so the names are not suffixed
        # with the qt version.
        if sys.version_info[0] == 2:
            from .darwin_python2 import osutils
        else:
            from .darwin_python3 import osutils
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
