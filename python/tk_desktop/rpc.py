# Copyright (c) 2014 Shotgun Software Inc.
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
import traceback
import cPickle as pickle
import multiprocessing.connection

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

    # timeout in seconds to wait for a request
    LISTEN_TIMEOUT = 2

    # Special return value from the main thread signifying the callable wasn't executed because
    # the server is tearing down. Ideally we would raise an exception but execute_in_main_thread
    # doesn't propagate exceptions.
    _SERVER_WAS_STOPPED = "INTERNAL_DESKTOP_MESSAGE : SERVER_WAS_STOPPED"

    def __init__(self, engine):
        threading.Thread.__init__(self)

        # registry for methods to call for names that come via the connection
        self._functions = {
            "list_functions": self.list_functions,
        }

        self._stop = False  # used to shut down the thread cleanly
        self.engine = engine  # need access to the engine to run functions in the main thread
        self.authkey = str(uuid.uuid1())  # generate a random key for authentication

        # setup the server pipe
        if sys.platform == "win32":
            family = "AF_PIPE"
        else:
            family = "AF_UNIX"
        self.server = multiprocessing.connection.Listener(
            address=None, family=family, authkey=self.authkey)

        # grab the name of the pipe
        self.pipe = self.server.address

    def is_closed(self):
        return self._stop

    def list_functions(self):
        """
        Default method that returns the list of functions registered with the server.
        """
        return self._functions.keys()

    def register_function(self, func, name=None):
        """
        Add a new function to the list of functions being served.
        """
        if name is None:
            name = func.__name__

        # This method will be called from the main thread. If the server has been stopped, there
        # is no need to call the method.
        def wrapper(*args, **kwargs):
            if self._stop:
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
        while True:
            # test to see if there is a connection waiting on the pipe
            if sys.platform == "win32":
                # need to use win32 api for windows
                mpc_win32 = multiprocessing.connection.win32
                try:
                    mpc_win32.WaitNamedPipe(self.server.address, self.LISTEN_TIMEOUT * 1000)
                    ready = True
                except WindowsError, e:
                    if e.args[0] not in (mpc_win32.ERROR_SEM_TIMEOUT, mpc_win32.ERROR_PIPE_BUSY):
                        raise
                    ready = False
            else:
                # can use select on osx and linux
                (rd, _, _) = select.select([self.server._listener._socket], [], [], self.LISTEN_TIMEOUT)
                ready = (len(rd) > 0)

            if not ready:
                # nothing ready, see if we need to stop the server, if not keep waiting
                if self._stop:
                    break
                continue

            # connection waiting to be read, accept it
            connection = self.server.accept()
            logger.debug("server accepted connection")
            try:
                while True:
                    # test to see if there is data waiting on the connection
                    has_data = connection.poll(self.LISTEN_TIMEOUT)

                    # see if we need to stop the server
                    if self._stop:
                        break

                    # If we timed out waiting for data, go back to sleep.
                    if not has_data:
                        continue

                    # data coming over the connection is a tuple of (name, args, kwargs)
                    (respond, func_name, args, kwargs) = pickle.loads(connection.recv())
                    logger.debug("server calling '%s(%s, %s)'" % (func_name, args, kwargs))

                    try:
                        if func_name not in self._functions:
                            logger.error("unknown function call: '%s'" % func_name)
                            raise ValueError("unknown function call: '%s'" % func_name)

                        # grab the function from the function table
                        func = self._functions[func_name]

                        # execute the function on the main thread.  It may do GUI work.
                        result = self.engine.execute_in_main_thread(func, *args, **kwargs)

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
                logger.debug("server closing")
                connection.close()

    def close(self):
        """Signal the server to shut down connections and stop the run loop."""
        logger.debug("server setting flag to stop")
        self._stop = True


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
