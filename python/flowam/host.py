# -
# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# These coded instructions, statements, and computer programs contain
# unpublished proprietary information written by Autodesk, Inc. and are
# protected by Federal copyright law. They may not be disclosed to third
# parties or copied or duplicated in any form, in whole or in part, without
# the prior written consent of Autodesk, Inc.
# *****************************************************************************
#

from __future__ import annotations  # needed for python 3.9 support

import os

import sgtk
from tank import LogManager
from tank.flowam.host import FlowHost
from tank.flowam.utils import open_explorer
from tank_vendor.flow_integration_sdk.utils import trace


class DesktopHost(FlowHost):
    """Toolkit Desktop implementation of FlowHost interface.
    This is a collection of required capabilities to support Flow AM integration.
    """

    logger = LogManager.get_logger("DesktopHost")

    #: Desktop application deals with generic workfiles
    WORKFILE_TYPE = "type.workfile.generic"
    #: Supports all file types
    FILE_TYPES = ["*"]

    def __init__(self, context):

        self.logger.info("Doing DesktopHost initialization...")

        super().__init__(context)

    @trace
    def current_file(self) -> str:
        # Not applicable for desktop application
        return ""

    @trace
    def new_scene(self, force: bool = True) -> bool:
        # Not applicable for desktop application
        return True

    @trace
    def open_file(self, file_path: str) -> bool:
        """Open given file path. In Desktop context, this means opening
        the containing folder of file in file explorer.

        Args:
            file_path: Full path to file to be opened.

        Returns:
            True if file is opened, False on error or if operation is cancelled.
        """
        # path to file directory
        dir_path = os.path.dirname(file_path)

        # Open the file explorer
        return open_explorer(dir_path)

    @trace
    def dialog(
        self,
        title: str,
        msg: str,
        buttons: list[str] | None = None,
        default: int = 0,
        cancel: int | None = None,
        no_ui_option: int | None = None,
    ) -> int:
        """Pop up a dialog in the dcc.

        Args:
            title: Title of dialog window.
            msg: Message to be displayed.
            buttons: List of strings denoting buttons to be added to dialog.
                     NOTE: Maximum of 9 buttons can be supported for this host.
            default: Index of default button.
            cancel: Index of cancel button. If not specified, native behaviour is to
                    use 1 if there is more than one option, or 0 otherwise.
            no_ui_option: Irrelevant for Desktop host.

        Returns:
            The index of the button selected by user. Value of -1 indicates dismissed dialog.
        """
        from tank.platform.qt import QtGui as qtg

        if not buttons:
            # Minimally provide a generic confirmation button
            buttons = ["Ok"]
        elif len(buttons) > 9:
            raise ValueError("Maximum of 9 buttons supported in DesktopHost dialog.")

        if default >= len(buttons):
            raise ValueError(f"Provided default action {default} is out of range.")
        if cancel is not None and cancel >= len(buttons):
            raise ValueError(f"Provided cancel action {cancel} is out of range.")

        # Create qt message box
        parent = self._get_dialog_parent()
        dialog = qtg.QMessageBox(parent)
        dialog.setWindowTitle(title)
        dialog.setText(msg)

        # Create qt push buttons
        push_buttons = [qtg.QPushButton(btn_text) for btn_text in buttons]

        # NOTE: The order of addition here does not control the order
        #       of display unfortunately - rather that is determined by
        #       platform based on button roles.
        #       To have complete control over this and remove the 9 button limit
        #       we must make a custom dialog.
        for i, btn in enumerate(push_buttons):
            # NOTE: Using a hack here to assign each button a unique int
            #       value using available button roles (there are 9)
            dialog.addButton(btn, qtg.QMessageBox.ButtonRole(i))

        # Set default action
        default_button = push_buttons[default]
        dialog.setDefaultButton(default_button)

        # Set cancel action
        if cancel is not None:
            cancel_button = push_buttons[cancel]
            dialog.setEscapeButton(cancel_button)

        # Show dialog
        dialog.exec()

        # Determine which button is clicked and return corresponding action index
        # NOTE: from QMessageBox documentation:
        #       When you add custom buttons with addButton(), the return value of
        #       exec_() can vary across platforms, but clickedButton() will consistently
        #       return the actual button object that was clicked.
        return push_buttons.index(dialog.clickedButton())

    @trace
    def file_dialog(
        self,
        title: str,
        starting_dir: str = "",
        folder_mode: bool = False,
        file_type: str = "",
        multi_select: bool = False,
    ) -> list[str]:
        """Invoke a file dialog for selecting one or more file paths.

        Args:
            title: Title of dialog.
            starting_dir: Starting location of dialog.
            folder_mode: If True, dialog will browse folders instead of files.
            file_filter: Extension of file type to filter for.
                         Applicable only when browsing files.
            multi_select: If True, allow multiple selection of files.
                          Applicable only when browsing files.

        Returns:
            A list of file/directory paths.
            If multi_select = False, the return value will be a list of size 1.
            If user cancels, list will be empty.
        """
        from tank.platform.qt import QtGui as qtg

        parent = self._get_dialog_parent()

        if folder_mode:
            # Select single directory
            result = qtg.QFileDialog.getExistingDirectory(
                parent=parent,
                caption=title,
                dir=starting_dir,
            )
            if result:
                return [str(result)]
            return []

        file_filter = f"*.{file_type}" if file_type else ""

        if multi_select:
            # Select multiple files
            result, _ = qtg.QFileDialog.getOpenFileNames(
                parent=parent,
                caption=title,
                dir=starting_dir,
                filter=file_filter,
            )
            return [str(path) for path in result]

        # Select single file
        result, _ = qtg.QFileDialog.getOpenFileName(
            parent=parent,
            caption=title,
            dir=starting_dir,
            filter=file_filter,
        )
        if result:
            return [str(result)]
        return []

    def _get_dialog_parent(self):
        """
        Return the parent widget for dialogs in DesktopHost.
        Currently returns None as there is no specific parent.
        If in the future a main application window is defined, this method can be updated to return that window.

        Returns:
            The parent widget or None.
        """
        engine = sgtk.platform.current_engine()
        if engine is not None:
            return engine._get_dialog_parent()

        return None

    @trace
    def copy_to_clipboard(self, text: str) -> bool:
        """Copy given text to clipboard of QT application.

        Args:
            text: Text to be copied.

        Returns:
            True on success.
        """
        from tank.platform.qt import QtGui as qtg

        app = qtg.QApplication.instance()
        if app is None:
            # NOTE: Desktop always has a running QApplication so the None
            #       guard is just a safety net, not a real code path.
            msg = "Copy to clipboard failed. "
            msg += "No QApplication instance available for clipboard access."
            self.logger.error(msg)
            return False

        app.clipboard().setText(text)
        return True
