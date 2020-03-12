# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
VERY IMPORTANT. READ THIS BEFORE MODIFYING THIS FILE!!!!!

This module exposes the necessary low-level components to have the site and project
engine's of the Shotgun Desktop communicate with each other.

This API needs to remain fixed as it needs to be backward and forward compatible
with different versions of tk-desktop on both sides. This API used to be
implemented on top of the multiprocessing module, but unfortunately
the multiprocessing module in Python 3 forces data to be sent with pickle version 3
which is not understood by Python 2. Therefore, a new implementation was written
from scratch using HTTPServer and urllib.urlopen.

Also, this file needs to remain backwards compatible with older tk-core's, so
we can't import methods from Toolkit that may be too recent. For now, this
file is compatible with 0.18 and up, as it uses the LogManager, which
was introduced in 0.18.

The two main classes, and those that are part of the API, are RPCServerThread and
RPCProxy and they are defined at the top of this file. Every other classes are part
of the internal API of this module. The module is expected to be stored on disk as
a single file by older versions of tk-desktop, so we can't turn it into a module
with multiple files.

The relationship between the classes are as follow:

- RPCServerThread owns the Listener.
- The Listener is used to register methods and owns an HTTPServer that the Handler
  will invoke.

- The RPCProxy owns a Connection object to send data to the server.
- The Connection class owns an AsyncDispatcher that allows it to send fire-and-forget
  data to the server.
"""

import os
import sys
import uuid
import select
import logging
import threading
import traceback
import multiprocessing.connection

from sgtk.util import pickle
from tank_vendor import six

# We can't assume that the project we're talking to has a recent tk-core
# that ships with six, so we're detecting python 3 and making the right
# imports on our own.
PY3 = sys.version_info[0] >= 3
if PY3:
    from http.server import HTTPServer
    from http.server import SimpleHTTPRequestHandler
    from urllib.request import urlopen
    from queue import Queue
else:
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from urllib import urlopen
    from Queue import Queue


class SafeLogger(object):
    def __init__(self):
        self.__logger = None
        if self._is_debugging_rpc():
            self._simple_thread_ids = {}
            self._id_generation_lock = threading.Lock()

    def _is_debugging_rpc(self):
        return True  # "TK_DESKTOP_RPC_DEBUG" in os.environ

    def _get_simple_thread_id(self):
        ident = threading.current_thread()
        if ident not in self._simple_thread_ids:
            with self._id_generation_lock:
                self._simple_thread_ids[threading.current_thread()] = len(
                    self._simple_thread_ids
                )
        return self._simple_thread_ids[threading.current_thread()]

    def debug(self, *args, **kwargs):
        if self._logger:
            if self._is_debugging_rpc():
                args = list(args)
                if threading.current_thread().getName() != "MainThread":
                    args[0] = "Thread %d - " % self._get_simple_thread_id() + args[0]
                else:
                    args[0] = "Main Thread - " + args[0]
            self._logger.debug(*args, **kwargs)

    def warning(self, *args, **kwargs):
        if self._logger:
            self._logger.error(*args, **kwargs)

    def error(self, *args, **kwargs):
        if self._logger:
            self._logger.error(*args, **kwargs)

    def exception(self, *args, **kwargs):
        if self._logger:
            self._logger.exception(*args, **kwargs)

    @property
    def _logger(self):
        if self.__logger is None:
            try:
                from sgtk import LogManager
            except ImportError:
                return None
            else:
                self.__logger = LogManager.get_logger(__name__)
                # Only log debug messages if they are specifically requested.
                if self._is_debugging_rpc():
                    self.__logger.setLevel(logging.DEBUG)
                else:
                    self.__logger.setLevel(logging.INFO)
        return self.__logger


logger = SafeLogger()


class MultiprocessingRPCServerThread(threading.Thread):
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
        self.authkey = authkey or str(uuid.uuid1()).encode()

        # setup the server pipe
        if sys.platform == "win32":
            family = "AF_PIPE"
        else:
            family = "AF_UNIX"
        self.server = multiprocessing.connection.Listener(
            address=None, family=family, authkey=self.authkey
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
        logger.debug("multi server listening on '%s'", self.pipe)
        while self._is_closed is False:
            logger.debug("multi server thread is about to create a server")
            # test to see if there is a connection waiting on the pipe
            if sys.platform == "win32":
                # need to use win32 api for windows
                mpc_win32 = multiprocessing.connection.win32
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
                logger.debug("multi server thread could not create server")
                continue

            try:
                # connection waiting to be read, accept it
                logger.debug("multi server about to accept connection")
                connection = self.server.accept()
                logger.debug("multi server accepted connection")
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
                        "multi server calling '%s(%s, %s)'" % (func_name, args, kwargs)
                    )

                    try:
                        if func_name not in self._functions:
                            logger.error("unknown function call: '%s'" % func_name)
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
                            logger.debug("multi server got result '%s'" % result)

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
                if "connection" in locals():
                    logger.debug("multi server closing")
                    connection.close()
                    logger.debug("multi server closed")
        logger.debug("multi server thread shutting down")

    def close(self):
        """Signal the server to shut down connections and stop the run loop."""
        logger.debug("multi server setting flag to stop")
        self.server.close()
        if sys.platform == "win32":
            # Unblocks the call to accept from the server loop on Windows
            try:
                MultiprocessingRPCProxy(self.pipe, self.authkey)
            except Exception:
                pass
        self._is_closed = True


class MultiprocessingRPCProxy(object):
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
        logger.debug("multi client connecting to to %s", pipe)
        self._connection = multiprocessing.connection.Client(
            address=pipe, family=family, authkey=authkey
        )
        logger.debug("multi client connected to %s", pipe)

    def call_no_response(self, name, *args, **kwargs):
        msg = "multi client calling '%s(%s, %s)'" % (name, args, kwargs)
        if self._closed:
            raise RuntimeError("closed " + msg)
        # send the call through with args and kwargs
        logger.debug(msg)
        self._connection.send(pickle.dumps((False, name, args, kwargs)))

    def call(self, name, *args, **kwargs):
        msg = "multi client waiting call '%s(%s, %s)'" % (name, args, kwargs)
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
                    # On Unix, the poll return False, so we raise an error.
                    if self._closed:
                        raise RuntimeError("client closed while waiting for a response")
                    continue
            except IOError as e:
                # On Windows, an IOError is raised.
                if self._closed:
                    raise RuntimeError("client closed while waiting for a response")
                raise

        # read the result
        result = pickle.loads(self._connection.recv())
        logger.debug("multi client got result '%s'" % result)
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


class HttpRPCServerThread(threading.Thread):
    """
    Run an RPC Server in a subthread.

    Will listen on a named pipe for connection objects that are
    pickled tuples in the form (name, list, dictionary) where name
    is a lookup against functions registered with the server and
    list/dictionary are treated as args/kwargs for the function call.
    """

    def __init__(self, engine, authkey=None):
        """
        :param engine: The tk-desktop engine.
        """
        super(HttpRPCServerThread, self).__init__()
        self.engine = engine
        # need access to the engine to run functions in the main thread
        self._listener = Listener(engine, authkey)

    @property
    def pipe(self):
        """
        Connection string to the server.

        Note that this property is named pipe to be backwards compatible with
        previous versions of the API.
        """
        # Keep the IP hardcoded instead of set to localhost.
        # localhost host is about 5 times slower on Windows.
        return "http://127.0.0.1:%s" % self._listener.server_port

    @property
    def authkey(self):
        """
        Credential to connect to this server.
        """
        return self._listener.authkey

    def is_closed(self):
        """
        :returns: ``True`` if the server is closed, ``False`` if not.
        """
        return self._listener.is_closed()

    def list_functions(self):
        """
        Default method that returns the list of functions registered with the server.
        """
        return self._listener.list_functions()

    def register_function(self, func, name=None):
        """
        Add a new function to the list of functions being served.
        """
        return self._listener.register_function(func, name)

    def run(self):
        """
        Run the thread, accepting connections and then listening on them until
        they are closed.  Each message is a call into the function table.
        """
        logger.debug("http server thread listening on '%s'", self.pipe)
        try:
            self._listener.serve_forever()
        except BaseException as e:
            # Not catching the error here seems to not clean up the
            # server connection and it can deadlock the main thread.
            # Keep this except in place or you'll freeze when hitting
            # the back arrow on the project page of the desktop window.
            # Let's also be thorough and catch BaseException to make
            # sure CTRL-C still ends this thread peacefully.
            logger.debug("caught exception when serving forever:", exc_info=True)
        logger.debug("http server thread shutting down")

    def close(self):
        """
        Signal the server to shut down connections and stop the run loop.
        """
        logger.debug("requesting http server thread to close")
        self._listener.close()
        logger.debug("requested http server thread to close")


class HttpRPCProxy(object):
    """
    Client side for an RPC Server.

    Return attributes on the object as methods that will result in an RPC call
    whose results are returned as the return value of the method.

    DO NOT MODIFY THE INTERFACE OF THIS CLASS. IT IS USED ACROSS VERSIONS OF THE DESKTOP
    ENGINE AND SHOULD NOT BE MODIFIED UNDER ANY CIRCUMSTANCES.
    """

    def __init__(self, pipe, authkey):
        """
        :param str pipe: Connection to the server.
        :param str authkey: Credentials for the server.
        """
        self._closed = False
        self._connection = Connection(pipe, authkey)

    def call_no_response(self, name, *args, **kwargs):
        """
        Call a method on the server asynchronously.

        :param str name: Name of the method to call.
        :param args: Arguments to pass to the method
        :param kwargs: Keyword arguments to pass to the method.
        """
        msg = "http client calling '%s(%s, %s)'" % (name, args, kwargs)
        if self._closed:
            raise RuntimeError("closed " + msg)
        # send the call through with args and kwargs
        logger.debug(msg)
        self._connection.send(False, name, args, kwargs)

    def call(self, name, *args, **kwargs):
        """
        Call a method on the server synchronously.

        The call with return/raise the value/exception returned by the
        server.

        :param str name: Name of the method to call.
        :param args: Arguments to pass to the method
        :param kwargs: Keyword arguments to pass to the method.
        """
        msg = "http client waiting call '%s(%s, %s)'" % (name, args, kwargs)
        if self._closed:
            raise RuntimeError("closed " + msg)
        # send the call through with args and kwargs
        logger.debug(msg)
        result = self._connection.send(True, name, args, kwargs)
        if self._closed:
            raise RuntimeError("client closed while waiting for a response")
        logger.debug("http client got result '%s'" % result)
        # if an exception was returned raise it on the client side
        if isinstance(result, Exception):
            raise result
        # return the result as our own
        return result

    def is_closed(self):
        """
        Test if the connection to the server is still open.

        :returns: ``True`` is close, ``False`` if not.
        """
        return self._closed

    def close(self):
        """
        Close the connection to the server.
        """
        self._connection.close()
        self._closed = True


def get_rpc_proxy_factory(pipe):
    if pipe.startswith("http://"):
        return HttpRPCProxy
    else:
        return MultiprocessingRPCProxy


def get_rpc_server_factory(pipe):
    if pipe.startswith("http://"):
        return HttpRPCServerThread
    else:
        return MultiprocessingRPCProxy


RPCProxy = HttpRPCProxy
RPCServerThread = HttpRPCServerThread


class DualRPCServer(object):
    def __init__(self, engine):
        self._authkey = str(uuid.uuid1()).encode()
        self._multiprocessing_thread = MultiprocessingRPCServerThread(
            engine, self._authkey
        )
        self._http_thread = HttpRPCServerThread(engine, self._authkey)

    @property
    def pipes(self):
        """
        Connection. strings to both servers
        """
        return (self._multiprocessing_thread.pipe, self._http_thread.pipe)

    @property
    def engine(self):
        return self._multiprocessing_thread.engine

    @property
    def authkey(self):
        return self._authkey

    def is_closed(self):
        # Both are closed or both are opened, so no need to ask both.
        return self._multiprocessing_thread.is_closed()

    def list_functions(self):
        # Both have the same functions, so no need to ask both.
        return self._multiprocessing_thread.list_functions()

    def register_function(self, func, name=None):
        self._multiprocessing_thread.register_function(func, name)
        self._http_thread.register_function(func, name)

    def start(self):
        self._multiprocessing_thread.start()
        self._http_thread.start()

    def close(self):
        self._multiprocessing_thread.close()
        self._http_thread.close()

    def is_alive(self):
        return self._multiprocessing_thread.is_alive() or self._http_thread.is_alive()

    def join(self):
        self._multiprocessing_thread.join()
        self._http_thread.join()


##############################################################################
# Internal API starts here.

######################
# Server side classes


class Listener(object):
    """
    Server that allows methods to be called from a remote process.
    """

    def __init__(self, engine, authkey=None):
        """
        :param engine: Current Toolkit engine.
        """
        self._server = HTTPServer(("localhost", 0), Handler)
        self._server.listener = self

        # generate a random key for authentication
        self.authkey = authkey or str(uuid.uuid1()).encode()
        self.engine = engine
        self._is_closed = False

        # registry for methods to call for names that come via the connection
        self._functions = {"list_functions": self.list_functions}

    def register_function(self, func, name=None):
        """
        Register a function with the server.

        :param callable func: Method to call.
        :param name: Optional. If set, the function will be named as the parameter states.
            Otherwise, func.__name__ will be used.
        """
        if name is None:
            name = func.__name__

        # This method will be called from the main thread. If the server has been stopped, there
        # is no need to call the method.
        def wrapper(*args, **kwargs):
            if self._is_closed:
                return
            return func(*args, **kwargs)

        self._functions[name] = wrapper

    def list_functions(self):
        """
        Return a list of functions that can be invoked on the server.
        """
        return list(self._functions)

    def serve_forever(self):
        """
        Serve requests until the server is closed.
        """
        # Implement our own variant of serve_forever here.
        # HTTPServer.serve_forever will serve requests until HTTPServer.shut_down
        # is invoked. The problem with that flow is that if there is a request
        # currently being handled, the shut_down() call will block until
        # the request has been handled.
        #
        # This becomes an issue in this flow
        #
        # 1. Project engine makes an RPC call from the main thread.
        # 2. Site engine makes an RPC call from the main thread.
        # 3. Site engine receives the request to process the RPC and queues it for
        #    execution in the main thread.
        # 4. Project engine receives the request to process the RPC and queues it for
        #    execution in the main thread.
        # 5. At this point, both main threads are executing something and both
        #    have a second event in queue.
        # 6. Site engine wants to close the server thread using shut_down()
        #
        # 7. Deadlock!
        #
        # This happens because the site engine HTTP server is currently
        # waiting for a response from the main thread and we've just asked
        # from the main thread to shut_down(), which waits for the current
        # request to terminate before returning.
        #
        # The solution to this problem is to implement the loop ourselves
        # by calling handle_request manually. From the main thread
        # we simply raise a flag which will not block the main thread. When
        # the current event is done, the event queued by the server thread
        # will be executed and the serve_forever method will unblock,
        # read the flag and will be done.
        self._server.timeout = 1
        try:
            while self._is_closed is False:
                # This will wait for a request until the timeout
                # is reached. This means that we'll wait at most
                # one second before noticing we should be closing down.
                self._server.handle_request()
        finally:
            self._server.socket.close()

    def close(self):
        """
        Close the server.
        """
        self._is_closed = True

    def is_closed(self):
        """
        :returns: ``True`` is the server is closed, ``False`` if not.
        """
        return self._is_closed

    @property
    def server_port(self):
        """
        :returns: Port number used by the server.
        """
        return self._server.server_port


class Handler(SimpleHTTPRequestHandler):
    """
    Handle an HTTP request.
    """

    @property
    def _functions(self):
        """
        Shorthand to access the listener's function list.
        """
        return self.server.listener._functions

    @property
    def _engine(self):
        """
        Shorthand to access the engine we're exposing methods for.
        """
        return self.server.listener.engine

    def do_POST(self):
        """
        Handle request to execute a function from the listener.
        """
        response = None
        try:
            (authkey, (is_blocking, func_name, args, kwargs)) = self._read_request()
            logger.debug("http server calling '%s(%s, %s)'" % (func_name, args, kwargs))

            # Make sure the right credentials were sent.
            if authkey != self.server.listener.authkey:
                raise ValueError("invalid auth key")

            # Make sure the function exists.
            if func_name not in self._functions:
                logger.error("unknown function call: '%s'" % func_name)
                raise ValueError("unknown function call: '%s'" % func_name)

            # grab the function from the function table
            func = self._functions[func_name]

            # execute the function on the main thread, as it may to GUI work.
            if is_blocking:
                response = self._engine.execute_in_main_thread(func, *args, **kwargs)
            else:
                self._engine.async_execute_in_main_thread(func, *args, **kwargs)
                response = None

            logger.debug("http '%s' result: '%s" % (func_name, response))
        except Exception as e:
            response = e
            # if any of the above fails send the exception back to the client
            logger.exception("got exception during '%s" % func_name)
        finally:
            self._send_response(response)

    def log_request(self, code=None, size=None):
        """
        Prevent the server from outputting to stdout every single time
        a query is processed by the server.
        """

    def _read_request(self):
        """
        Read an incoming request and return the data.

        :returns: The data that was sent.
        """
        if PY3:
            content_len = int(self.headers.get("content-length", 0))
        else:
            content_len = int(self.headers.getheader("content-length", 0))

        body = self.rfile.read(content_len)
        try:
            return pickle.loads(body)
        except Exception:
            raise RuntimeError("Response could not be unserialized: %s" % body)

    def _send_response(self, body):
        """
        Send a response back to the client.

        :param body: Data to send back to the client.
        """
        raw_data = pickle.dumps(body)
        self.send_response(200, self.responses[200])
        self.send_header("Content-Type", "text/text")
        self.send_header("Content-Length", len(raw_data))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(six.ensure_binary(raw_data))


######################
# Client side classes


class AsyncDispatcher(threading.Thread):
    """
    Asynchronously sends payloads to the server.
    """

    def __init__(self, connection):
        """
        :param connection: The Connection object to use to send payloads.
        """
        super(AsyncDispatcher, self).__init__()
        self._queue = Queue()
        self._shut_down_requested = False
        self._connection = connection

    def send(self, payload):
        """
        Queue a payload to be sent asynchronously.
        :param payload: Data to send.
        """
        self._queue.put(payload)

    def shutdown(self):
        """
        Stop the dispatching thread.
        """
        # Sets the shut down now flag
        self._shut_down_requested = True
        # Insert dummy data to wake up the thread
        # if nothing is currently in the queue
        self._queue.put(None)

    def run(self):
        """
        Dispatch payloads to the server.

        This method returns when ``shutdown`` is called on the AsyncDispatcher.
        """
        while True:
            # Job might raise an error, but we don't care
            # this was an asynchronous call.
            try:
                payload = self._queue.get()
                # If a shutdown request was made.
                if self._shut_down_requested:
                    break
                # We're in the background thread, so we can send
                # a blocking request now, as urlopen is blocking
                # anyway.
                self._connection._send(payload)
            except Exception:
                logger.exception("Error was raised from RPC dispatching thread:")


class Connection(object):
    """
    Connection to the other process's server.
    """

    def __init__(self, address, authkey):
        """
        :param str address: Address of the server.
        :param str authkey: Credentials to the server.
        """
        self._address = address
        self._authkey = authkey

        self._async_dipsatcher = AsyncDispatcher(self)
        self._async_dipsatcher.start()

    def close(self):
        """
        Close the connection to the server.
        """
        self._async_dipsatcher.shutdown()

    def send(self, is_blocking, func_name, args, kwargs):
        """
        Call a function on the server synchronously or not.

        :param bool is_blocking: If ``True``, the call will block until the server
            completes the task and the value/exception will be returned/raised by this
            method. If ``False``, the call will be queued for delivery and the method
            returns None.
        """
        payload = (is_blocking, func_name, args, kwargs)
        if is_blocking:
            return self._send(payload)
        else:
            self._async_dipsatcher.send(payload)

    def _send(self, payload):
        """
        Send a payload to the server.

        The call will block until the server completes the task and the value/exception
        will be returned/raised by this method.

        :param payload: Data to send.
        """
        payload = pickle.dumps((self._authkey, payload))
        r = urlopen(self._address, data=six.ensure_binary(payload))
        response = pickle.loads(r.read())
        if isinstance(response, Exception):
            raise response
        return response
