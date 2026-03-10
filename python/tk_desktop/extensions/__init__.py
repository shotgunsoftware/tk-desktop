# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import importlib.util
import os
import sys

import sgtk

logger = sgtk.platform.get_logger(__name__)


def _load_osutils_from_bundle():
    """
    Load the osutils C extension from the FPT Desktop app bundle.

    Since SGD 3.0.0 (SG-42559), the compiled extension lives inside the app
    bundle rather than being committed as a binary blob to this (public)
    repository.  The bundle ships a universal binary covering all supported
    Python versions, so no per-release commit to tk-desktop is required.

    The bundle path is derived from ``sys.prefix``, which inside the Desktop
    app always points to
    ``{App.app}/Contents/Resources/Python3``.
    One directory up from there is ``Resources/``, and the extensions live
    under ``Resources/Desktop/extensions/darwin_python3/``.

    :returns: The loaded osutils module, or ``None`` if it cannot be found.
    """
    # Derive bundle extension dir from sys.prefix, mirroring the same
    # 3-level-up logic used by AppBootstrap in tk-desktop-internal.
    # sys.prefix  = .../Shotgun.app/Contents/Resources/Python3
    # target dir  = .../Shotgun.app/Contents/Resources/Desktop/extensions/
    #               darwin_python3
    bundle_ext_dir = os.path.normpath(
        os.path.join(sys.prefix, "..", "Desktop", "extensions", "darwin_python3")
    )
    if not os.path.isdir(bundle_ext_dir):
        return None

    # Match the ABI tag for the running interpreter, e.g. "cpython-313".
    abi_prefix = f"osutils.cpython-{sys.version_info.major}{sys.version_info.minor}"
    for fname in sorted(os.listdir(bundle_ext_dir)):
        if not (fname.startswith(abi_prefix) and fname.endswith(".so")):
            continue
        so_path = os.path.join(bundle_ext_dir, fname)
        try:
            spec = importlib.util.spec_from_file_location("osutils", so_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            logger.debug("Loaded osutils from app bundle: %s", so_path)
            return module
        except Exception as e:
            logger.warning(
                "Could not load osutils from bundle %s: %s", so_path, e, exc_info=True
            )
        break  # Only try the first matching file.

    return None


use_mocked_osutils = True
if sys.platform == "darwin":
    # On macOS, osutils is required to control foreground/background app state.
    #
    # Try the app bundle first (SGD >= 3.0.0).  Fall back to the pre-compiled
    # binaries committed to darwin_python3/ in this package (Python 3.7-3.11)
    # for backward compatibility with older installers.
    osutils = _load_osutils_from_bundle()
    if osutils is None:
        try:
            # This library does not link against Qt, so the names are not
            # suffixed with the Qt version.
            from .darwin_python3 import osutils
        except Exception as e:
            logger.warning("Could not load osutils: %s", e, exc_info=True)
            osutils = None

    use_mocked_osutils = osutils is None

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
