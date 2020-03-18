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

from .communication_base import CommunicationBase
from .rpc import get_rpc_server_factory

from sgtk.platform import get_logger

logger = get_logger(__name__)


class ProjectCommunication(CommunicationBase):
    """
    Communication channel for the project engine to the site engine.
    """

    def __init__(self, engine):
        """
        :param engine: Toolkit engine.
        """
        CommunicationBase.__init__(self, engine)
        self._connected = False

    def connect_to_server(self, pipe, auth, disconnect_callback):
        """
        Sets up a server to communicate with the foreground process and connects
        back to the site engine.
        """
        # create the connection to the site engine.
        self._create_proxy(pipe, auth)

        # Register our side of the pipe as the current app proxy.
        # Based on the pipe we received, which is either multiprocessing based
        # or http based, we'll create the right server to listen to request
        # from the main desktop process.
        #
        # The logic is this: If the main desktop process supports http,
        # we'll always use that to connect back because this is the safest
        # way to exchange data. If the main desktop process didn't support http
        # then the pipe will be a file path and therefore get_rpc_server_factory
        # will return a multiprocessing-based server.
        self._create_server(get_rpc_server_factory(pipe))
        self.call("create_app_proxy", self.server_pipe, self.server_authkey)
        self._connected = True

        # Register to the other server's disconnect
        def wrapper():
            self._connected = False
            self._destroy_proxy()
            disconnect_callback()

        self.register_function(wrapper, "signal_disconnect")

    @property
    def server_pipe(self):
        """
        :returns: The server's pipe.
        """
        return self._msg_server.pipe

    def shut_down(self):
        """
        Disconnects from the other process and shuts down the local server.
        """
        self._connected = False
        CommunicationBase.shut_down(self)

    def join(self):
        """
        Waits for the message server to shut down.
        """
        self._msg_server.join()

    def _notify_proxy_closure(self):
        """
        Called during the shutdown to notify the server that this process is side of the communication
        is shutting down.
        """
        self.call_no_response("destroy_app_proxy")

    def _signal_disconnect(self):
        self._connected = False

    @property
    def connected(self):
        """
        Indicates if the inter-process communication is up and running.
        """
        return self._connected
