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
import imp
import logging
import inspect


class ProxyLoggingHandler(logging.Handler):
    """
    Logs messages through the proxy.
    """

    def __init__(self, proxy):
        """
        :param proxy: Connection to the main process.
        :type proxy: rpc.RPCProxy
        """
        # Call the __init__ directly since Python 2.6's logging.Handler doesn't
        # derive from object and hence doesn't support 'super'.
        logging.Handler.__init__(self)
        self._proxy = proxy

    def emit(self, record):
        """
        Emits a log back to the host.
        """
        # Do not send logs if the connection is closed!
        if self._proxy.is_closed():
            return

        try:
            self._proxy.call_no_response(
                "proxy_log", record.levelno, record.msg, record.args
            )
        except Exception:
            # If something couldn't be pickled, don't fret too much about it,
            # we'll format it ourselves instead.
            self._proxy.call_no_response(
                "proxy_log", record.levelno, (record.msg % record.args), []
            )


class Bootstrap(object):
    """
    Bootstraps the tk-desktop engine.
    """

    def __init__(self, data):
        """
        :param data: Dictionary of data passed down from the main desktop process.
        """
        # Extract the relevant information from the data
        self._raw_data = data
        self._proxy_data = data["proxy_data"]
        self._manager_settings = data["manager_settings"]
        self._project = data["project"]
        self._core_python_path = data["core_python_path"]
        self._rpc_lib_path = data["rpc_lib_path"]

        self._proxy = None
        self._handler = None
        self._user = None

    def start_engine(self):
        """
        Bootstraps the engine and launches it.
        """
        # Import Toolkit, but make sure we're not inheriting the parent process's current
        # pipeline configuration.
        sys.path.insert(0, self._core_python_path)
        import sgtk
        del os.environ["TANK_CURRENT_PC"]

        # Connect to the main desktop process so we can send updates to it.
        # We're not guanranteed if the py or pyc file will be passed back to us
        # from the desktop due to write permissions on the folder.
        rpc_lib = imp.load_source("rpc", self._rpc_lib_path)
        self._proxy = rpc_lib.RPCProxy(
            self._proxy_data["proxy_pipe"],
            self._proxy_data["proxy_auth"]
        )
        try:
            # Set up logging with the rpc.
            self._handler = ProxyLoggingHandler(self._proxy)
            sgtk.LogManager().root_logger.addHandler(self._handler)

            # Get the user we should be running as.
            self._user = sgtk.authentication.deserialize_user(
                os.environ["SHOTGUN_DESKTOP_CURRENT_USER"]
            )

            # Prepare the manager based on everything the bootstrap manager expected of us.
            manager = sgtk.bootstrap.ToolkitManager(self._user)
            manager.restore_settings(self._manager_settings)
            manager.pre_engine_start_callback = self._pre_engine_start_callback
            manager.progress_callback = self._progress_callback

            # We're now ready to start the engine.
            return manager.bootstrap_engine("tk-desktop", self._project)
        except Exception as exc:
            # We have a situation here where, on Windows, we end up with some
            # kind of leaked connection back to the server. This results in
            # the connection attempt from the handle_error function hanging
            # until the parent process is killed. The error is never reported
            # as a result.
            #
            # Instead, we'll handle the exception here and use the RPCProxy
            # connection we already have.
            handle_error(self._raw_data, self._proxy)
            exc.sgtk_exception_handled = True
            raise
        finally:
            # Make sure we're closing our proxy so the error reporting,
            # which also creates a proxy, can create its own. If there's an
            # error, make sure we catch it and ignore it. Then the finally
            # can do its job and propagate the real error if there was one.
            try:
                self._proxy.close()
            except:
                pass

    def _pre_engine_start_callback(self, ctx):
        """
        Called before the engine is started. Closes the proxy connection and removes out log handle.
        """
        import sgtk
        # At this point we need to close the proxy because we can't have two proxies connected
        # at the same sime, especially for logging, to the server.
        # When the engine starts it will set up its own logging.
        self._proxy.close()
        if hasattr(sgtk, "LogManager"):
            sgtk.LogManager().root_logger.removeHandler(self._handler)

        # The desktop engine expects the sgtk instance to have the _desktop_data attribute with
        # the proxy credentials in it.
        ctx.sgtk._desktop_data = self._proxy_data

    def _progress_callback(self, value, msg):
        """
        Reports bootstrap progress back to the main process.
        """
        # If the proxy hasn't been closed, report our progress.
        # Note here that is we haven't closed the proxy ourselves in pre_engine_start_callback,
        # but the main process has closed our connection, this code will raise an error.
        # This is great because if the host has closed the connection it means at their the process
        # crashes (yikes!) or that the user backed out of the project. In any case, it means
        # we can stop bootstrapping. This exception will then bubble all the way up and back outside
        # this file and we'll jump into "handle_error" at the bottom of this file. Jump over thread
        # to understand more what is going on.
        if self._proxy.is_closed():
            return

        self._proxy.call_no_response(
            "bootstrap_progress", value, msg
        )


def start_engine(data):
    """
    Start the tk-desktop engine given a data dictionary like the one passed
    to the launch_python hook.
    """
    engine = Bootstrap(data).start_engine()

    # Import Toolkit locally. We need to capture this Python path so we can use it to bootstrap.
    # inside another process.
    import sgtk
    if hasattr(sgtk, "get_sgtk_module_path"):
        python_folder = sgtk.get_sgtk_module_path()
    else:
        __init__py_location = inspect.getsourcefile(sgtk) # python/tank/__init__.py

        # If the path is not absolute, make it so.
        if not os.path.isabs(__init__py_location):
            __init__py_location = os.path.join(os.getcwd(), __init__py_location)

        tank_folder = os.path.dirname(__init__py_location)
        python_folder = os.path.dirname(tank_folder)

    sgtk.util.prepend_path_to_env_var("PYTHONPATH", python_folder)

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

        # NOTE
        # The following code is meant to run for very old verions of tk-desktop. It
        # should not be edited to support newer features.
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


def handle_error(data, proxy=None):
    """
    Attempt to communicate the error back to the GUI proxy given a data
    dictionary like the one passed to the launch_python hook. Note that
    if the server has already been closed (process crashes or user left the
    project) this will actually fail silently, which is alright as the main
    process doesnt't care about this one anymore.

    :param proxy: An optional RPCProxy object to use when sending the
        error to the server. If a proxy is not given, a client connection
        will be created on the fly.
    """
    # build a message for the GUI signaling that an error occurred
    exc_type, exc_value, exc_traceback = sys.exc_info()

    # There's a chance this exception was already handled by, in which
    # case we can ignore it.
    if hasattr(exc_value, "sgtk_exception_handled"):
        return

    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)

    # If we were given an RPCProxy object and it's open, use that
    # to send the message.
    if proxy is not None and not proxy.is_closed():
        proxy.call_no_response("engine_startup_error", exc_value, ''.join(lines))
        return

    from multiprocessing.connection import Client
    if sys.platform == "win32":
        family = "AF_PIPE"
    else:
        family = "AF_UNIX"

    try:
        connection = Client(
            address=data["proxy_data"]["proxy_pipe"],
            family=family,
            authkey=data["proxy_data"]["proxy_auth"],
        )
        msg = pickle.dumps((False, "engine_startup_error", [exc_value, ''.join(lines)], {}))
        connection.send(msg)
    finally:
        try:
            connection.close()
        except Exception:
            pass
