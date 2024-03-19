# Copyright (c) 2024 Autodesk.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


# This is a backpost of Python 3.10's platform module

import re

### freedesktop.org os-release standard
# https://www.freedesktop.org/software/systemd/man/os-release.html

# NAME=value with optional quotes (' or "). The regular expression is less
# strict than shell lexer, but that's ok.
_os_release_line = re.compile(
    "^(?P<name>[a-zA-Z0-9_]+)=(?P<quote>[\"']?)(?P<value>.*)(?P=quote)$"
)
# unescape five special characters mentioned in the standard
_os_release_unescape = re.compile(r"\\([\\\$\"\'`])")
# /etc takes precedence over /usr/lib
_os_release_candidates = ("/etc/os-release", "/usr/lib/os-release")
_os_release_cache = None


def _parse_os_release(lines):
    # These fields are mandatory fields with well-known defaults
    # in practice all Linux distributions override NAME, ID, and PRETTY_NAME.
    info = {
        "NAME": "Linux",
        "ID": "linux",
        "PRETTY_NAME": "Linux",
    }

    for line in lines:
        mo = _os_release_line.match(line)
        if mo is not None:
            info[mo.group("name")] = _os_release_unescape.sub(r"\1", mo.group("value"))

    return info


def freedesktop_os_release():
    """Return operation system identification from freedesktop.org os-release"""
    global _os_release_cache

    if _os_release_cache is None:
        errno = None
        for candidate in _os_release_candidates:
            try:
                with open(candidate, encoding="utf-8") as f:
                    _os_release_cache = _parse_os_release(f)
                break
            except OSError as e:
                errno = e.errno
        else:
            raise OSError(
                errno, f"Unable to read files {', '.join(_os_release_candidates)}"
            )

    return _os_release_cache.copy()
