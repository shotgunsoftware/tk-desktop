# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

# This file needs to remain backwards compatible with older tk-core's, so
# we can import methods from Toolkit that may be too recent. For now, this
# file is compatible with 0.18 and up, as it uses the LogManager, which
# was introduce in 0.18.

import os
import sys
import uuid
import select
import logging
import threading
import traceback
import socket

# Try to import the fastest version of pickle we can.
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


import multiprocessing.connection

from sgtk import LogManager

logger = LogManager.get_logger(__name__)

# Only log debug messages if they are specifically requested.
if "TK_DESKTOP_RPC_DEBUG" in os.environ:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


class Listener(object):
    def __init__(self, engine, min_port=49152, max_port=65535):
        # According to the following link
        # https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml?&page=137
        # the port range 49152-65535 is free to use for everyone and is meant for dynamic servers
        # which is our case here.
        # range intervals are always [a, b[, so add 1 to include max_port.
        self._server = HTTPServer(("localhost", 0), Handler)

        self._server.listener = self

        self.authkey = str(uuid.uuid1())  # generate a random key for authentication
        if PY3:
            self.authkey = self.authkey.encode("utf8")

        self.engine = engine
        self._is_closed = False

        # registry for methods to call for names that come via the connection
        self._functions = {"list_functions": self.list_functions}

    def register_function(self, func, name=None):
        if name is None:
            name = func.__name__

        # This method will be called from the main thread. If the server has been stopped, there
        # is no need to call the method.
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        self._functions[name] = wrapper

    def list_functions(self):
        return list(self._functions)

    def serve_forever(self):
        self._server.serve_forever()

    def close(self):
        self._server.socket.close()
        self._is_closed = True

    def is_closed(self):
        return self._is_closed

    @property
    def server_port(self):
        return self._server.server_port


class Handler(SimpleHTTPRequestHandler):
    @property
    def _functions(self):
        return self.server.listener._functions

    @property
    def _engine(self):
        return self.server.listener.engine

    def do_POST(self):
        (is_blocking, func_name, args, kwargs) = self._read_request()

        logger.debug("server calling '%s(%s, %s)'" % (func_name, args, kwargs))
        response = None
        try:
            if func_name not in self._functions:
                logger.error("unknown function call: '%s'" % func_name)
                raise ValueError("unknown function call: '%s'" % func_name)

            # grab the function from the function table
            func = self._functions[func_name]

            # execute the function on the main thread.  It may do GUI work.
            result = self._engine.execute_in_main_thread(func, *args, **kwargs)

            # If the RPC server was stopped, don't bother trying to reply, the connection
            # will have been broken on the client side and this will avoid an error
            # on the server side when calling send.
            if self.server.listener.is_closed() is False:
                # if the client expects the results, send them along
                logger.debug("server got result '%s'" % result)
                response = result
        except Exception as e:
            # if any of the above fails send the exception back to the client
            logger.error("got exception '%s'" % e)
            logger.debug("   traceback:\n%s" % traceback.format_exc())

            if is_blocking:
                response = e
        self._send_response(200, response)

    def log_request(self, code=None, size=None):
        pass

    def _read_request(self):
        if PY3:
            content_type = self.headers.get("content-type")
            content_len = int(self.headers.get("content-length", 0))
        else:
            content_type = self.headers.getheader("content-type")
            content_len = int(self.headers.getheader("content-length", 0))

        body = self.rfile.read(content_len)
        try:
            return pickle.loads(body)
        except Exception:
            raise RuntimeError("Response could not be unserialized: %s" % body)

    def _send_response(self, code, body):
        raw_data = pickle.dumps(body, protocol=0)
        self.send_response(code, self.responses[code])
        self.send_header("Content-Type", "text/text")
        self.send_header("Content-Length", len(raw_data))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(raw_data)


class RPCServerThread(threading.Thread):
    """
    Run an RPC Server in a subthread.

    Will listen on a named pipe for connection objects that are
    pickled tuples in the form (name, list, dictionary) where name
    is a lookup against functions registered with the server and
    list/dictionary are treated as args/kwargs for the function call.
    """

    def __init__(self, engine):
        super(RPCServerThread, self).__init__()
        self.engine = engine
        # need access to the engine to run functions in the main thread
        self._listener = Listener(engine)

    @property
    def pipe(self):
        return "http://localhost:%s" % self._listener.server_port

    @property
    def authkey(self):
        return self._listener.authkey

    def is_closed(self):
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
        logger.debug("server listening on '%s'", self.pipe)
        try:
            self._listener.serve_forever()
        except Exception as e:
            if "bad file descriptor" not in str(e).lower():
                raise

    def close(self):
        """Signal the server to shut down connections and stop the run loop."""
        logger.debug("server setting flag to stop")
        self._listener.close()


class Dispatcher(threading.Thread):
    _shutdown_hint = "shutdown_hint"

    def __init__(self, emitter):
        super(Dispatcher, self).__init__()
        self._emitter = emitter
        self._queue = Queue()

    def queue_job(self, job):
        self._queue.put(job)

    def shutdown(self):
        self._queue.put(self._shutdown_hint)

    def run(self):
        while True:
            job = self._queue.get()
            if job == self._shutdown_hint:
                return
            # Job might raise an error, but we don't care
            # this was an asynchronous call.
            try:
                job()
            except Exception:
                pass


class Emitter(object):
    def __init__(self, address, authkey):
        self._address = address

    def send(self, payload):
        payload = pickle.dumps(payload, protocol=0)
        r = urlopen(self._address, data=payload)
        response = pickle.loads(r.read())
        if isinstance(response, Exception):
            raise response
        return response


class Connection(object):
    def __init__(self, address, authkey):
        self._emitter = Emitter(address, authkey)
        self._dispatcher = Dispatcher(self._emitter)
        self._dispatcher.start()

    def close(self):
        self._dispatcher.shutdown()

    def send(self, is_blocking, func_name, args, kwargs):
        payload = (is_blocking, func_name, args, kwargs)
        if is_blocking:
            return self._emitter.send(payload)
        else:
            self._dispatcher.queue_job(lambda: self._emitter.send(payload))


class RPCProxy(object):
    """
    Client side for an RPC Server.

    Return attributes on the object as methods that will result in an RPC call
    whose results are returned as the return value of the method.
    """

    def __init__(self, pipe, authkey):
        self._closed = False
        logger.debug("client connecting to to %s", pipe)
        self._connection = Connection(pipe, authkey)
        logger.debug("client connected to %s", pipe)

    def call_no_response(self, name, *args, **kwargs):
        msg = "client calling '%s(%s, %s)'" % (name, args, kwargs)
        if self._closed:
            raise RuntimeError("closed " + msg)
        # send the call through with args and kwargs
        logger.debug(msg)
        self._connection.send(False, name, args, kwargs)

    def call(self, name, *args, **kwargs):
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
        return self._closed

    def close(self):
        # close down the client connection
        logger.debug("closing connection")
        self._connection.close()
        self._closed = True
