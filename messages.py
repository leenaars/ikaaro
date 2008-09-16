# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from itools
from itools.gettext import MSG
from itools.web import INFO, ERROR



MSG_BAD_KEY = ERROR(
    u"Your confirmation key is invalid.")

MSG_BAD_NAME = ERROR(
    u'The document name contains illegal characters, choose another one.')

MSG_CAPTION = ERROR(
    u'Caption')

MSG_CHANGES_SAVED = INFO(
    u'The changes have been saved.')

MSG_CHANGES_SAVED2 = INFO(
    u'The changes have been saved ($time).')

MSG_DELETE_RESOURCE = MSG(
    u'Are you sure you want to delete this resource?')

MSG_DELETE_SELECTION = MSG(
    u'Are you sure you want to delete the selection?')

MSG_EDIT_CONFLICT = ERROR(
    u'Someone already saved this document, click "Save" again to force.')

MSG_EMPTY_FILENAME = ERROR(
    u'The file must be entered.')

MSG_EXISTANT_FILENAME = ERROR(
    u'A given name already exists.')

MSG_INVALID_EMAIL = ERROR(
    u'The email address provided is invalid.')

MSG_NAME_CLASH = ERROR(
    u'There is already another resource with this name.')

MSG_NAME_MISSING = ERROR(
    u'The name is missing.')

MSG_NEW_RESOURCE = INFO(
    u'A new resource has been added.')

MSG_NONE_REMOVED = ERROR(
    u'No resource removed.')

MSG_RESOURCES_REMOVED = INFO(
    u'Resources removed: $resources.')

MSG_PAGE_LOCK = ERROR(
    message = u'This page is locked by $user')

MSG_PASSWORD_MISMATCH = ERROR(
    u'The provided passwords do not match.')

MSG_REGISTERED = ERROR(
    u"You have already confirmed your registration. "
    u"Try to log in or ask for a new password.")
