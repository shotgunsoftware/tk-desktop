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
import functools

from PySide import QtGui
from PySide import QtCore

import tank

from .login import ShotgunLogin

shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunModel = shotgun_model.ShotgunModel


class FuzzyMatcher():
    """
    Implement an algorithm to rank strings via fuzzy matching.

    Based on the analysis at
    http://crossplatform.net/sublime-text-ctrl-p-fuzzy-matching-in-python
    """
    def __init__(self, pattern):
        # construct a pattern that matches the letters in order
        # for example "aad" turns into "a.*?a.*?d".
        self.pattern = '.*?'.join(re.escape(char) for char in pattern)
        self.re = re.compile(self.pattern)

    def score(self, string):
        match = self.re.search(string)
        if match is None:
            # letters did not appear in order
            return 0
        else:
            # have a match, scores are higher for matches near the beginning
            # or that are clustered together
            return 100.0 / ((1 + match.start()) * (match.end() - match.start() + 1))


class SgProjectModelProxy(QtGui.QSortFilterProxyModel):
    """Enable sorting and filtering on projects"""
    ASCENDING = 'asc'
    DESCENDING = 'desc'

    def __init__(self, parent=None):
        """Constructor"""
        QtGui.QSortFilterProxyModel.__init__(self, parent)

        self._limit = None  # limit how many items to show
        self._search_text = ''  # search text for ranking projects
        self._show_nonfavorites = True  # boolean on whether to only show favorites
        self._sort_fields = [('name', self.ASCENDING)]  # array of fields to sort by

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

    search_text = property(_get_search_text, _set_search_text)

    # show_favorites property
    def _get_show_nonfavorites(self):
        return self._show_nonfavorites

    def _set_show_nonfavorites(self, value):
        if self._show_nonfavorites == value:
            return
        self._show_nonfavorites = value
        self._update_cached_data()

    show_nonfavorites = property(_get_show_nonfavorites, _set_show_nonfavorites)

    # sort property
    def _get_sort_fields(self):
        return self._sort_fields

    def _set_sort_fields(self, value):
        if self._sort_fields == value:
            return
        self._sort_fields = value
        self._update_cached_data()

    sort_fields = property(_get_sort_fields, _set_sort_fields)

    #############################################

    def _update_cached_data(self, invalidate=True):
        """
        Update our internal state with the results of how the current
        properties are set.

        Will call invalidate unless the invalidate parameter is set
        to False.
        """
        if self.sourceModel() is None:
            # project list is stored on the model, so return unless
            # the model is set.
            return

        def fields_cmp(left, right):
            # a comparator that compares the left and right projects
            # based on the fields set in sort_fields

            # default answer is that left and right are equal
            ret = 0

            for (key, order) in self.sort_fields:
                lhs_value = left[key]
                rhs_value = right[key]
                if lhs_value is None and rhs_value is None:
                    # this field's values are equal
                    continue

                # None sorts after values
                if lhs_value is None:
                    ret = -1
                    break
                if rhs_value is None:
                    ret = 1
                    break

                # See if this sort field has a winner or loser
                if lhs_value < rhs_value:
                    ret = -1
                    break
                if lhs_value > rhs_value:
                    ret = 1
                    break

            # if the last comparison should have been descending, flip result
            if order == self.DESCENDING:
                ret = -ret

            return ret

        # grab the full list of projects from the model
        projects = self.sourceModel()._project_map.values()

        # filter out non favorites
        if self.show_nonfavorites is False:
            projects = [p for p in projects if p['current_user_favorite']]

        # apply ordering
        if self.search_text:
            # order is done by search text
            ratios = []
            matcher = FuzzyMatcher(self.search_text.lower())
            for project in projects:
                ratio = matcher.score(project['name'].lower())
                if ratio:
                    ratios.append((ratio, project))
            ratios_in_order = sorted(ratios, key=lambda key: -key[0])
            projects_in_order = [r[1] for r in ratios_in_order]
        else:
            # otherwise order by sort_fields
            projects_in_order = sorted(projects, key=functools.cmp_to_key(fields_cmp))

        # apply limit post sort
        if self.limit is not None:
            projects_in_order = projects_in_order[:self.limit]

        # grab the ids for easy access during lessThan and filterAcceptsRow
        self._ids_in_order = [p['id'] for p in projects_in_order]

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
        right_sg_data = right.data(ShotgunModel.SG_DATA_ROLE)
        left_index = self._ids_in_order.index(left_sg_data['id'])
        right_index = self._ids_in_order.index(right_sg_data['id'])
        return (left_index < right_index)

    def filterAcceptsRow(self, source_row, source_parent):
        """
        QSortFilterProxyModel override to base filtering on our cached values.
        """
        model = self.sourceModel()
        current_item = model.invisibleRootItem().child(source_row)  # assume non-tree structure
        current_sg_data = current_item.data(ShotgunModel.SG_DATA_ROLE)

        if current_sg_data and 'id' in current_sg_data:
            return current_sg_data['id'] in self._ids_in_order
        return False


class SgProjectModel(ShotgunModel):
    """
    This model represents the data which is displayed in the projects list view
    """
    DISPLAY_NAME_ROLE = QtCore.Qt.UserRole + 101
    LAST_ACCESSED_ROLE = QtCore.Qt.UserRole + 102

    thumbnail_updated = QtCore.Signal(QtGui.QStandardItem)

    def __init__(self, parent, overlay_parent_widget):
        """ Constructor """
        # Temporary workaround until toolkit connects to shotgun
        # using a user login.
        #
        # Get a local cache of project data using a connection linked
        # to the current login.  This will provide fields like last
        # accessed and current user favorite.
        connection = ShotgunLogin.get_connection()

        fields = [
            "code",
            "sg_status",
            "current_user_favorite",
            "last_accessed_by_current_user",
            "name",
        ]
        projects = connection.find('Project', [], fields=fields)
        self._project_map = dict([(p['id'], p) for p in projects])

        # End of workaround

        ShotgunModel.__init__(self, parent, download_thumbs=True)

        # load up the thumbnail to use when there is none set in Shotgun
        self._missing_thumbnail_project = QtGui.QPixmap(":/res/missing_thumbnail_project.png")

        # specify sort key
        self.setSortRole(self.DISPLAY_NAME_ROLE)

        # load up the cached data for the model
        interesting_fields = [
            'sg_status',
            'current_user_favorite',
            'last_accessed_by_current_user',
            'sg_description',
        ]
        ShotgunModel._load_data(
            self,
            entity_type='Project',
            filters=[],
            hierarchy=["name"],
            fields=interesting_fields,
            order=[],
        )

        # and force a refresh of the data from Shotgun
        self._refresh_data()

    def get_project_accessed_time(self, project):
        """Return the last accessed time for the given project."""
        return self._project_map[project['id']]['last_accessed_by_current_user']

    def update_project_accessed_time(self, project):
        """Set the last accessed time for the given project."""
        login = ShotgunLogin.get_login()
        connection = ShotgunLogin.get_connection()

        page = connection.find_one(
            'Page',
            [
                ['entity_type', 'is', 'Project'],
                ['ui_category', 'is', 'project_overview'],
                ['project', 'is', project],
            ],
        )

        # This is forbidden currently from the API and will raise an Exception
        connection.create('PageHit', {'user': login, 'page': page})

        updated = connection.find(
            'Project',
            [['id', 'is', project['id']]],
            fields=['last_accessed_by_current_user'],
        )
        time = updated['last_accessed_by_current_user']
        self._project_map[project['id']]['last_accessed_by_current_user'] = time

    def _populate_item(self, item, sg_data):
        """
        Implement the abstract class method from ShotgunModel.

        Set the item data based on the Shotgun project.
        """
        name = sg_data.get("name", "No Name")
        item.setData(name, self.DISPLAY_NAME_ROLE)

    def _populate_default_thumbnail(self, item):
        """
        Implement the abstract class method from ShotgunModel.

        Set the default thumbnail to the missing thumbnail.
        """
        item.setIcon(self._missing_thumbnail_project)

    def _populate_thumbnail(self, item, field, path):
        """
        Implmenet the abstract class method from ShotgunModel.

        Set the thumbnail directly from the path.
        """
        # first load as a pixmap to avoid the icon delayed loading
        thumb = QtGui.QPixmap(path)
        item.setIcon(thumb)

        # signal anybody listening for thumbnail updates
        self.thumbnail_updated.emit(item)
