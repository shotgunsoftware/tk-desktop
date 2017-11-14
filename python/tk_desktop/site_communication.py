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

from sgtk.platform.qt import QtCore
from .communication_base import CommunicationBase

from sgtk import LogManager

logger = LogManager.get_logger(__name__)


class SiteCommunication(QtCore.QObject, CommunicationBase):
    """
    Communication channel for the site engine to the project engine.
    """

    proxy_closing = QtCore.Signal()
    proxy_created = QtCore.Signal()

    def __init__(self, engine):
        """
        :param engine: Toolkit engine.
        """
        QtCore.QObject.__init__(self)
        CommunicationBase.__init__(self, engine)

    def _create_proxy(self, pipe, authkey):
        """
        Connects to the other process's RPC server.
        """
        CommunicationBase._create_proxy(self, pipe, authkey)
        self.proxy_created.emit()

    def start_server(self):
        """
        Sets up a server to communicate with the background process.
        """
        self._create_server()

        self.register_function(self._create_proxy, "create_app_proxy")
        self.register_function(self._destroy_proxy, "destroy_app_proxy")
        self.register_function(self._proxy_log, "proxy_log")

    def _notify_proxy_closure(self):
        """
        Disconnect from the app proxy.
        """
        self.proxy_closing.emit()
        try:
            self.call_no_response("signal_disconnect")
        except Exception, e:
            logger.warning("Error while sending signal to proxy to disconnect: %s", e)
        else:
            logger.debug("Proxy was signaled that we are disconnecting.")

    def _proxy_log(self, level, msg, args):
        """
        Outputs messages from the proxy into the application's logs.

        :param level: Level of the message.
        :param msg: Message to log.
        :param args: Arguments to log.
        """
        try:
            logger.log(level, "[PROXY] %s" % msg, *args)
        except Exception:
            logger.exception("Unexpected error when logging proxy message:")
            raise
