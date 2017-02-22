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

def _getResource(id_):
	res = resources.get(id_)
	UserError.check(res, UserError.ENTITY_DOES_NOT_EXIST, "No such resource", data={"id": id_})
	return res


def resource_create(type, attrs=None):  # @ReservedAssignment
	"""
	Creates a resource of given type, configuring it with the given attributes
	by the way.

	The resource types that are supported on this host can be obtained using
	:py:func:`~hostmanager.tomato.api.host.host_capabilities`

	Parameter *type*:
	  The parameter *type* must be a string identifying one of the supported
	  resource types.

	Parameter *attrs*:
	  The attributes of the resource can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes if given. Attributes can
	  later be changed using :py:func:`resource_modify`. This method should
	  behave like::

		 info = resource_create(type, {})
		 resource_modify(info["id"], attrs)

	Return value:
	  The return value of this method is the info dict of the new resource as
	  returned by :py:func:`resource_info`. This info dict also contains the
	  resource id that is needed for further manipulation of that object.

	Exceptions:
	  Various other exceptions can be raised, depending on the given type.
	"""
	if not attrs: attrs = {}
	attrs = dict(attrs)
	res = resources.create(type, attrs)
	return res.info()


def resource_modify(id, attrs):  # @ReservedAssignment
	"""
	Modifies a resource, configuring it with the given attributes.

	The attributes that are supported by the resource depend on the resource
	*type*.

	Parameter *id*:
	  The parameter *id* identifies the resource by giving its unique id.

	Parameter *attrs*:
	  The attributes of the resource can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes.

	Return value:
	  The return value of this method is the info dict of the resource as
	  returned by :py:func:`resource_info`. This info dict will reflect all
	  attribute changes.

	Exceptions:
	  If the given resource does not exist an exception *resource does not
	  exist* is raised.
	  Various other exceptions can be raised, depending on the resource type.
	"""
	res = _getResource(str(id))
	res.modify(attrs)
	return res.info()


def resource_remove(id):  # @ReservedAssignment
	"""
	Removes a resource.

	Parameter *id*:
	  The parameter *id* identifies the resource by giving its unique id.

	Return value:
	  The return value of this method is ``None``.

	Exceptions:
	  If the given resource does not exist an exception *resource does not
	  exist* is raised.
	  Various other exceptions can be raised, depending on the resource type.
	"""
	res = _getResource(str(id))
	res.remove()


def resource_info(id):  # @ReservedAssignment
	"""
	Retrieves information about a resource.

	Parameter *id*:
	  The parameter *id* identifies the resource by giving its unique id.

	Return value:
	  The return value of this method is a dict containing information
	  about this resource. The information that is returned depends on the
	  *type* of this resource but the following information is always returned.

	``id``
	  The unique id of the element.

	``type``
	  The type of the element.

	``attrs``
	  A dict of attributes of this resource. The contents of this field depend
	  on the *type* of the resource. If this resource does not have attributes,
	  this field is ``{}``.

	Exceptions:
	  If the given resource does not exist an exception *resource does not
	  exist* is raised.
	"""
	res = _getResource(str(id))
	return res.info()


def resource_list(type_filter=None):
	"""
	Retrieves information about all resources.

	Parameter *type_filter*:
	  If *type_filter* is set, only resources with a matching type will be
	  returned.

	Return value:
	  A list with information entries of all matching resources. Each list
	  entry contains exactly the same information as returned by
	  :py:func:`resource_info`. If no resource matches, the list is empty.
	"""

	res = resources.getAll(type=type_filter) if type_filter else resources.getAll()
	return [r.info() for r in res]


from .. import resources
from ..lib.error import UserError