# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.
#

from sgtk.platform.qt import QtCore
import sgtk

from sgtk import LogManager

logger = LogManager.get_logger(__name__)


class ProjectSyncingCancelledError(Exception):
    """
    Raised to notify the thread that the user aborted the syncing process.
    """
    pass


class ProjectSynchronizationThread(QtCore.QThread):
    """
    Synchronizes a project on disk from a thread.
    """

    report_progress = QtCore.Signal(float, str)
    sync_failed = QtCore.Signal(str)
    sync_success = QtCore.Signal(str, object)

    def __init__(self, manager, project):
        """
        :param manager: ToolkitManager to prepare to prepare the engine with.
        :param project: Project for which we require the engine to be prepared.
        """
        super(ProjectSynchronizationThread, self).__init__()
        self._toolkit_manager = manager
        self._toolkit_manager.progress_callback = self._report_progress
        self._abort = False
        self._engine = sgtk.platform.current_engine()
        self._project = project

    def _report_progress(self, pct, msg):
        """
        Emits progress reports to the main thread.

        :param pct: Value between 0 and 1 indicating how far along is the syncing.
        :param msg: Current action taking place.
        """
        if self._abort:
            logger.debug("About to raise ProjectSyncingCancelledError")
            # This exception will fall through to this class' run method, which will catch the
            # error.
            raise ProjectSyncingCancelledError()
        else:
            self.report_progress.emit(pct, msg)

    def run(self):
        """
        Syncs a project's configuration to disk and caches the necessary bundles.
        """
        try:
            # Make sure the config is downloaded and the bundles cached.
            config_path, descriptor = self._toolkit_manager.prepare_engine(None, self._project)
        except ProjectSyncingCancelledError:
            logger.debug("Caught ProjectSyncingCancelledError.")
            # Someone has canceled the syncing. Simply abort. No need to emit anything, abort is fire
            # and forget.
            pass
        except Exception as error:
            logger.exception(str(error))
            self.sync_failed.emit(str(error))
        else:
            logger.debug("Syncing completed successfully.")
            self.sync_success.emit(config_path, descriptor)

    def abort(self):
        """
        Raises a flag indicating we want to abort the syncing process.
        """
        logger.debug("Setting abort flag.")
        self._abort = True
