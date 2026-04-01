# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import logging
import os

from sgtk.platform.qt import QtGui

from .ui import licenses

LICENSE_LOCATION = os.path.join(os.path.dirname(__file__), "licenses.html")

_logger = logging.getLogger(__name__)

# LBP-approved Qt LGPL attribution template.
# Version placeholders are filled at runtime by get_pyside_license_html().
_PYSIDE_LGPL_TEMPLATE = """\
<!--       Qt / PySide -->
<div>
    <p><strong>Qt v. {qt_version} / PySide {pyside_version}</strong></p>
    <pre>
The Qt Toolkit is Copyright (C) 2022 The Qt Company Ltd. and other
contributors. This Autodesk software contains Qt v. {qt_version}, as modified
by Autodesk. Qt is licensed under the GNU Lesser General Public License v.3,
which can be found at https://www.gnu.org/licenses/lgpl-3.0.html. You may
obtain a copy of the license and source code for Qt v. {qt_version}, as
modified by Autodesk, from
https://github.com/autodesk-forks/qt5/tree/adsk-v{qt_version} or by sending
a written request to:

    Autodesk, Inc.
    Attention: General Counsel
    Legal Department
    The Landmark at One Market Street, Suite 400
    San Francisco, CA 94105
    </pre>
</div>
"""


class Licenses(QtGui.QDialog):
    """Simple about dialog"""

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        # setup the GUI
        self.ui = licenses.Ui_Licenses()
        self.ui.setupUi(self)
        # setSource seems broken on Qt4, so use setHtml instead.
        self.ui.licenseText.setHtml(self.get_license_html())

    @classmethod
    def get_pyside_license_html(cls):
        """Return the Qt/PySide LGPL attribution HTML with runtime version detection.

        Detects the installed PySide version so the wording is always accurate
        regardless of which SGD and tk-desktop versions are running together.

        This method is intentionally designed to be overridable. External code
        (e.g. tk-framework-desktopstartup) may replace it on old tk-desktop
        builds to inject the correct version when needed.

        :returns: HTML string with the Qt/PySide LGPL attribution.
        :rtype: str
        """
        try:
            import PySide6
            import PySide6.QtCore

            pyside_version = PySide6.__version__
            qt_version = PySide6.QtCore.__version__
        except ImportError:
            try:
                import PySide2
                import PySide2.QtCore

                pyside_version = PySide2.__version__
                qt_version = PySide2.QtCore.__version__
            except ImportError:
                _logger.debug(
                    "Could not detect PySide version for license attribution."
                )
                pyside_version = "unknown"
                qt_version = "unknown"

        return _PYSIDE_LGPL_TEMPLATE.format(
            pyside_version=pyside_version,
            qt_version=qt_version,
        )

    @classmethod
    def get_license_html(cls):
        """Return the full license HTML, combining the static file with the
        dynamic Qt/PySide attribution.

        :returns: Full HTML string for the Licenses dialog.
        :rtype: str
        """
        with open(LICENSE_LOCATION, encoding="utf-8") as f:
            base_html = f.read()
        return base_html + cls.get_pyside_license_html()
