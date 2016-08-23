# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys
import traceback
import cPickle as pickle


def start_engine(data):
    """
    Start the tk-desktop engine given a data dictionary like the one passed
    to the launch_python hook.
    """
    sys.path.append(data["core_python_path"])

    # make sure we don't inherit the GUI's pipeline configuration
    os.environ["TANK_CURRENT_PC"] = data["config_path"]

    import sgtk
    sgtk.util.append_path_to_env_var("PYTHONPATH", data["core_python_path"])

    # If the core supports the shotgun_authentication module and the pickle has
    # a current user, we have to set the authenticated user.
    if hasattr(sgtk, "set_authenticated_user"):
        # Retrieve the currently authenticated user for this process.
        from tank_vendor.shotgun_authentication import ShotgunAuthenticator
        user = ShotgunAuthenticator(sgtk.util.CoreDefaultsManager()).get_default_user()
        sgtk.set_authenticated_user(user)

    tk = sgtk.sgtk_from_path(data["config_path"])
    tk._desktop_data = data["proxy_data"]
    ctx = tk.context_from_entity("Project", data["project"]["id"])
    return sgtk.platform.start_engine("tk-desktop", tk, ctx)


def start_app(engine):
    """
    Run the QApplication for the given tk-desktop engine.
    """

    # If we're running the new engine that knows how to start the app, delegate the
    # task to it
    if hasattr(engine, "start_app"):
        return engine.start_app()

    # Otherwise run the legacy code.
    if engine.has_ui:
        from tank.platform.qt import QtGui

        app = QtGui.QApplication([])
        app.setQuitOnLastWindowClosed(False)
        app.setApplicationName("%s Python" % engine.context.project["name"])

        # set default icon
        python_icon = os.path.realpath(os.path.join(
            os.path.dirname(__file__),
            "..", "..", "resources", "python_icon.png"))
        app.setWindowIcon(QtGui.QIcon(python_icon))

        # Let the engine know we've created the app
        engine.register_qapplication(app)

        # use the toolkit look and feel
        engine._initialize_dark_look_and_feel()

        result = 0
        while True:
            # loop until we are signaled to close, in case an app accidentally quits the app
            result = app.exec_()
            if not engine.connected:
                # we have been signaled to quit rather than waiting for more commands
                break
        return result

    else:  # not engine.has_ui
        # wait for the engine communication channel to shut down
        engine.msg_server.join()
        return 0

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

    # build a message for the GUI signaling that an error occurred
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    msg = pickle.dumps((False, "engine_startup_error", [exc_value, ''.join(lines)], {}))
    connection.send(msg)
    connection.close()
