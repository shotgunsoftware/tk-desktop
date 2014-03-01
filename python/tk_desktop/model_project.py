# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import functools

from PySide import QtGui
from PySide import QtCore

import tank

import shotgun_desktop.login

shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunModel = shotgun_model.ShotgunModel


class SgProjectModelProxy(QtGui.QSortFilterProxyModel):
    """
    Enable sorting and filtering on projects
    """

    ASCENDING = 'asc'
    DESCENDING = 'desc'

    def __init__(self, parent=None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)

        self._limit = None
        self._show_nonfavorites = True
        self._sort_fields = [('name', self.ASCENDING)]

        # Temporary workaround until toolkit connects to shotgun
        # using a user login.
        #
        # Get a local cache of project data using a connection linked
        # to the current login.  This will provide fields like last
        # accessed and current user favorite.
        connection = shotgun_desktop.login.ShotgunLogin.get_connection()

        fields = [
            "code",
            "sg_status",
            "current_user_favorite",
            "last_accessed_by_current_user",
            "name",
        ]
        projects = connection.find('Project', [], fields=fields)
        self._project_map = dict([(p['id'], p) for p in projects])
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

    def _update_cached_data(self):
        def fields_cmp(left, right):
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

        projects = self._project_map.values()

        # filter out non favorites
        if self.show_nonfavorites is False:
            projects = [p for p in projects if p['current_user_favorite']]

        projects_in_order = sorted(projects, key=functools.cmp_to_key(fields_cmp))

        # apply limit post sort
        if self.limit is not None:
            projects_in_order = projects_in_order[:self.limit]

        print "--------- ORDER ----------"
        print "\n".join([p['name'] for p in projects_in_order])
        print "--------------------------"
        self._ids_in_order = [p['id'] for p in projects_in_order]
        self.invalidateFilter()

    def lessThan(self, left, right):
        left_sg_data = left.data(ShotgunModel.SG_DATA_ROLE)
        right_sg_data = right.data(ShotgunModel.SG_DATA_ROLE)
        left_index = self._ids_in_order.index(left_sg_data['id'])
        right_index = self._ids_in_order.index(right_sg_data['id'])
        return (left_index < right_index)

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        current_item = model.invisibleRootItem().child(source_row)  # assume non-tree structure
        current_sg_data = current_item.data(ShotgunModel.SG_DATA_ROLE)

        return current_sg_data['id'] in self._ids_in_order


class SgProjectModel(ShotgunModel):
    """
    This model represents the data which is displayed in the projects list view
    """
    DISPLAY_NAME_ROLE = QtCore.Qt.UserRole + 101
    LAST_ACCESSED_ROLE = QtCore.Qt.UserRole + 102

    def __init__(self, parent, overlay_parent_widget):
        """ Constructor """
        ShotgunModel.__init__(self, parent, overlay_parent_widget, download_thumbs=True)

        self._missing_thumbnail_project = QtGui.QPixmap(":/res/missing_thumbnail_project.png")

        # specify sort key
        self.setSortRole(self.DISPLAY_NAME_ROLE)

        # get data from Shotgun
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

        self._refresh_data()

    ############################################################################################
    # subclassed methods

    def _ShotgunModel__on_worker_failure(self, uid, msg):
        super(SgProjectModel, self)._ShotgunModel__on_worker_failure(uid, msg)

    def _populate_item(self, item, sg_data):
        name = sg_data.get("name", "No Name")
        last_accessed = sg_data.get('last_accessed_by_current_user', None)
        item.setData(name, self.DISPLAY_NAME_ROLE)
        item.setData(last_accessed, self.LAST_ACCESSED_ROLE)

    def _populate_default_thumbnail(self, item):
        item.setIcon(self._missing_thumbnail_project)

    def _populate_thumbnail(self, item, field, path):
        thumb = QtGui.QPixmap(path)
        item.setIcon(thumb)
