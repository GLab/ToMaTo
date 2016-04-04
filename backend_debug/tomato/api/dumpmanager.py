# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from ..dumpmanager.errorgroup import get_group, ErrorGroup
from ..dumpmanager import update_all
from ..lib.error import UserError

def errordump_info(group_id, source, dump_id, include_data=False):
		"""
		Returns details for the given dump.
		A dump is identified by its group_id, its source, and the dump_id on this source.

		Parameter *group_id*:
			A string. This is the group id of the dump group.

		Parameter *source*:
			A string. This is the source (i.e., a certain host, or the backend) of the dump.

		Parameter *dump_id*:
			The unique identifier of the dump to be queried.

		Parameter *include_data*:
			A boolean.
			Every dump has environment data attatched to it. This data may be big (i.e., >1MB).
			By default, the data of a dump has most likely not been loaded from its source.
			If include_data is False, this data will not be returned by this call.
			If it is True, this data will first be fetched from the source, if needed, and included in this call's return.

		Return value:
			The return value of this method is the info dict of the dump.
			If include_data is True, it will contain a data field, otherwise a data_available indicator.
		"""
		grp = get_group(group_id)
		UserError.check(grp, UserError.ENTITY_DOES_NOT_EXIST, message="no such error group", data={"group_id": group_id})
		return grp.get_dump(dump_id, source).info(include_data)

def errordump_list(group_id, source=None):
		"""
		Returns a list of dumps.

		Parameter *group_id*:
			A string. Only dumps of this group will be included.

		Parameter *source*:
			A string. If this is not None, only dumps from this source will be included.

		Return value:
			A list of dumps, filtered by the arguments.
		"""
		grp = get_group(group_id)
		UserError.check(grp, UserError.ENTITY_DOES_NOT_EXIST, message="no such error group", data={"group_id": group_id})
		return [d.info(False) for d in grp.get_dumps(source)]

def errorgroup_info(group_id, include_dumps=False, as_user=None):
		"""
		Returns details for the given dump group.

		Parameter *group_id*:
			A string. The unique identifier of the group.

		Parameter *include_dumps*:
			If true, a list of all dumps will be attached.

		Return value:
			The return value of this method is the info dict of the group, maybe expanded by a list of dumps.
		"""
		grp = get_group(group_id)
		UserError.check(grp, UserError.ENTITY_DOES_NOT_EXIST, message="no such error group", data={"group_id": group_id})
		res = grp.info(as_user)
		if include_dumps:
			res['dumps'] = [d.info(False) for d in grp.get_dumps(None)]
		return res

def errorgroup_list(show_empty, as_user=None):
		"""
		Returns a list of all error groups.
		"""
		res = [grp.info(as_user) for grp in ErrorGroup.objects.all()]
		if show_empty:
			return res
		else:
			return [grp for grp in res if grp['count'] > 0]

def errorgroup_modify(group_id, attrs):
		"""
		Allows to modify the description of the error group.

		Parameter *group_id*:
			A string. The unique identifier of the group.

		Parameter *attrs*:
			A dict with attributes to update. This matches the info dict.
			Only the description can be updated.

		Return value:
			The return value of this method is the info dict of the group.
		"""
		grp = get_group(group_id)
		UserError.check(grp, UserError.ENTITY_DOES_NOT_EXIST, message="no such error group", data={"group_id": group_id})
		grp.modify(attrs)
		grp.save()
		return grp.info()

def errorgroup_remove(group_id):
		"""
		Remove a dump.

		Parameter *dump_id*:
			The unique identifier of the group to be removed.
		"""
		grp = get_group(group_id)
		UserError.check(grp, UserError.ENTITY_DOES_NOT_EXIST, message="no such error group", data={"group_id": group_id})
		grp.remove()

def errordumps_force_refresh():
		"""
		Force a refresh of dumps.
		This is done automatically in a longer interval.
		To get instant access to all dumps, call this function.

		Return value:
			The time in seconds it takes until all dumps should be collected.
		"""
		update_all()

def errorgroup_hide(group_id):
		"""
		Hide an errorgroup.
		It will be shown as soon as a new dump is inserted.

		:param group_id: the group ID
		:return: None
		"""
		grp = get_group(group_id)
		UserError.check(grp, UserError.ENTITY_DOES_NOT_EXIST, message="no such error group", data={"group_id": group_id})
		grp.hide()
		grp.save()

def errorgroup_favorite(username, group_id, is_favorite):
		"""
		Add or remove the group to favorites of the current user

		:param group_id: group to add/remove
		:param is_favorite: True to add, False to remove.
		:return: None
		"""
		grp = get_group(group_id)
		UserError.check(grp, UserError.ENTITY_DOES_NOT_EXIST, message="no such error group", data={"group_id": group_id})
		if is_favorite:
			grp.add_favorite_user(username)
		else:
			grp.remove_favorite_user(username)
		grp.save()