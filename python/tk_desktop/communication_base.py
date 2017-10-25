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

from .rpc import RPCServerThread, RPCProxy

from sgtk import LogManager

logger = LogManager.get_logger(__name__)


class CommunicationBase(object):
    """
    Communication channel base class.
    """

    def __init__(self, engine):
        """
        :param engine: Toolkit engine.
        """
        self._engine = engine
        self._msg_server = None
        self._proxy = None

    @property
    def is_connected(self):
        """
        Indicates whether there a live connection.

        :rtype: bool
        """
        return (
            self._proxy is not None and
            not self._proxy.is_closed()
        )

    def shut_down(self):
        """
        Disconnects from the other process and shuts down the local server.
        """
        logger.debug("Shutting down communication channel...")

        # Be super careful when closing the proxy, because it can be in an inconsistent state and
        # throw errors.
        if self._proxy is not None:
            try:
                self._notify_proxy_closure()
            except Exception:
                logger.exception("Error while destroying app proxy:")
            else:
                logger.debug("Destroyed app proxy.")

            self._destroy_proxy()

        # close down our server thread
        if self._msg_server is not None:
            self._msg_server.close()
            logger.debug("Closed message server.")
            self._msg_server = None

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
        return self._proxy.call_no_response(name, *args, **kwargs)

    def _create_proxy(self, pipe, authkey):
        """
        Connects to the other process's RPC server.
        """
        logger.info("Connecting to gui pipe %s" % pipe)
        self._proxy = RPCProxy(pipe, authkey)
        logger.debug("Connected to the proxy server.")

    def _create_server(self):
        """
        Launches an RPC server.
        """
        logger.debug("Starting RPC server")
        self._msg_server = RPCServerThread(self._engine)
        self._msg_server.start()

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

    def _destroy_proxy(self):
        """
        Disconnects from the background process's RPC server. This method is actually invoked from the
        background process to inform the Desktop app that it is about to shut down.
        """
        # Notify clients that the background process requested a shut down.
        if self._proxy is not None:
            try:
                self._proxy.close()
            except Exception, e:
                logger.warning("Error disconnecting from proxy: %s", e)
            else:
                logger.debug("Disconnected from the proxy.")
            finally:
                self._proxy = None
