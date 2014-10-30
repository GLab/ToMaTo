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

def _getConnection(id_):
	con = connections.get(id_, owner=currentUser())
	UserError.check(con, UserError.ENTITY_DOES_NOT_EXIST, "No such connection", data={"id": id_})
	return con


def connection_create(element1, element2, type=None, attrs=None):  # @ReservedAssignment
	"""
	Connects the given elements using the given type of connection, configuring
	it with the given attributes by the way. The order of the elements does not
	matter. The given connection type must support the element types.
	The elements that are connected can not be changed later.

	The connection types that are supported on this host and their attributes,
	as well as which elements can be connected can be obtained using
	:py:func:`~hostmanager.tomato.api.host.host_capabilities`

	Parameter *element1*:
	  The element id of the first element to include in the connection. The
	  elements that are connected can not be changed later.

	Parameter *element2*:
	  The element id of the second element to include in the connection. The
	  elements that are connected can not be changed later.

	Parameter *type*:
	  If the parameter *type* is specified, it must be a string identifying
	  one of the supported connection types. If *type* is not specified a
	  matching connection type will be determined based on the elements.

	Parameter *attrs*:
	  The attributes of the connection can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes if given. Attributes can
	  later be changed using :py:func:`connection_modify`. This method should
	  behave like::

		 info = connection_create(element1, element2, type, {})
		 connection_modify(info["id"], attrs)

	Return value:
	  The return value of this method is the info dict of the new connection as
	  returned by :py:func:`connection_info`.
	  This info dict also contains the connection id that is needed for further
	  manipulation of that object.

	Exceptions are raised if:
	  * one of the elements does not exist or belongs to a different user
	  * one of the elements does not support to be connected in its current
		state
	  * one of the elements is already connected
	  * both elements are the same
	  * *type* is specified and the type can not be used to connect the
		elements
	  * *type* is not specified and no available connection type can be used to
		connect the elements
	"""
	if not attrs:
		attrs = {}
	el1 = _getElement(element1)
	el2 = _getElement(element2)
	con = connections.create(el1, el2, type, attrs)
	return con.info()


def connection_modify(id, attrs):  # @ReservedAssignment
	"""
	Modifies a connection, configuring it with the given attributes.

	The attributes that are supported by the connection depend on the
	connection *type* and can be obtained using
	:py:func:`~hostmanager.tomato.api.host.host_capabilities`
	Attribute availability can depend on the connection *state* which can be
	obtained using :py:func:`~connection_info`.

	Parameter *id*:
	  The parameter *id* identifies the connection by giving its unique id.

	Parameter *attrs*:
	  The attributes of the connection can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes.

	Return value:
	  The return value of this method is the info dict of the connection as
	  returned by :py:func:`connection_info`. This info dict will reflect all
	  attribute changes.

	Exceptions:
	  If the given connection does not exist or belongs to another owner
	  an exception *connection does not exist* is raised.
	  Various other exceptions can be raised, depending on the connection type
	  and state.
	"""
	con = _getConnection(int(id))
	con.modify(attrs)
	return con.info()


def connection_action(id, action, params=None):  # @ReservedAssignment
	"""
	Performs an action on the connection.

	The actions that are supported by the connection depend on the connection
	*type* and can be obtained using
	:py:func:`~hostmanager.tomato.api.host.host_capabilities`
	Action availability can depend on the connection *state* which can be
	obtained using :py:func:`~connection_info`.

	Parameter *id*:
	  The parameter *id* identifies the connection by giving its unique id.

	Parameter *action*:
	  The parameter *action* is the action to execute on the connection.

	Parameter *params*:
	  The parameters for the action (if needed) can be given as the parameter
	  *params*. This parameter must be a dict if given.

	Return value:
	  The return value of this method is  **not the info dict of the
	  connection**. Instead this method returns the result of the action.
	  Changes of the action to the connection can be checked using
	  :py:func:`~connection_info`.

	Exceptions:
	  If the given connection does not exist or belongs to another owner
	  an exception *connection does not exist* is raised.
	  Various other exceptions can be raised, depending on the connection type
	  and state.
	"""
	if not params:
		params = {}
	con = _getConnection(int(id))
	res = con.action(action, params)
	return res


def connection_remove(id):  # @ReservedAssignment
	"""
	Removes a connection.

	Whether connections can be removed in a certain *state* depends on the
	connection *type* and can be obtained using
	:py:func:`~hostmanager.tomato.api.host.host_capabilities`
	The connection state can be obtained using :py:func:`~connection_info`.

	Parameter *id*:
	  The parameter *id* identifies the connection by giving its unique id.

	Return value:
	  The return value of this method is ``None``.

	Exceptions:
	  If the given connection does not exist or belongs to another owner
	  an exception *connection does not exist* is raised.
	  Various other exceptions can be raised, depending on the connection type
	  and state.
	"""
	con = _getConnection(int(id))
	con.remove()


def connection_info(id):  # @ReservedAssignment
	"""
	Retrieves information about a connection.

	Parameter *id*:
	  The parameter *id* identifies the connection by giving its unique id.

	Return value:
	  The return value of this method is a dict containing information
	  about this connection. The information that is returned depends on the
	  *type* and *state* of this connection but the following information is
	  always returned.

	``id``
	  The unique id of the connection.

	``type``
	  The type of the connection.

	``state``
	  The current state this connection is in.

	``elements``
	  A list with the unique element ids of both elements. This array is always
	  of size 2.

	``attrs``
	  A dict of attributes of this connection. The contents of this field depends
	  on the *type* and *state* of the connection. If this connection does not have
	  attributes, this field is ``{}``.

	Exceptions:
	  If the given connection does not exist or belongs to another owner
	  an exception *connection does not exist* is raised.
	"""
	con = _getConnection(int(id))
	return con.info()


def connection_list():
	"""
	Retrieves information about all connections of the user.

	Return value:
	  A list with information entries of all connections. Each list entry
	  contains exactly the same information as returned by
	  :py:func:`connection_info`. If no connections exist, the list is empty.
	"""
	return [con.info() for con in connections.getAll(owner=currentUser())]


from ..lib.error import UserError
from .. import connections, currentUser
from elements import _getElement