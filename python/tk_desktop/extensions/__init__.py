# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sys

if sys.version_info[0] == 2:
    if sys.platform == "darwin":
        from .darwin_python2 import *
    elif sys.platform == "win32":
        from .win32_python2 import *
    elif sys.platform.startswith("linux"):
        from .linux_python2 import *
else:
    if sys.platform == "darwin":
        from .darwin_python3 import *
    elif sys.platform == "win32":
        from .win32_python3 import *
    elif sys.platform.startswith("linux"):
        from .linux_python3 import *
