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

if sys.platform.startswith("linux"):
    try:
        import PySide  # noqa
    except Exception:
        # PySide 2 build of desktop does not require help
        # making the application go in the foreground/background.
        use_mocked_osutils = True
    else:
        # We're in a PySide 1 version of Shotgun Desktop, so try
        # to import the old osutils
        try:
            from .linux_python2_qt4 import osutils
        except Exception as e:
            logger.warning("Could not load osutils: %s", e, exc_info=True)
            use_mocked_osutils = True
elif sys.plaform == "darwin":
    # On macOS, the osutils are required to make the app move to the foreground
    # or background in certain cases.
    try:
        if sys.version_info[0] == 2:
            from .darwin_python2 import osutils
        else:
            from .darwin_python3 import osutils
    except Exception as e:
        logger.warning("Could not load osutils: %s", e, exc_info=True)
        use_mocked_osutils = True
else:
    # Not only has Windows' osutils been broken for years since it
    # was a 32-bit compiled version of the extension, in practice
    # none of the code has been necessary to get both PySide and PySide2
    # versions of desktop running, so we'll use the mocked osutils there as
    # well.
    use_mocked_osutils = True

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

        is_mocked = True
