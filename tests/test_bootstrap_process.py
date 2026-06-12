# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import subprocess
import sys
import unittest.mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

with unittest.mock.patch.dict(
    "sys.modules",
    {
        "sgtk": unittest.mock.MagicMock(
            LogManager=unittest.mock.MagicMock(
                get_logger=unittest.mock.MagicMock(return_value=unittest.mock.Mock())
            )
        )
    },
):
    from tk_desktop.bootstrap_process import terminate_process


class TestTerminateProcess:
    def test_does_nothing_when_process_is_none(self):
        terminate_process(None)

    def test_does_nothing_when_process_already_exited(self):
        process = unittest.mock.Mock()
        process.poll.return_value = 0

        terminate_process(process)

        process.terminate.assert_not_called()
        process.kill.assert_not_called()

    def test_terminates_running_process(self):
        process = unittest.mock.Mock()
        process.poll.return_value = None
        process.pid = 1234
        process.wait.return_value = 0

        terminate_process(process)

        process.terminate.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=5)
        process.kill.assert_not_called()

    def test_kills_process_when_terminate_times_out(self):
        process = unittest.mock.Mock()
        process.poll.return_value = None
        process.pid = 1234
        process.wait.side_effect = [subprocess.TimeoutExpired("cmd", 5), 0]

        terminate_process(process)

        process.terminate.assert_called_once_with()
        process.kill.assert_called_once_with()
        assert process.wait.call_count == 2
