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
import sys
import time
import datetime

from tank.platform.qt import QtCore, QtGui

import sgtk

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")

ShotgunModel = shotgun_model.ShotgunModel


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
        self.invalidate()

    search_text = property(_get_search_text, _set_search_text)

    #############################################

    def _update_cached_data(self):
        """
        Update our internal state with the results of how the current
        properties are set.
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
            if project is not None:
                project["__item"] = item
                projects.append(project)

        # apply ordering
        if self.search_text:
            def highlighter(char):
                return "<b><u><font color='white'>" + char + "</font></u></b>"
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

    def invalidate(self):
        """
        Override invalidate to update our cached data before calling the base implementation.
        """
        self._update_cached_data()
        QtGui.QSortFilterProxyModel.invalidate(self)

    def lessThan(self, left, right):
        """
        QSortFilterProxyModel override to base ordering on our cached values.
        """
        left_sg_data = left.data(ShotgunModel.SG_DATA_ROLE)
        if left_sg_data is None:
            left_index = sys.maxint
        else:
            left_index = self._ids_in_order.index(left_sg_data["id"])

        right_sg_data = right.data(ShotgunModel.SG_DATA_ROLE)
        if right_sg_data is None:
            right_index = sys.maxint
        else:
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
    DISPLAY_NAME_ROLE = QtCore.Qt.UserRole + 101

    thumbnail_updated = QtCore.Signal(QtGui.QStandardItem)
    project_launched = QtCore.Signal()

    _supports_project_templates = None

    @classmethod
    def supports_project_templates(cls):
        """
        Tests if Shotgun 6.0 Project Templates are supported on the server. If
        this method has never been called, the server will be contacted
        synchronously and the result will be cached so subsequent calls are
        faster.

        :returns: True if the server supports Shotgun 6.0 Project Templates,
                  False otherwise.
        """

        connection = sgtk.platform.current_engine().shotgun

        # If we haven't checked on the server yet.
        if cls._supports_project_templates is None:
            try:
                # Try to read the field's schema.
                connection.schema_field_read("Project", "is_template")
                # It worked therefore it exists.
                cls._supports_project_templates = True
            except Exception:
                # We got an error, so it doesn't exist.
                cls._supports_project_templates = False
        return cls._supports_project_templates

    def __init__(self, parent, overlay_parent_widget):
        """ Constructor """
        ShotgunModel.__init__(self, parent, download_thumbs=True)

        # load up the thumbnail to use when there is none set in Shotgun
        self._missing_thumbnail_project = QtGui.QPixmap(":/tk-desktop/missing_thumbnail_project.png")

        # load up the cached data for the model
        filters = [
            ["name", "is_not", "Template Project"],
            ["archived", "is_not", True]
        ]
        # Template projects is a Shotgun 6.0 feature, so make sure it exists
        # on the server before filtering on that value.
        if SgProjectModel.supports_project_templates():
            filters.append(["is_template", "is_not", True])

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

    def update_project_accessed_time(self, project):
        """
        Set the current user's last-accessed time for the given project.

        This will update the value in the model and in Shotgun.
        """
        if project is None:
            return

        # Update Project.last_accessed_by_current_user in Shotgun
        engine = sgtk.platform.current_engine()
        engine.shotgun.update_project_last_accessed(project, engine.get_current_login())

        # Update the data in the model
        item = self.item_from_entity("Project", project["id"])
        # set to unix seconds rather than datetime to be compatible with Shotgun model
        utc_now_epoch = time.mktime(datetime.datetime.utcnow().utctimetuple())
        project["last_accessed_by_current_user"] = utc_now_epoch
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
