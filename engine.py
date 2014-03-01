# Copyright (c) 2013 Shotgun Software Inc.
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
import logging
import cPickle as pickle
import logging.handlers

import multiprocessing.connection

from PySide import QtGui
from PySide import QtCore

from tank.platform import Engine


class RPCServerThread(QtCore.QThread):
    def __init__(self, engine, parent=None):
        QtCore.QThread.__init__(self, parent)

        self._functions = {
            'list_functions': self.list_functions,
        }

        self.engine = engine

        self.authkey = str(uuid.uuid1())
        self.server = multiprocessing.connection.Listener(
            address=None, family='AF_UNIX', authkey=self.authkey)
        self.pipe = self.server.address

    def list_functions(self):
        return self._functions.keys()

    def register_function(self, func, name=None):
        if name is None:
            name = func.__name__
        self._functions[name] = func

    def run(self):
        print "Listening on pipe: %s" % self.pipe
        while True:
            connection = self.server.accept()
            try:
                while True:
                    func_name, args, kwargs = pickle.loads(connection.recv())
                    try:
                        func = self._functions[func_name]
                        result = self.engine.execute_in_main_thread(func, *args, **kwargs)
                        connection.send(pickle.dumps(result))
                    except Exception as e:
                        connection.send(pickle.dumps(e))
            except EOFError:
                pass


class RPCProxy(object):
    def __init__(self, pipe, authkey):
        self._connection = multiprocessing.connection.Client(
            address=pipe, family='AF_UNIX', authkey=authkey)

    def __getattr__(self, name):
        def do_rpc(*args, **kwargs):
            self._connection.send(pickle.dumps((name, args, kwargs)))
            result = pickle.loads(self._connection.recv())
            if isinstance(result, Exception):
                raise result
            return result
        return do_rpc


class DesktopEngine(Engine):
    def __init__(self, *args, **kwargs):
        self.has_gui = True

        # mapping from namespaces to gui builders
        self.__gui_map = {}

        # initialize engine logging
        platform_lookup = {
            'darwin': os.path.join(os.path.expanduser("~"), "Library", "Logs", "Shotgun", "tk-desktop.log"),
            'win32': os.path.join(os.environ.get("APPDATA", "Foo"), "Shotgun", "tk-desktop.log"),
            'linux': None,
        }

        fname = platform_lookup.get(sys.platform)

        if fname is None:
            raise NotImplementedError("Unknown platform: %s" % sys.platform)

        log_dir = os.path.dirname(fname)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self._logger = logging.getLogger("tk-desktop")
        handler = logging.handlers.RotatingFileHandler(fname, maxBytes=1024*1024, backupCount=5)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

        # Now continue with the standard initialization
        Engine.__init__(self, *args, **kwargs)

        # start messaging server
        self.msg_server = RPCServerThread(self)
        self.msg_server.register_function(self.trigger_gui, 'trigger_gui')
        self.msg_server.register_function(self.trigger_callback, 'trigger_callback')
        self.msg_server.register_function(self.create_app_proxy, 'create_app_proxy')
        self.msg_server.register_function(self.open_project_locations, 'open_project_locations')

        self.msg_server.start()

    def init_engine(self):
        if self.get_setting("debug_logging", False):
            self._logger.setLevel(logging.DEBUG)

        bootstrap_data = getattr(self.sgtk, '_desktop_data', None)
        if bootstrap_data is not None:
            if 'proxy_pipe' in bootstrap_data and 'proxy_auth' in bootstrap_data:
                self.has_gui = False
                pipe = bootstrap_data['proxy_pipe']
                auth = bootstrap_data['proxy_auth']
                self._logger.info("Connecting to gui pipe %s" % pipe)
                self.proxy = RPCProxy(pipe, auth)

    def open_project_locations(self):
        paths = self.context.filesystem_locations
        for disk_location in paths:

            # get the setting
            system = sys.platform

            # run the app
            if system == "linux2":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)

            exit_code = os.system(cmd)
            if exit_code != 0:
                self.log_error("Failed to launch '%s'!" % cmd)

    def register_app_proxy(self, pipe, authkey):
        self.proxy.create_app_proxy(pipe, authkey)

    def create_app_proxy(self, pipe, authkey):
        self.proxy = RPCProxy(pipe, authkey)

    def register_callback(self, namespace, command, callback):
        self.__gui_map[(namespace, command)] = callback

    def call_callback(self, namespace, command, *args, **kwargs):
        self.proxy.trigger_callback(namespace, command, *args, **kwargs)

    def trigger_callback(self, namespace, command, *args, **kwargs):
        callback = self.__gui_map.get((namespace, command))
        callback(*args, **kwargs)

    def register_gui(self, namespace, callback):
        """ Register a callback to build a gui when a namespace is triggered """
        self.__gui_map[namespace] = callback

    def trigger_build_gui(self, namespace):
        self.proxy.trigger_gui(namespace)

    def trigger_gui(self, namespace):
        callback = self.__gui_map.get(namespace)

        if callback is not None:
            parent = self.systray.get_app_widget(namespace)
            callback(parent)

    def run(self):
        self._run_gui()

    def _run_gui(self):
        # Initialize PySide app
        self.app = QtGui.QApplication.instance()
        if self.app is None:
            QtGui.QApplication.setStyle("cleanlooks")
            self.app = QtGui.QApplication(sys.argv)
            css_file = os.path.join(self.disk_location, "resources", "dark.css")
            f = open(css_file)
            css = f.read()
            f.close()
            self.app.setStyleSheet(css)

        # update the icon
        icon = QtGui.QIcon(":res/default_systray_icon")
        self.app.setWindowIcon(icon)

        # Initialize System Tray
        tk_desktop = self.import_module("tk_desktop")
        self.systray = tk_desktop.SystemTrayWindow()
        return self.app.exec_()

    def log_debug(self, msg, *args):
        self._logger.debug(msg, *args)

    def log_info(self, msg, *args):
        self._logger.info(msg, *args)

    def log_warning(self, msg, *args):
        self._logger.warn(msg, *args)

    def log_error(self, msg, *args):
        self._logger.error(msg, *args)
