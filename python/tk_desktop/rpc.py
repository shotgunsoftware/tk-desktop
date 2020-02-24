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

# We can't assume that the project we're talking to has a recent tk-core
# that ships with six, so we're detecting python 3 and making the right
# imports on our own.
PY3 = sys.version_info[0] >= 3
if PY3:
    import pickle
    from http.server import HTTPServer
    from http.server import SimpleHTTPRequestHandler
    from urllib.request import urlopen
    from queue import Queue
else:
    try:
        import cPickle as pickle
    except ImportError:
        import pickle

    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from urllib import urlopen
    from Queue import Queue

from sgtk import LogManager

logger = LogManager.get_logger(__name__)

# Only log debug messages if they are specifically requested.
if "TK_DESKTOP_RPC_DEBUG" in os.environ:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


class RPCServerThread(threading.Thread):
    """
    Run an RPC Server in a subthread.

    Will listen on a named pipe for connection objects that are
    pickled tuples in the form (name, list, dictionary) where name
    is a lookup against functions registered with the server and
    list/dictionary are treated as args/kwargs for the function call.
    """

    def __init__(self, engine):
        """
        :param engine: The tk-desktop engine.
        """
        super(RPCServerThread, self).__init__()
        self.engine = engine
        # need access to the engine to run functions in the main thread
        self._listener = Listener(engine)

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
        logger.debug("server thread listening on '%s'", self.pipe)
        try:
            self._listener.serve_forever()
        except BaseException:
            # Not catching the error here seems to not clean up the
            # server connection and it can deadlock the main thread.
            # Keep this except in place or you'll freeze when hitting
            # the back arrow on the project page of the desktop window.
            # Let's also be thorough and catch BaseException to make
            # sure CTRL-C still ends this thread peacefully.
            pass
        logger.debug("server thread shutting down")

    def close(self):
        """
        Signal the server to shut down connections and stop the run loop.
        """
        logger.debug("requesting server thread to close")
        self._listener.close()
        logger.debug("requested server thread close request to close")


class RPCProxy(object):
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
        msg = "client calling '%s(%s, %s)'" % (name, args, kwargs)
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
        msg = "client waiting call '%s(%s, %s)'" % (name, args, kwargs)
        if self._closed:
            raise RuntimeError("closed " + msg)
        # send the call through with args and kwargs
        logger.debug(msg)
        result = self._connection.send(True, name, args, kwargs)
        if self._closed:
            raise RuntimeError("client closed while waiting for a response")
        logger.debug("client got result '%s'" % result)
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


##############################################################################
# Internal API starts here.

######################
# Server side classes


class Listener(object):
    """
    Server that allows methods to be called from a remote process.
    """

    def __init__(self, engine):
        """
        :param engine: Current Toolkit engine.
        """
        self._server = HTTPServer(("localhost", 0), Handler)
        self._server.timeout = 1

        self._server.listener = self

        self.authkey = str(uuid.uuid1())  # generate a random key for authentication
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
        # HTTPServer.serve_forever will server requests until HTTP
        try:
            while self._is_closed is False:
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
            logger.debug("server calling '%s(%s, %s)'" % (func_name, args, kwargs))

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

            logger.debug("'%s' result: '%s" % (func_name, response))
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
        raw_data = pickle.dumps(body, protocol=0)
        self.send_response(200, self.responses[200])
        self.send_header("Content-Type", "text/text")
        self.send_header("Content-Length", len(raw_data))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(raw_data)


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
        payload = pickle.dumps((self._authkey, payload), protocol=0)
        r = urlopen(self._address, data=payload)
        response = pickle.loads(r.read())
        if isinstance(response, Exception):
            raise response
        return response
