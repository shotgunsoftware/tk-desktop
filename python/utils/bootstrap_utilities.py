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
import traceback
import cPickle as pickle


def start_engine(data):
    """
    Start the tk-desktop engine given a data dictionary like the one passed
    to the launch_python hook.
    """
    sys.path.append(data["core_python_path"])

    import sgtk
    sgtk.util.append_path_to_env_var("PYTHONPATH", data["core_python_path"])

    tk = sgtk.sgtk_from_path(data["config_path"])
    tk._desktop_data = data["proxy_data"]
    ctx = tk.context_from_entity("Project", data["project"]["id"])
    return sgtk.platform.start_engine("tk-desktop", tk, ctx)


def start_app(engine):
    """ Run the QApplication for the given tk-desktop engine """
    from PySide import QtGui

    QtGui.QApplication.setStyle("cleanlooks")
    app = QtGui.QApplication([])
    app.setStyleSheet(engine._get_standard_qt_stylesheet())
    app.setQuitOnLastWindowClosed(False)
    app.exec_()


def handle_error(data):
    """
    Attempt to communicate the error back to the GUI proxy given a data
    dictionary like the one passed to the launch_python hook.
    """
    from multiprocessing.connection import Client
    if sys.platform == "win32":
        family = "AF_PIPE"
    else:
        family = "AF_UNIX"

    connection = Client(
        address=data["proxy_data"]["proxy_pipe"],
        family=family,
        authkey=data["proxy_data"]["proxy_auth"],
    )

    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    msg = pickle.dumps((
        "engine_startup_error",
        [exc_value, ''.join(lines)],
        {"__proxy_expected_return": False},
    ))
    connection.send(msg)
    connection.close()
