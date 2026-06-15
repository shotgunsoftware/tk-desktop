# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Helpers for managing the project bootstrap subprocess launched by tk-desktop.
"""

import subprocess  # nosec B404
import typing

import sgtk

logger = sgtk.LogManager.get_logger(__name__)

DEFAULT_TERMINATION_TIMEOUT: int = 5


def terminate_process(
    process: typing.Optional[subprocess.Popen],
    timeout: int = DEFAULT_TERMINATION_TIMEOUT,
) -> None:
    """
    Terminates a subprocess if it is still running.

    :param process: A :class:`subprocess.Popen` instance, or None.
    :param timeout: Number of seconds to wait for graceful termination before killing.
    """
    if process is None:
        return

    if process.poll() is not None:
        return

    logger.debug("Terminating bootstrap process (pid %s)...", process.pid)
    try:
        process.terminate()
    except OSError as exc:
        logger.warning("Error terminating bootstrap process: %s", exc)

    try:
        process.wait(timeout=timeout)
        return
    except subprocess.TimeoutExpired:
        logger.warning(
            "Bootstrap process (pid %s) did not exit after terminate(), killing...",
            process.pid,
        )

    try:
        process.kill()
    except OSError as exc:
        logger.warning("Error killing bootstrap process: %s", exc)

    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.warning(
            "Bootstrap process (pid %s) did not exit after kill().", process.pid
        )
