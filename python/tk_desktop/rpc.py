# Copyright (c) 2020 Shotgun Software Inc.
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
import uuid
import select
import logging
import threading
import time
import traceback
import multiprocessing.connection

# We have to import Python's pickle to serialize our data.
# tk-core's sgtk.util.pickle module assumes too much about the data
# type that is stored in the pickle and assumes the output of a dump
# can always be turned into a utf-8 encoded string, which is false.
# Therefore, we'll simply take the raw pickle and send it over the wire.
from tank_vendor import six
from tank_vendor.six.moves import cPickle as py_pickle
from tank.util import pickle as tk_pickle, is_windows

if is_windows():
    # This is not ideal. We're importing a private Python module.
    # However, if we didn't and instead relied on pywin32 then we would
    # have to expect clients to install it.
    if six.PY2:
        mpc_win32 = multiprocessing.connection.win32
    else:
        # If we ever seen this code raising an error with a new Python version,
        # it's likely because the attribute has changed name.
        mpc_win32 = multiprocessing.connection._winapi


class pickle:
    """
    Provides a Python 2/3 compatible shim for the pickle module.

    Unfortunately, the shim in tk-core returns a string instead
    of a binary string, which would complicate the code here,
    so we're doing to rely on the default implementation
    so that the rest of the multiprocessing-based code and remain
    the same instead of peppering the code with calls to protocol=2
    and the right loads.
    """

    loads = staticmethod(tk_pickle.loads)

    @staticmethod
    def dumps(payload):
        return py_pickle.dumps(payload, protocol=2)


from sgtk import LogManager


class Logger(object):
    """
    Wrapper around a logger object. It augments the logged information when
    TK_DESKTOP_RPC_DEBUG is turned on. It also prevents logging from every single
    RPC call, which would slow down the logging process. In fact, logging
    from the Shotgun Desktop with this environment variable sends the subprocess
    into an infinite loop as logging anything from the background process
    means doing an RPC call. If from the RPC module we log messages as well,
    we end up in an infinite logging loop an the project never finishes loading.
    As such, TK_DESKTOP_RPC_DEBUG should only be used when running tests.

    One could argue why we need this, when a simple logger formatter would do
    to print the thread id and current time.
    The problem is that the logger formatter option prints the real thread id,
    which is hard to read because it is a 64bit value. When looking at test logs,
    this makes it hard to differentiate between tests. Doing in this way makes
    it a lot easier. Threads could also be named, but then in a test suite
    you wouldn't be able to differentiate between a message coming from a test
    or leaking from another test, which has been an issue in the past.
    """

    def __init__(self):
        self._logger = LogManager.get_logger(__name__)
        # Only log debug messages if they are specifically requested.
        if self._is_debugging_rpc():
            self._simple_thread_ids = {}
            self._id_generation_lock = threading.Lock()
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger.setLevel(logging.INFO)

    def _is_debugging_rpc(self):
        """
        True if debug logging should be activated, False otherwise.
        """
        return "TK_DESKTOP_RPC_DEBUG" in os.environ

    def _get_simple_thread_id(self):
        """
        Translates the current thread object into a simple integer for
        easy debugging.
        """
        ident = threading.current_thread()
        # If we've never seen this thread object before
        if ident not in self._simple_thread_ids:
            # Generate a new thread id.
            with self._id_generation_lock:
                self._simple_thread_ids[threading.current_thread()] = len(
                    self._simple_thread_ids
                )
        return self._simple_thread_ids[threading.current_thread()]

    def debug(self, *args, **kwargs):
        """
        Log debug message.
        """
        if self._is_debugging_rpc():
            args = list(args)
            if threading.current_thread().getName() != "MainThread":
                args[0] = "Thread %d - " % self._get_simple_thread_id() + args[0]
            else:
                args[0] = "Main Thread - " + args[0]
            args[0] = "%f - %s" % (time.time(), args[0])
        self._logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        """
        Log warning message.
        """
        self._logger.info(*args, **kwargs)

    def warning(self, *args, **kwargs):
        """
        Log warning message.
        """
        self._logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        """
        Log error message.
        """
        self._logger.error(*args, **kwargs)

    def exception(self, *args, **kwargs):
        """
        Log exception message.
        """
        self._logger.exception(*args, **kwargs)


logger = Logger()


class SafePickleConnection(object):
    """
    Wrap the multiprocessing.connection.Connection object
    so that any calls to send and recv data is caught
    and reimplemented in a way that works between Python 2 and
    Python 3.

    Python 3's Connection.send always uses protocol 3 of pickle,
    which Python 2 does not understand. So we now force the
    protocol to 2 all the time.
    """

    def __init__(self, conn):
        self._conn = conn

    def send(self, payload):
        payload = py_pickle.dumps(payload, protocol=2)
        self._conn.send_bytes(payload)

    def recv(self):
        payload = self._conn.recv_bytes()
        if six.PY3:
            return py_pickle.loads(payload, encoding="bytes")
        else:
            return py_pickle.loads(payload)

    def __getattr__(self, name):
        return getattr(self._conn, name)


class RPCServerThread(threading.Thread):
    """
    Run an RPC Server in a subthread.

    Will listen on a named pipe for connection objects that are
    pickled tuples in the form (name, list, dictionary) where name
    is a lookup against functions registered with the server and
    list/dictionary are treated as args/kwargs for the function call.
    """

    # timeout in seconds to wait for a request
    LISTEN_TIMEOUT = 2

    # Special return value from the main thread signifying the callable wasn't executed because
    # the server is tearing down. Ideally we would raise an exception but execute_in_main_thread
    # doesn't propagate exceptions.
    _SERVER_WAS_STOPPED = "INTERNAL_DESKTOP_MESSAGE : SERVER_WAS_STOPPED"

    def __init__(self, engine, authkey=None):
        threading.Thread.__init__(self)

        # registry for methods to call for names that come via the connection
        self._functions = {
            "list_functions": self.list_functions,
        }

        self._is_closed = False  # used to shut down the thread cleanly
        # need access to the engine to run functions in the main thread
        self.engine = engine
        # generate a random key for authentication
        self.authkey = authkey or str(uuid.uuid1())

        # setup the server pipe
        if sys.platform == "win32":
            family = "AF_PIPE"
        else:
            family = "AF_UNIX"
        self.server = multiprocessing.connection.Listener(
            address=None, family=family, authkey=six.ensure_binary(self.authkey)
        )
        # grab the name of the pipe
        self.pipe = self.server.address

    def is_closed(self):
        return self._is_closed

    def list_functions(self):
        """
        Default method that returns the list of functions registered with the server.
        """
        return list(self._functions)

    def register_function(self, func, name=None):
        """
        Add a new function to the list of functions being served.
        """
        if name is None:
            name = func.__name__

        # This method will be called from the main thread. If the server has been stopped, there
        # is no need to call the method.
        def wrapper(*args, **kwargs):
            if self._is_closed:
                # Return special value indicating the server was stopped.
                return self._SERVER_WAS_STOPPED
            return func(*args, **kwargs)

        self._functions[name] = wrapper

    def run(self):
        """
        Run the thread, accepting connections and then listening on them until
        they are closed.  Each message is a call into the function table.
        """
        logger.debug("server listening on '%s'", self.pipe)
        while self._is_closed is False:
            logger.debug("server thread is about to create a server")
            ready = False
            # test to see if there is a connection waiting on the pipe
            if sys.platform == "win32":
                try:
                    mpc_win32.WaitNamedPipe(
                        self.server.address, self.LISTEN_TIMEOUT * 1000
                    )
                    ready = True
                except WindowsError as e:
                    logger.debug("Error during WaitNamedPipe:", exc_info=True)
                    if e.args[0] not in (
                        mpc_win32.ERROR_SEM_TIMEOUT,
                        mpc_win32.ERROR_PIPE_BUSY,
                    ):
                        raise
                    ready = False
            else:
                # can use select on osx and linux
                (rd, _, _) = select.select(
                    [self.server._listener._socket], [], [], self.LISTEN_TIMEOUT
                )
                ready = len(rd) > 0

            if not ready:
                logger.debug("server thread could not create server")
                continue

            connection = None
            try:
                # connection waiting to be read, accept it
                logger.debug("server about to accept connection")
                connection = SafePickleConnection(self.server.accept())
                logger.debug("server accepted connection")
                while self._is_closed is False:
                    # test to see if there is data waiting on the connection
                    has_data = connection.poll(self.LISTEN_TIMEOUT)

                    # see if we need to stop the server
                    if self._is_closed:
                        return

                    # If we timed out waiting for data, go back to sleep.
                    if not has_data:
                        continue

                    # data coming over the connection is a tuple of (name, args, kwargs)
                    (respond, func_name, args, kwargs) = pickle.loads(connection.recv())
                    logger.debug(
                        "server calling '%s(%s, %s)'" % (func_name, args, kwargs)
                    )

                    try:
                        if func_name not in self._functions:
                            logger.error(
                                "unknown function call: '%s', expecting one of '%s'"
                                % (func_name, self.list_functions())
                            )
                            raise ValueError("unknown function call: '%s'" % func_name)

                        # grab the function from the function table
                        func = self._functions[func_name]

                        # execute the function on the main thread.  It may do GUI work.
                        result = self.engine.execute_in_main_thread(
                            func, *args, **kwargs
                        )

                        # If the RPC server was stopped, don't bother trying to reply, the connection
                        # will have been broken on the client side and this will avoid an error
                        # on the server side when calling send.
                        if self._SERVER_WAS_STOPPED != result:
                            # if the client expects the results, send them along
                            logger.debug("server got result '%s'" % result)

                            if respond:
                                connection.send(pickle.dumps(result))
                    except Exception as e:
                        # if any of the above fails send the exception back to the client
                        logger.error("got exception '%s'" % e)
                        logger.debug("   traceback:\n%s" % traceback.format_exc())
                        if respond:
                            connection.send(pickle.dumps(e))
            except (EOFError, IOError):
                # let these errors go
                # just keep serving new connections
                pass
            finally:
                # It's possible we failed accepting, so the variable may not be defined.
                if connection is not None:
                    logger.debug("server closing")
                    connection.close()
                    logger.debug("server closed")
        logger.debug("server thread shutting down")

    def close(self):
        """Signal the server to shut down connections and stop the run loop."""
        logger.debug("server setting flag to stop")
        self.server.close()
        self._is_closed = True
        if sys.platform == "win32":
            # The accept call blocks until a client is available.
            # Unfortunately closing the connection on Windows does not
            # cause accept to unblock and raise an error, so we have to force
            # accept to unblock by connecting to the server. The server thread
            # will then test the _is_closed flag and shut down.
            try:
                RPCProxy(self.pipe, self.authkey)
            except Exception:
                pass


class RPCProxy(object):
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
        self._connection = SafePickleConnection(
            multiprocessing.connection.Client(
                address=pipe, family=family, authkey=six.ensure_binary(authkey)
            )
        )
        logger.debug("client connected to %s", pipe)

    def call_no_response(self, name, *args, **kwargs):
        msg = "client calling '%s(%s, %s)'" % (name, args, kwargs)
        if self._closed:
            raise RuntimeError("closed " + msg)
        # send the call through with args and kwargs
        logger.debug(msg)
        self._connection.send(pickle.dumps((False, name, args, kwargs)))

    def call(self, name, *args, **kwargs):
        msg = "client waiting call '%s(%s, %s)'" % (name, args, kwargs)
        if self._closed:
            raise RuntimeError("closed " + msg)
        # send the call through with args and kwargs
        logger.debug(msg)
        self._connection.send(pickle.dumps((True, name, args, kwargs)))

        # wait until there is a result, pause to check if we have been closed
        while True:
            try:
                if self._connection.poll(self.LISTEN_TIMEOUT):
                    # have a response waiting, grab it
                    break
                else:
                    # If the connection was closed while we polled, raise an error.
                    if self._closed:
                        raise RuntimeError("client closed while waiting for a response")
                    continue
            except IOError:
                # An exception is raised on Windows when the connection is closed
                # during polling instead of simply returning False.
                if self._closed:
                    raise RuntimeError("client closed while waiting for a response")
                raise

        # read the result
        try:
            result = pickle.loads(self._connection.recv())
        except OSError:
            # On Linux, an exception will be raised here instead.
            if self._closed:
                raise RuntimeError("client closed while waiting for a response")

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
