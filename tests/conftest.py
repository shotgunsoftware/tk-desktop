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
from unittest.mock import MagicMock

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

# Also expose the tk_desktop package itself so tests can use
# "from tk_desktop.X import Y" style imports.
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")),
)

# ── Inject lightweight sgtk / Qt stubs ────────────────────────────────────────
# Tests that exercise tk_desktop source modules need sgtk and Qt to be
# importable even when the full Flow Production Tracking toolkit is not
# installed.  We inject minimal stubs into sys.modules here (conftest runs
# before any test file is imported) so every test in the suite benefits.
#
# Rules:
#  • Only inject a stub when the real package is NOT already present.
#  • QtCore.QObject must be a real Python class so that sub-classing works
#    (SiteCommunication inherits from it at class-definition time).
#  • QtCore.Signal must return a callable mock so .emit() can be used.

try:
    import sgtk as _sgtk_check  # noqa: F401
    _sgtk_available = True
except ImportError:
    _sgtk_available = False

if not _sgtk_available:
    _log_manager = MagicMock()
    _log_manager.get_logger.return_value = MagicMock()

    _sgtk = MagicMock()
    _sgtk.LogManager = _log_manager

    # QObject must be an independent stub class, not `object` itself.
    # Using plain `object` causes an MRO conflict because CommunicationBase
    # also inherits from `object`:
    #   class SiteCommunication(object, CommunicationBase) → MRO error.
    # A dedicated stub class resolves this:
    #   class SiteCommunication(_QObjectStub, CommunicationBase) → valid MRO.
    class _QObjectStub:
        """Minimal stand-in for QtCore.QObject in test environments."""

    _qt_core = MagicMock()
    _qt_core.QObject = _QObjectStub
    _qt_core.Signal = MagicMock(side_effect=lambda *a, **kw: MagicMock())

    _qt_module = MagicMock()
    _qt_module.QtCore = _qt_core

    # tank.util is imported by rpc.py as:
    #   from tank.util import pickle as tk_pickle, is_windows
    # The sub-module must be in sys.modules *before* the import so Python
    # doesn't try to walk the 'tank' package (which would fail because our
    # 'tank' stub is a MagicMock, not a real package).
    _tank_util = MagicMock()
    _tank_util.is_windows = MagicMock(return_value=(sys.platform == "win32"))

    _stub_modules = {
        "sgtk": _sgtk,
        "sgtk.platform": _sgtk.platform,
        "sgtk.platform.qt": _qt_module,
        "sgtk.util": _sgtk.util,
        "sgtk.bootstrap": MagicMock(),
        "sgtk.deploy": MagicMock(),
        "tank": _sgtk,
        "tank.platform": _sgtk.platform,
        "tank.platform.qt": _qt_module,
        "tank.util": _tank_util,
        "tank_vendor": MagicMock(),
        "tank_vendor.shotgun_authentication": MagicMock(),
    }
    for _mod_name, _mod in _stub_modules.items():
        sys.modules.setdefault(_mod_name, _mod)
