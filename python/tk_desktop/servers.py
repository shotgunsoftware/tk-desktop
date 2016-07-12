# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Implements communication channels between the desktop app and the background process.
"""

import logging

from .rpc import RPCServerThread, RPCProxy
from sgtk.platform.qt import QtCore


class SiteCommunication(QtCore.QObject):
    """
    Communication channel for the site engine to the background process, aka slave.
    """

    proxy_closing = QtCore.Signal()

    def __init__(self, engine):
        """
        :param engine: Toolkit engine.
        """
        QtCore.QObject.__init__(self)
        self._engine = engine
        self._msg_server = None
        self._proxy = None

    def shut_down(self):
        """
        Disconnects from the slave process and shuts down the local server.
        """
        self._log("Shutting down communication channel...")
        # Disconnect from the client
        if self._proxy is not None:
            self._signal_disconnect()
            self._destroy_app_proxy()

        # Stop listening for messages.
        if self._msg_server is not None:
            self._msg_server.close()
            self._msg_server = None

    @property
    def server_pipe(self):
        """
        :returns: The server's pipe.
        """
        return self._msg_server.pipe

    @property
    def server_authkey(self):
        """
        :returns: The server's authorization key.
        """
        return self._msg_server.authkey

    def register_function(self, callable, function_name):
        """
        Registers a function for the background process to call.

        :param callable: Callable object to execute when the function is called from the background
            process.

        :param function_name: Name to register the callable under.
        """
        self._msg_server.register_function(callable, function_name)

    def call(self, name, *args, **kwargs):
        """
        Calls a method on the background process and waits for the result.

        :param name: Name of the method to call.
        :param args: Position arguments for the call.
        :param kwargs: Named arguments for the call.
        """
        return self._proxy.call(name, *args, **kwargs)

    def call_no_response(self, name, *args, **kwargs):
        """
        Calls a method on the background process and does not wait for the result.

        :param name: Name of the method to call.
        :param args: Position arguments for the call.
        :param kwargs: Named arguments for the call.
        """
        return self._proxy.call(name, *args, **kwargs)

    def start_server(self):
        """
        Sets up a server to communicate with the background process.
        """
        self._log("Starting RPC server")
        self._msg_server = RPCServerThread(self._engine)

        self._msg_server.register_function(self._create_app_proxy, "create_app_proxy")
        self._msg_server.register_function(self._destroy_app_proxy, "destroy_app_proxy")
        self._msg_server.register_function(self._proxy_log, "proxy_log")

        self._msg_server.start()

    def _create_app_proxy(self, pipe, authkey):
        """
        Connects to the background process's RPC server. This method is actually invoked from the
        background process to inform the Desktop app that it is ready.
        """
        assert(self._proxy is None)
        self._proxy = RPCProxy(pipe, authkey)
        self._log("Connected to the proxy server.")

    def _destroy_app_proxy(self):
        """
        Disconnects from the background process's RPC server. This method is actually invoked from the
        background process to inform the Desktop app that it is about to shut down.
        """
        # Notify clients that the background process requested a shut down.
        self.proxy_closing.emit()
        if self._proxy is not None:
            try:
                self._proxy.close()
            except Exception, e:
                self._warn("Error disconnecting from proxy: %s", e)
            else:
                self._log("Disconnected from the proxy.")
            finally:
                self._proxy = None

    def _signal_disconnect(self):
        """
        Disconnect from the app proxy.
        """
        try:
            self._proxy.call_no_response("signal_disconnect")
        except Exception, e:
            self._warn("Error while sending signal to proxy to disconnect: %s", e)
        else:
            self._log("Proxy was signaled that we are disconnecting.")

        self._destroy_app_proxy()

    def _log(self, msg, *args):
        """
        Writes a message to the debug logger.

        :param msg: Message to log.
        :param args: Arguments to log.
        """
        self._engine._logger.debug(msg, *args)

    def _warn(self, msg, *args):
        """
        Writes a message to the warning logger.

        :param msg: Message to log.
        :param args: Arguments to log.
        """
        self._engine._logger.warning(msg, *args)

    def _proxy_log(self, level, msg, args):
        """
        Outputs messages from the proxy into the application's logs.

        :param level: Level of the message.
        :param msg: Message to log.
        :param args: Arguments to log.
        """
        self._engine._logger.log(level, "[PROXY] %s" % msg, *args)
