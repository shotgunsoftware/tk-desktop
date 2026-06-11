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

import subprocess

from sgtk.platform.qt import QtCore
from .bootstrap_process import terminate_process
from .communication_base import CommunicationBase

from sgtk import LogManager

logger = LogManager.get_logger(__name__)


class SiteCommunication(QtCore.QObject, CommunicationBase):
    """
    Communication channel for the site engine to the project engine.
    """

    proxy_closing = QtCore.Signal()
    proxy_created = QtCore.Signal()

    def __init__(self):
        CommunicationBase.__init__(self)
        QtCore.QObject.__init__(self)
        self._bootstrap_process = None

    def set_bootstrap_process(self, process: subprocess.Popen) -> None:
        """
        Registers the bootstrap subprocess and terminates any previous one.

        :param process: A :class:`subprocess.Popen` instance for the bootstrap process.
        """
        self._terminate_bootstrap_process()
        self._bootstrap_process = process

    def _terminate_bootstrap_process(self) -> None:
        """
        Terminates the bootstrap subprocess if one is still running.
        """
        process = self._bootstrap_process
        self._bootstrap_process = None
        terminate_process(process)

    def shut_down(self) -> None:
        """
        Overrides :meth:`CommunicationBase.shut_down` to also terminate the
        bootstrap subprocess after disconnecting from the RPC proxy.

        Called from the following locations:
        - ``desktop_window._about_to_quit``: user quits Desktop via menu / Alt+F4
        - ``desktop_window._on_back_to_projects_clicked``: user returns to the project browser
        - ``desktop_window.__launch_app_proxy_for_project``: before switching to a new project
        - ``desktop_engine_site_implementation.destroy_engine``: engine teardown
        """
        CommunicationBase.shut_down(self)
        self._terminate_bootstrap_process()

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
        except Exception as e:
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
