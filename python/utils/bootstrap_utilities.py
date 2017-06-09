# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Bootstrap utilities for the Project-level tk-desktop engine.

While this file gets executed by the background process running the desktop engine,
the path to this file is actually passed as an argument to the background process. The
path is actually to a file that is package with the site-level tk-desktop engine.
As such, the site-level engine has control over how the project-level tk-desktop
engine is bootstrapped and finalized.
"""

import os
import sys
import traceback
import cPickle as pickle
import multiprocessing.connection

logger = None


class LameRPCProxy(object):
    """
    Client side for an RPC Server.

    Return attributes on the object as methods that will result in an RPC call
    whose results are returned as the return value of the method.
    """
    # timeout in seconds to wait for a response
    LISTEN_TIMEOUT = 2

    def __init__(self, pipe, authkey):
        self._closed = False

        # connect to the server via the pipe using authkey for authentication
        if sys.platform == "win32":
            family = "AF_PIPE"
        else:
            family = "AF_UNIX"
        logger.debug("client connecting to to %s", pipe)
        self._connection = multiprocessing.connection.Client(
            address=pipe, family=family, authkey=authkey)
        logger.debug("client connected to %s", pipe)

    def call_no_response(self, name, *args, **kwargs):
        msg = "client calling '%s(%s, %s)'" % (name, args, kwargs)
        if self._closed:
            raise EOFError("closed " + msg)
        # send the call through with args and kwargs
        logger.debug(msg)
        self._connection.send(pickle.dumps((False, name, args, kwargs)))

    def call(self, name, *args, **kwargs):
        msg = "client waiting call '%s(%s, %s)'" % (name, args, kwargs)
        if self._closed:
            raise EOFError("closed " + msg)
        # send the call through with args and kwargs
        logger.debug(msg)
        self._connection.send(pickle.dumps((True, name, args, kwargs)))

        # wait until there is a result, pause to check if we have been closed
        while True:
            if self._connection.poll(self.LISTEN_TIMEOUT):
                # have a response waiting, grab it
                break
            else:
                # no response waiting, see if we need to stop the client
                if self._closed:
                    raise EOFError("client closed while waiting for a response")
                continue
        # read the result
        result = pickle.loads(self._connection.recv())
        logger.debug("client got result '%s'" % result)
        # if an exception was returned raise it on the client side
        if isinstance(result, Exception):
            raise result
        # return the result as our own
        return result

    def is_closed(self):
        return self._closed

    def close(self):
        # close down the client connection
        logger.debug("closing connection")
        self._connection.close()
        self._closed = True


def start_engine(data):
    """
    Start the tk-desktop engine given a data dictionary like the one passed
    to the launch_python hook.
    """
    sys.path.append(data["core_python_path"])

    # make sure we don't inherit the GUI's pipeline configuration
    del os.environ["TANK_CURRENT_PC"]

    import sgtk
    sgtk.LogManager().initialize_base_file_handler("tk-desktop")

    global logger
    logger = sgtk.LogManager.get_logger(__name__)

    from sgtk.authentication import deserialize_user

    user = deserialize_user(os.environ["SHOTGUN_DESKTOP_CURRENT_USER"])

    manager_settings = data["manager_settings"]

    def pre_engine_start_callback(ctx):
        proxy.close()
        ctx.sgtk._desktop_data = data["proxy_data"]

    proxy = LameRPCProxy(
        data["proxy_data"]["proxy_pipe"],
        data["proxy_data"]["proxy_auth"]
    )

    def progress_callback(value, msg):
        if not proxy.is_closed():
            proxy.call_no_response(
                "bootstrap_progress", value, msg
            )

    manager = sgtk.bootstrap.ToolkitManager(user)
    manager.pre_engine_start_callback = pre_engine_start_callback
    manager.caching_policy = manager_settings["caching_policy"]
    manager.plugin_id = manager_settings["plugin_id"]
    manager.base_configuration = manager_settings["base_configuration"]
    manager.bundle_cache_fallback_paths = manager_settings["bundle_cache_fallback_paths"]
    manager.pipeline_configuration = manager_settings["pipeline_configuration"]
    manager.progress_callback = progress_callback

    engine = manager.bootstrap_engine("tk-desktop", data["project"])
    return engine


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
