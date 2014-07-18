# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import re
import time
import datetime

from tank.platform.qt import QtCore, QtGui

import sgtk

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
shotgun_login = sgtk.platform.import_framework("tk-framework-login", "shotgun_login")

ShotgunModel = shotgun_model.ShotgunModel
ShotgunLogin = shotgun_login.ShotgunLogin


class FuzzyMatcher():
    """
    Implement an algorithm to rank strings via fuzzy matching.

    Based on the analysis at
    http://crossplatform.net/sublime-text-ctrl-p-fuzzy-matching-in-python
    """
    def __init__(self, pattern, case_sensitive=False):
        # construct a pattern that matches the letters in order
        # for example "aad" turns into "(a).*?(a).*?(d)".
        self.pattern = ".*?".join("(%s)" % re.escape(char) for char in pattern)
        if case_sensitive:
            self.re = re.compile(self.pattern)
        else:
            self.re = re.compile(self.pattern, re.IGNORECASE)

    def score(self, string, highlighter=None):
        match = self.re.search(string)
        if match is None:
            # letters did not appear in order
            return (0, string)
        else:
            # have a match, scores are higher for matches near the beginning
            # or that are clustered together
            score = 100.0 / ((1 + match.start()) * (match.end() - match.start() + 1))

            if highlighter is not None:
                highlighted = string[0:match.start(1)]
                for group in xrange(1, match.lastindex+1):
                    if group == match.lastindex:
                        remainder = string[match.end(group):]
                    else:
                        remainder = string[match.end(group):match.start(group+1)]
                    highlighted += highlighter(match.group(group)) + remainder
            return (score, highlighted)


class SgProjectModelProxy(QtGui.QSortFilterProxyModel):
    """Enable sorting and filtering on projects"""
    def __init__(self, parent=None):
        """Constructor"""
        QtGui.QSortFilterProxyModel.__init__(self, parent)

        self._limit = None  # limit how many items to show
        self._search_text = ""  # search text for ranking projects

    def setSourceModel(self, model):
        """
        Override base setSourceModel to include a call to update our
        internal representation for sorting and filtering.
        """
        old_model = self.sourceModel()
        if old_model is not None:
            old_model.data_refreshed.disconnect(self._update_cached_data)
            old_model.project_launched.disconnect(self._update_cached_data)
        model.data_refreshed.connect(self._update_cached_data)
        model.project_launched.connect(self._update_cached_data)

        QtGui.QSortFilterProxyModel.setSourceModel(self, model)
        self._update_cached_data()

    #############################################
    # properties

    # limit property
    def _get_limit(self):
        return self._limit

    def _set_limit(self, value):
        if self._limit == value:
            return
        self._limit = value
        self._update_cached_data()

    limit = property(_get_limit, _set_limit)

    # search_text property
    def _get_search_text(self):
        return self._search_text

    def _set_search_text(self, value):
        if self._search_text == value:
            return
        self._search_text = value
        self._update_cached_data()

    search_text = property(_get_search_text, _set_search_text)

    #############################################

    def _update_cached_data(self, invalidate=True):
        """
        Update our internal state with the results of how the current
        properties are set.

        Will call invalidate unless the invalidate parameter is set
        to False.
        """
        src_model = self.sourceModel()
        if src_model is None:
            # project list is stored on the model, so return unless the model is set.
            return

        # grab the full list of projects from the model
        projects = []
        for row in xrange(src_model.rowCount()):
            item = src_model.item(row, 0)
            project = item.data(ShotgunModel.SG_DATA_ROLE)
            project["__item"] = item
            projects.append(project)

        # apply ordering
        if self.search_text:
            def highlighter(char):
                return "<b>" + char + "</b>"
            # order is done by search text
            ratios = []
            matcher = FuzzyMatcher(self.search_text.lower())
            for project in projects:
                (ratio, highlighted) = matcher.score(project["name"], highlighter)
                if ratio:
                    ratios.append((ratio, project))
                    project["__item"].setData(highlighted, SgProjectModel.DISPLAY_NAME_ROLE)
                else:
                    project["__item"].setData(project["name"], SgProjectModel.DISPLAY_NAME_ROLE)
            ratios_in_order = sorted(ratios, key=lambda key: -key[0])
            projects_in_order = [r[1] for r in ratios_in_order]
        else:
            # clear any existing highlighting
            for project in projects:
                project["__item"].setData(project["name"], SgProjectModel.DISPLAY_NAME_ROLE)

            # sort by last_accessed_by_current_user
            def key_for_project(project):
                return (
                    project["last_accessed_by_current_user"],
                    project["name"],
                    project["id"],
                )
            projects_in_order = sorted(projects, key=key_for_project, reverse=True)

        # apply limit post sort
        if self.limit is not None:
            projects_in_order = projects_in_order[:self.limit]

        # grab the ids for easy access during lessThan and filterAcceptsRow
        self._ids_in_order = [p["id"] for p in projects_in_order]

        if invalidate:
            # invalidate to trigger views to refresh
            self.invalidate()

    def invalidate(self):
        """
        Override invalidate to update our cached data before calling the base implementation.
        """
        self._update_cached_data(invalidate=False)
        QtGui.QSortFilterProxyModel.invalidate(self)

    def lessThan(self, left, right):
        """
        QSortFilterProxyModel override to base ordering on our cached values.
        """
        left_sg_data = left.data(ShotgunModel.SG_DATA_ROLE)
        left_index = self._ids_in_order.index(left_sg_data["id"])

        right_sg_data = right.data(ShotgunModel.SG_DATA_ROLE)
        right_index = self._ids_in_order.index(right_sg_data["id"])

        return (left_index < right_index)

    def filterAcceptsRow(self, source_row, source_parent):
        """
        QSortFilterProxyModel override to base filtering on our cached values.
        """
        model = self.sourceModel()
        current_index = model.index(source_row, 0, source_parent)
        current_item = model.itemFromIndex(current_index)
        current_sg_data = current_item.data(ShotgunModel.SG_DATA_ROLE)

        if current_sg_data and "id" in current_sg_data:
            return current_sg_data["id"] in self._ids_in_order
        return False


class SgProjectModel(ShotgunModel):
    """
    This model represents the data which is displayed in the projects list view
    """
    PROJECT_LAUNCH_EVENT_TYPE = "Toolkit_Desktop_ProjectLaunch"

    DISPLAY_NAME_ROLE = QtCore.Qt.UserRole + 101

    thumbnail_updated = QtCore.Signal(QtGui.QStandardItem)
    project_launched = QtCore.Signal()

    def __init__(self, parent, overlay_parent_widget):
        """ Constructor """
        ShotgunModel.__init__(self, parent, download_thumbs=True)

        # override the default connection to use one that is tied to the current login
        connection = ShotgunLogin.get_instance_for_namespace("tk-desktop").get_connection()

        self.set_shotgun_connection(connection)

        # load up the thumbnail to use when there is none set in Shotgun
        self._missing_thumbnail_project = QtGui.QPixmap(":/tk-desktop/missing_thumbnail_project.png")

        # load up the cached data for the model
        filters = [
            ["name", "is_not", "Template Project"],
            ["archived", "is_not", True],
        ]
        interesting_fields = [
            "name",
            "sg_status",
            "current_user_favorite",
            "last_accessed_by_current_user",
            "sg_description",
        ]
        ShotgunModel._load_data(
            self,
            entity_type="Project",
            filters=filters,
            hierarchy=["name"],
            fields=interesting_fields,
            order=[],
        )

        # and force a refresh of the data from Shotgun
        self._refresh_data()

    def _before_data_processing(self, sg_data_list):
        # merge in timestamps from project launch events if they are newer than
        # the last access timestamps from Shotgun

        # pull down matching events for the current user
        login = ShotgunLogin.get_instance_for_namespace("tk-desktop").get_login()
        filters = [
            ["user", "is", login],
            ["event_type", "is", self.PROJECT_LAUNCH_EVENT_TYPE],
        ]

        # execute the Shotgun summarize command
        # get one group per project with a summary of the latest created_at
        connection = sgtk.platform.current_engine().shotgun
        summary = connection.summarize(
            entity_type="EventLogEntry",
            filters=filters,
            summary_fields=[{"field": "created_at", "type": "latest"}],
            grouping=[{"field": "project", "type": "exact", "direction": "asc"}],
        )

        # parse the results
        # convert all last accessed timestamps to naive datetime objects in UTC time
        # this makes sure that the event times and Shotgun times can be directly
        # compared
        launches_by_project_id = {}
        for group in summary["groups"]:
            # convert the text representation of created_at to a UTC based timetuple
            text_stamp = group["summaries"]["created_at"]
            time_stamp = datetime.datetime.strptime(text_stamp, "%Y-%m-%d %H:%M:%S %Z")
            launches_by_project_id[group["group_value"]["id"]] = time_stamp.utctimetuple()

        for project in sg_data_list:
            if project["last_accessed_by_current_user"] is None:
                # never accessed in shotgun
                if project["id"] in launches_by_project_id:
                    # but is has been launched from the desktop
                    launch_date = launches_by_project_id[project["id"]]
                    # set last accessed on the project in UTC
                    project["last_accessed_by_current_user"] = \
                        datetime.datetime.fromtimestamp(time.mktime(launch_date))
                continue

            # grab the shotgun time as a UTC based timetuple
            shotgun_date = project["last_accessed_by_current_user"].utctimetuple()

            # set the non-overridden one to avoid timezone issues being
            # introduced by the shotgun model time conversion
            project["last_accessed_by_current_user"] = \
                datetime.datetime.fromtimestamp(time.mktime(shotgun_date))

            # if there are desktop launches for this project
            if project["id"] in launches_by_project_id:
                launch_date = launches_by_project_id[project["id"]]
                if launch_date > shotgun_date:
                    # desktop launch is newer, swap in the event time
                    project["last_accessed_by_current_user"] = \
                        datetime.datetime.fromtimestamp(time.mktime(launch_date))

        return sg_data_list

    def update_project_accessed_time(self, project):
        """
        Set the last accessed time for the given project.

        This will update the value in the model and create a tracking event
        in Shotgun.
        """
        # use toolkit connection to get ApiUser permissions for event creation
        engine = sgtk.platform.current_engine()
        connection = engine.shotgun
        login = ShotgunLogin.get_instance_for_namespace("tk-desktop").get_login()
        data = {
            "description": "Project launch from tk-desktop",
            "event_type": self.PROJECT_LAUNCH_EVENT_TYPE,
            "project": project,
            "meta": {"version": engine.version},
            "user": login,
        }
        engine.log_debug("Registering project launch event: %s" % data)
        connection.create("EventLogEntry", data)

        # update the data in the model
        item = self.item_from_entity("Project", project["id"])
        project = item.data(ShotgunModel.SG_DATA_ROLE)

        # set to unix seconds rather than datetime to be compatible with shotgun model
        utc_now = time.mktime(datetime.datetime.utcnow().utctimetuple())
        project["last_accessed_by_current_user"] = utc_now
        item.setData(project, ShotgunModel.SG_DATA_ROLE)

        self.project_launched.emit()

    def _populate_item(self, item, sg_data):
        """
        Implement the abstract class method from ShotgunModel.

        Set the item data based on the Shotgun project.
        """
        item.setData(sg_data.get("name", "No Name"), self.DISPLAY_NAME_ROLE)

    def _populate_default_thumbnail(self, item):
        """
        Implement the abstract class method from ShotgunModel.

        Set the default thumbnail to the missing thumbnail.
        """
        item.setIcon(self._missing_thumbnail_project)

    def _populate_thumbnail(self, item, field, path):
        """
        Implement the abstract class method from ShotgunModel.

        Set the thumbnail directly from the path.
        """
        # first load as a pixmap to avoid the icon delayed loading
        thumb = QtGui.QPixmap(path)
        item.setIcon(thumb)

        # signal anybody listening for thumbnail updates
        self.thumbnail_updated.emit(item)
