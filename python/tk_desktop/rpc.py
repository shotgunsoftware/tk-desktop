# Copyright (c) 2014 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


import uuid
import select
import logging
import cPickle as pickle
import multiprocessing.connection

from PySide import QtCore

logger = logging.getLogger('tk-desktop.rpc')
logger.setLevel(logging.DEBUG)


class RPCServerThread(QtCore.QThread):
    """
    Run an RPC Server in a subthread.

    Will listen on a named pipe for connection objects that are
    pickled tuples in the form (name, list, dictionary) where name
    is a lookup against functions registered with the server and
    list/dictionary are treated as args/kwargs for the function call.

    The special method '__close_connection' will trigger the server
    to close the current connection and start accepting new ones.

    The special kwarg '__proxy_expected_return' that defaults to True
    can be used to keep the server from sending the return value of the
    method call back to the client side.
    """
    def __init__(self, engine, parent=None):
        QtCore.QThread.__init__(self, parent)
        self._logger = logging.getLogger('tk-desktop.rpc')

        # registry for methods to call for names that come via the connection
        self._functions = {
            'list_functions': self.list_functions,
        }

        self._stop = False  # used to shut down the thread cleanly
        self.engine = engine  # need access to the engine to run functions in the main thread
        self.authkey = str(uuid.uuid1())  # generate a random key for authentication

        # setup the server pipe
        self.server = multiprocessing.connection.Listener(
            address=None, family='AF_UNIX', authkey=self.authkey)

        # grab the name of the pipe
        self.pipe = self.server.address

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
        self._functions[name] = func

    def run(self):
        """
        Run the thread, accepting connections and then listening on them until
        they are closed.  Each message is a call into the function table.
        """
        self._logger.debug("listening on '%s'", self.pipe)
        while True:
            # test to see if there is a connection waiting on the pipe
            (rd, _, _) = select.select([self.server._listener._socket], [], [], 2)
            if not rd:
                # nothing ready, see if we need to stop the server, if not keep waiting
                if self._stop:
                    break
                continue

            # connection waiting to be read, accept it
            connection = self.server.accept()
            self._logger.debug("accepted connection")
            try:
                while True:
                    # test to see if there is data waiting on the connection
                    if not connection.poll(2):
                        # no data waiting, see if we need to stop the server, if not keep waiting
                        if self._stop:
                            break
                        continue

                    # data coming over the connection is a tuple of (name, args, kwargs)
                    (func_name, args, kwargs) = pickle.loads(connection.recv())

                    # special case where we do not call a registered method and break
                    # out of the listen loop
                    if func_name == "__close_connection":
                        self._logger.debug("closing connection")
                        connection.send(pickle.dumps(None))
                        connection.close()
                        break

                    self._logger.debug("calling '%s(%s, %s)'" % (func_name, args, kwargs))

                    # figure out if the client is expecting a response
                    expected_return = True
                    if '__proxy_expected_return' in kwargs:
                        expected_return = kwargs['__proxy_expected_return']
                        # make sure to clean out the kwarg so it doesn't pass to the function
                        del kwargs['__proxy_expected_return']

                    try:
                        if not func_name in self._functions:
                            self._logger.error("unknown function call: '%s'" % func_name)
                            raise ValueError("unknown function call: '%s'" % func_name)

                        # grab the function from the function table
                        func = self._functions[func_name]

                        # execute the function on the main thread.  It may do GUI work.
                        result = self.engine.execute_in_main_thread(func, *args, **kwargs)

                        # if the client expects the results, send them along
                        if expected_return:
                            self._logger.debug("got result '%s'" % result)
                            connection.send(pickle.dumps(result))
                    except Exception as e:
                        # if any of the above fails send the exception back to the client
                        if expected_return:
                            self._logger.error("got exception '%s'" % e)
                            connection.send(pickle.dumps(e))
            except (EOFError, IOError):
                # let these errors just keep serving new connections
                pass

        self._logger.info("server closing")

    def close(self):
        """Signal the server to shut down connections and stop the run loop."""
        self._stop = True


class RPCProxy(object):
    """
    Client side for an RPC Server.

    Return attributes on the object as methods that will result in an RPC call
    whose results are returned as the return value of the method.
    """
    def __init__(self, pipe, authkey):
        self._logger = logging.getLogger('tk-desktop.rpc')

        # connect to the server via the pipe using authkey for authentication
        self._connection = multiprocessing.connection.Client(
            address=pipe, family='AF_UNIX', authkey=authkey)
        self._logger.debug("connected to %s", pipe)

    def __getattr__(self, name):
        # all attributes are methods that result in an rpc call
        def do_rpc(*args, **kwargs):
            # figure out if we expect a return value
            expected_return = True
            if '__proxy_expected_return' in kwargs:
                expected_return = kwargs['__proxy_expected_return']

            # send the call through with args and kwargs
            self._connection.send(pickle.dumps((name, args, kwargs)))

            # if we expect a response read it
            if expected_return:
                result = pickle.loads(self._connection.recv())

                # if an exception was returned raise it on the client side
                if isinstance(result, Exception):
                    raise result

                # return the result as our own
                return result
        return do_rpc

    def close(self):
        # close down the client connection
        self._connection.close()
