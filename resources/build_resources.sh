#!/usr/bin/env bash
#
# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

# The path to where the PySide binaries are installed
PYTHON_BASE="/Applications/Shotgun.app/Contents/Resources/Python"
PYTHON_LIB="${PYTHON_BASE}/lib/python2.7"

# The path to output all built .py files to:
UI_PYTHON_PATH=../python/tk_desktop/ui

function build_qt {
    echo " > Building " $2

    # compile ui to python
    $1 $2 > $UI_PYTHON_PATH/$3.py

    # replace PySide imports with sgtk.platform.qt and remove line containing Created by date
    sed -i "" -e "s/from PySide import/from sgtk.platform.qt import/g" -e "/# Created:/d" $UI_PYTHON_PATH/$3.py
}

function build_ui {
    build_qt "${PYTHON_BASE}/bin/python ${PYTHON_BASE}/bin/pyside-uic --from-imports" "$1.ui" "$1"
}

function build_res {
    build_qt "${PYTHON_BASE}/bin/pyside-rcc" "$1.qrc" "$1_rc"
}

# build UI's:
echo "building user interfaces..."
build_ui desktop_window
build_ui wait_screen
build_ui about_screen
build_ui error_dialog
build_ui setup_new_os
build_ui thumb_widget
build_ui setup_project
build_ui no_apps_installed_overlay
build_ui update_project_config
build_ui loading_project_widget
build_ui browser_integration_user_switch_dialog
build_ui banner_widget

# build resources
echo "building resources..."
build_res resources

