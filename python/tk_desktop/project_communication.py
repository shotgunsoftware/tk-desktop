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
        Sets up a server to communicate with the background process and connects to the site engine.
        """
        # create the connection to the site engine.
        self._create_proxy(pipe, auth)

        # register our side of the pipe as the current app proxy
        self._create_server()
        self.call("create_app_proxy", self.server_pipe, self.server_authkey)
        self._connected = True

        # Register to the other server's disconnect
        def wrapper():
            self._connected = False
            self._destroy_proxy()
            disconnect_callback()
        self.register_function(wrapper, "signal_disconnect")

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
