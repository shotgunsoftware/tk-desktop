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
if sys.platform == "darwin":
    # On macOS, osutils is required to control foreground/background app state.
    # osutils is a private macOS C extension built by the FPT Desktop team.
    # SGD >= 3.0.0 installs the .so into Python's lib-dynload directory, so a
    # plain absolute import works automatically via the normal import machinery.
    # SGD < 3.0.0 shipped the .so committed directly to the darwin_python3/
    # package directory, so the fallback relative import handles those bundles.
    try:
        import osutils

        use_mocked_osutils = False
    except ImportError:
        try:
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
