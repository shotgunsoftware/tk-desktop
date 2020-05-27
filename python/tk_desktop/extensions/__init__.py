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
try:
    if sys.version_info[0] == 2:
        try:
            # If we can't import PySide2, then we're in Shotgun Desktop 1.5.7 or less
            # and we need to impo
            import PySide2  # noqa

            is_qt5 = True
        except Exception:
            is_qt5 = False

        if sys.platform == "darwin":
            from .darwin_python2 import osutils
        elif sys.platform == "win32":
            from .win32_python2 import osutils
        elif sys.platform.startswith("linux"):
            if is_qt5:
                from .linux_python2 import osutils
            else:
                from .linux_python2_qt4 import osutils
    else:
        if sys.platform == "darwin":
            from .darwin_python3 import osutils
        elif sys.platform == "win32":
            from .win32_python3 import osutils
        elif sys.platform.startswith("linux"):
            from .linux_python3 import osutils
    osutils.is_mocked = False
except Exception as e:
    logger.warning("Could not import osutils: %s", e, exc_info=True)

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
