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
            import PySide2 as _

            is_qt5 = True
        except Exception:
            is_qt5 = False
        if is_qt5:
            if sys.platform == "darwin":
                from .darwin_python2 import osutils
            elif sys.platform == "win32":
                from .win32_python2 import osutils
            elif sys.platform.startswith("linux"):
                from .linux_python2 import osutils
        else:
            if sys.platform == "darwin":
                from .darwin_python2 import osutils
            elif sys.platform == "win32":
                from .win32_python2 import osutils
            elif sys.platform.startswith("linux"):
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
    logger.debug("Could not import osutils: ", exc_info=True)
    print(e)

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
