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

import imp
import importlib.util
import inspect
import logging
import os
import pprint
import sys
import traceback


class ProxyLoggingHandler(logging.Handler):
    """
    Logs messages through the proxy.
    """

    def __init__(self, proxy):
        """
        :param proxy: Connection to the main process.
        :type proxy: rpc.RPCProxy
        """
        super().__init__()
        self._proxy = proxy

    def emit(self, record):
        """
        Emits a log back to the host.
        """
        # Note any changes made here, should also be considered for the
        # `DesktopEngineProjectImplementation._emit_log_message` method in the
        # desktop_engine_project_implementation module.

        # Do not send logs if the connection is closed!
        if self._proxy.is_closed():
            return

        # If we have exception details, we need to format these and combine them with the message, as the traceback
        # object can't be serialize and passed over the proxy.
        if record.exc_info:
            formatted_tracback = "".join(traceback.format_tb(record.exc_info[2]))
            msg = "{msg}\n{traceback}".format(
                msg=record.msg, traceback=formatted_tracback
            )
        else:
            msg = record.msg

        # Perform string interpolation safely
        if record.args:
            msg = msg % record.args

        try:
            self._proxy.call_no_response("proxy_log", record.levelno, msg, [])
        except Exception:
            # Ignore log failures, this is important, as we don't want logging to
            # cause issues.
            pass


def _create_proxy(data):
    """
    Create a proxy based on the data received from the PTR desktop app.

    :returns: A connection back to the PTR desktop app.
    """
    # Connect to the main desktop process so we can send updates to it.
    # We're not guanranteed if the py or pyc file will be passed back to us
    # from the desktop due to write permissions on the folder.
    rpc_lib = imp.load_source("rpc", data["rpc_lib_path"])
    return rpc_lib.RPCProxy(
        data["proxy_data"]["proxy_pipe"], data["proxy_data"]["proxy_auth"]
    )


def _enumerate_per_line(items):
    """
    Enumerate all items from an array, one line at a time.

    For example,
        - one
        - two
        - three

    :returns: The formatted output.
    """
    return "\n".join("- {}".format(item) for item in items)


def _env_not_set_or_split(var_name):
    """
    Format a PATH-like environment variable for output.

    :param str var_name: Name of the env var.
    :returns: "Not Set" if variable is not set, a bullet list otherwise.
    """
    if var_name not in os.environ:
        return "Not Set"
    else:
        # Add a \n before the first item so each item in the output start from the
        # beginning of the line. Otherwise you'd get.
        # varname: - one
        # - two
        # - three.
        return "\n" + _enumerate_per_line(os.environ[var_name].split(os.path.pathsep))


def _log_startup_information():
    """
    Log information about the Python subprocess that was just started.
    """
    import sgtk

    logger = sgtk.LogManager.get_logger(__file__)
    logger.debug("------------------ Desktop Utilities Startup ------------------")
    logger.debug(
        """
Python
======
Executable: {executable}
Version: {major}.{minor}.{micro}
sys.path:
{sys_path}

Environment variables
=====================
PATH: {path}
PYTHONHOME: {python_home}
PYTHONPATH: {python_path}
        """.format(
            executable=sys.executable,
            major=sys.version_info.major,
            minor=sys.version_info.minor,
            micro=sys.version_info.micro,
            sys_path=_enumerate_per_line(sys.path),
            path=_env_not_set_or_split("PATH"),
            python_home=os.environ.get("PYTHONHOME", "Not Set"),
            python_path=_env_not_set_or_split("PYTHONPATH"),
        )
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

        self._proxy = _create_proxy(self._raw_data)
        try:
            # Set up logging with the rpc.
            self._handler = ProxyLoggingHandler(self._proxy)
            sgtk.LogManager().root_logger.addHandler(self._handler)
            _log_startup_information()

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
            # Instead, we'll handle the exception here and use the proxy
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

        self._proxy.call_no_response("bootstrap_progress", value, msg)


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
        __init__py_location = inspect.getsourcefile(sgtk)  # python/tank/__init__.py

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
        python_icon = os.path.realpath(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "resources", "python_icon.png"
            )
        )
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

    :param proxy: An optional proxy object to use when sending the
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

    # If we were given an proxy object and it's open, use that
    # to send the message.
    if proxy is not None and not proxy.is_closed():
        proxy.call_no_response(
            "engine_startup_error",
            exc_type.__name__,
            str(exc_value),
            "".join(lines),
        )
        return

    proxy = _create_proxy(data)

    try:
        proxy.call_no_response(
            "engine_startup_error",
            exc_type.__name__,
            str(exc_value),
            "".join(lines),
        )
    finally:
        try:
            proxy.close()
        except Exception:
            pass


def logger_via_proxy(data, message):
    """
    Sends a log message to tk-desktop via the RPC proxy.

    This function uses the RPC proxy to send log messages to the main tk-desktop process.
    It is particularly useful for logging messages before the engine is fully initialized
    or when direct access to the tk-desktop logging system is not available.

    :param data: A dictionary containing proxy connection details, including the path
                 to the RPC library and proxy authentication information.
    :param message: The log message to send to tk-desktop.
    """
    if data["core_python_path"] not in sys.path:
        sys.path.insert(0, data["core_python_path"])
    import sgtk

    proxy = _create_proxy(data)
    handler = ProxyLoggingHandler(proxy)
    sgtk.LogManager().initialize_custom_handler(handler)
    logger = sgtk.LogManager.get_logger(__file__)
    logger.error(message)
    proxy.close()


def execute_pre_initialization_hook(data):
    """
    Executes the 'hook_pre_initialization' hook.

    This function dynamically loads and executes the 'hook_pre_initialization' hook,
    which is responsible for performing early initialization tasks before the engine
    is fully initialized. These tasks may include importing necessary libraries,
    setting environment variables, or preparing the environment to ensure compatibility
    with PySide6 and other dependencies.

    If a custom hook is not defined in the advanced configuration (`tk-desktop.yml`),
    the function falls back to dynamically loading the default hook located in the
    'hooks' directory of the project.

    :param data: A dictionary containing configuration and runtime details, including:
                 - `hook_pre_initialization`: The path of the configuration pipeline.
                 - `proxy_data`: Proxy connection details for logging.
                 - `rpc_lib_path`: Path to the RPC library for communication.
    """

    try:
        hook_path = data.get("hook_pre_initialization")
        if not hook_path:
            return

        # Dynamically load and execute the hook
        spec = importlib.util.spec_from_file_location("pre_initialization", hook_path)
        hook_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hook_module)

        # Execute the `execute` method of the `PreInitialization` class
        hook_class = getattr(hook_module, "PreInitialization", None)
        if hook_class is None or not hasattr(hook_class, "execute"):
            raise AttributeError(
                f"The 'PreInitialization' class or its 'execute' method is missing in the hook: {hook_path}"
            )
        hook_class.execute()
    except Exception as e:
        logger_via_proxy(
            data, f"An error occurred while executing the pre-initialization hook: {e}"
        )
        raise
