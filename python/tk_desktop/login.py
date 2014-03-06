# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from PySide import QtGui
from PySide import QtCore

from sgtk.util.shotgun import Shotgun

from .ui import resources_rc
from .ui import login as login_ui


class ShotgunLoginError(Exception):
    """ Generic login specific exceptions """
    pass


class ShotgunLogin(QtGui.QDialog):
    """ Manage authenticating a Shotgun login """

    # Constants that control where the settings are saved
    SETTINGS_APPLICATION = "Shotgun Desktop"
    SETTINGS_ORGANIZATION = "Shotgun Software"
    KEYRING_ROOT = "com.shotgunsoftware.desktop"

    ##########################################################################################
    # public methods

    @classmethod
    def get_login(cls):
        """
        Return the login dictionary for the currently authenticated user.

        This will check saved values to see if there is a valid Shotgun
        login cached. If no valid cached login information is found, a login
        dialog is displayed.

        This method returns a HumanUser dict for the login if it succeeds and
        None if it fails.
        """
        # first check in memory cache
        result = getattr(cls, '_%s__login' % cls.__name__, None)
        if result:
            return result

        # next see if the saved values return a valid user
        result = cls.__check_saved_values()
        if result:
            return cls.__login

        # saved values did not authenticate run the dialog
        result = cls.__run_dialog()
        if result:
            return cls.__login

        # failed
        return None

    @classmethod
    def get_connection(cls):
        """
        Return an authenticated Shotgun connection.

        This will check saved values to see if there is a valid Shotgun
        login cached. If no valid cached login information is found, a login
        dialog is displayed.

        This method returns a Shotgun connection if it succeeds and None if
        it fails.
        """
        # first check in memory cache
        result = getattr(cls, '_%s__connection' % cls.__name__, None)
        if result:
            return result

        # next see if the saved values return a valid user
        result = cls.__check_saved_values()
        if result:
            return cls.__connection

        # saved values did not authenticate run the dialog
        result = cls.__run_dialog()
        if result:
            return cls.__connection

        # failed
        return None

    @classmethod
    def logout(cls):
        """
        Log out of the current connection.

        This will clear any stored values and require a new login to retrieve
        any further login on connection information.
        """
        cls.__login = None
        cls.__connection = None
        cls.__clear_saved_values()

    ##########################################################################################
    # private class methods

    @classmethod
    def __run_dialog(cls):
        """ run the login dialog """
        dialog = cls()
        result = dialog.exec_()
        if result == dialog.Accepted:
            return True

        # dialog was canceled
        return False

    @classmethod
    def __check_saved_values(cls):
        """ return whether the saved values authenticate or not """
        (site, script, key, login, password) = cls.__get_saved_values()
        try:
            return cls.__check_values(site, script, key, login, password)
        except ShotgunLoginError:
            return False

    @classmethod
    def __get_saved_values(cls):
        """ return a tuple of all the stored values """
        import keyring

        # load up the values stored via qsettings
        settings = QtCore.QSettings(cls.SETTINGS_ORGANIZATION, cls.SETTINGS_APPLICATION)

        settings.beginGroup("loginInfo")
        site = settings.value("site", None)
        login = settings.value("login", None)
        script = settings.value("script", None)
        settings.endGroup()

        # load up the values stored securely in the os specific keyring
        if script:
            key = keyring.get_password("%s.key" % cls.KEYRING_ROOT, script)
        else:
            key = None

        if login:
            password = keyring.get_password("%s.login" % cls.KEYRING_ROOT, login)
        else:
            password = None

        return (site, script, key, login, password)

    @classmethod
    def __clear_saved_values(cls):
        """ clear any saved values """
        import keyring

        # grab values needed to clear keyring
        settings = QtCore.QSettings(cls.SETTINGS_ORGANIZATION, cls.SETTINGS_APPLICATION)
        settings.beginGroup("loginInfo")
        login = settings.value("login", None)
        script = settings.value("script", None)

        # remove settings stored via QSettings
        settings.remove("")
        settings.endGroup()

        # remove settings stored in the os specific keyring
        keyring.delete_password("%s.key" % cls.KEYRING_ROOT, script)
        keyring.delete_password("%s.login" % cls.KEYRING_ROOT, login)

    @classmethod
    def __save_values(cls, site, script, key, login, password):
        """ save the given values securely """
        import keyring

        # make sure the keyring supports encryption
        kr = keyring.get_keyring()
        if not kr.encrypted():
            raise ShotgunLoginError("keyring does not support encryption")

        # save the settings via qsettings
        settings = QtCore.QSettings(cls.SETTINGS_ORGANIZATION, cls.SETTINGS_APPLICATION)
        settings.beginGroup("loginInfo")
        settings.setValue("site", site)
        settings.setValue("login", login)
        settings.setValue("script", script)
        settings.endGroup()

        # save these settings securely in the os specific keyring
        keyring.set_password("%s.key" % cls.KEYRING_ROOT, script, key)
        keyring.set_password("%s.login" % cls.KEYRING_ROOT, login, password)

    @classmethod
    def __check_values(cls, site, script, key, login, password):
        """
        Authenticate the given values in Shotgun.

        Will always return True or raise a ShotgunLoginError.
        """
        # try to connect to Shotgun
        try:
            # connect and force an exchange so the script/key is validated
            connection = Shotgun(site, script, key)
            connection.find_one('HumanUser', [])
        except Exception, e:
            raise ShotgunLoginError("Could not connect to server", str(e))

        try:
            result = connection.authenticate_human_user(login, password)
            if result is None:
                raise ShotgunLoginError("Could not log in to server", "Login not valid.")
        except Exception, e:
            raise ShotgunLoginError("Could not log in to server", str(e))

        # cache results
        cls.__login = result
        cls.__connection = connection

        return True

    ##########################################################################################
    # instance methods

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        # set the dialog to not have window decorations and always stay on top
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # setup the gui
        self.ui = login_ui.Ui_Login()
        self.ui.setupUi(self)
        self.load_settings()
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.ok_pressed)

    def ok_pressed(self):
        """
        validate the values, accepting if login is successful and display an error message if not.
        """
        # pull values from the gui
        key = self.ui.key.text()
        site = self.ui.site.text()
        login = self.ui.login.text()
        script = self.ui.script.text()
        password = self.ui.password.text()

        try:
            # try and authenticate
            self.__check_values(site, script, key, login, password)
        except ShotgunLoginError, e:
            # authentication did not succeed
            self.ui.message.setText("%s\n\n%s" % (e[0], e[1]))
            return

        # all good, save the settings if requested and return accepted
        if self.ui.remember_me.isChecked():
            try:
                self.ui.message.setText("")
                self.save_settings()
            except ShotgunLoginError:
                # error saving the settings
                self.ui.message.setText(
                    "Could not store login information safely.\n\n" +
                    "Please uncheck \"Remember me\" to continue.")
                return

        # dialog is done
        self.accept()

    def load_settings(self):
        """ Load the saved values for the dialog """
        (site, script, key, login, password) = self.__get_saved_values()

        # populate the ui
        self.ui.site.setText(site or '')
        self.ui.login.setText(login or '')
        self.ui.password.setText(password or '')
        self.ui.script.setText(script or '')
        self.ui.key.setText(key or '')

    def save_settings(self):
        """ Save the values from the dialog """
        # pull values from the gui
        key = self.ui.key.text()
        site = self.ui.site.text()
        login = self.ui.login.text()
        script = self.ui.script.text()
        password = self.ui.password.text()

        self.__save_values(site, script, key, login, password)
