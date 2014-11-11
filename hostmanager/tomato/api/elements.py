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

def _getElement(id_):
	el = elements.get(id_, owner=currentUser())
	UserError.check(el, UserError.ENTITY_DOES_NOT_EXIST, "No such element", data={"id": id_})
	return el


def element_create(type, parent=None, attrs=None):  # @ReservedAssignment
	"""
	Creates an element of given type and with the given parent element,
	configuring it with the given attributes by the way.

	The element types that are supported on this host, their attributes,
	possible child and parent elements can be obtained using
	:py:func:`~hostmanager.tomato.api.host.host_capabilities`

	Parameter *type*:
	  The parameter *type* must be a string identifying one of the supported
	  element types.

	Parameter *parent*:
	  If the *parent* parameter is set, this element will become a child
	  element of the element with the given id. Elements must be created as
	  child elements from the start, there is no way to change that later.
	  Element types might restrict type and number of their children elements
	  or the type of their parent element.

	Parameter *attrs*:
	  The attributes of the element can be given as the parameter *attrs*. This
	  parameter must be a :term:`dict` of attributes if given. Attributes can
	  later be changed using :py:func:`element_modify`. This method should
	  behave like::

		 info = element_create(type, parent, {})
		 element_modify(info["id"], attrs)

	Return value:
	  The return value of this method is the info dict of the new element as
	  returned by :py:func:`element_info`. This info dict also contains the
	  element id that is needed for further manipulation of that object.

	Exceptions:
	  If the given parent element does not exist or belongs to another owner
	  an exception *element does not exist* is raised.
	  Various other exceptions can be raised, depending on the given type.
	"""
	if not attrs: attrs = {}
	parentEl = _getElement(int(parent)) if parent else None
	attrs = dict(attrs)
	el = elements.create(type, parentEl, attrs)
	return el.info()


def element_modify(id, attrs):  # @ReservedAssignment
	"""
	Modifies an element, configuring it with the given attributes.

	The attributes that are supported by the element depend on the element
	*type* and can be obtained using
	:py:func:`~hostmanager.tomato.api.host.host_capabilities`
	Attribute availability can depend on the element *state* which can be
	obtained using :py:func:`~element_info`.

	Parameter *id*:
	  The parameter *id* identifies the element by giving its unique id.

	Parameter *attrs*:
	  The attributes of the element can be given as the parameter *attrs*. This
	  parameter must be a dict of attributes.

	Return value:
	  The return value of this method is the info dict of the element as
	  returned by :py:func:`element_info`. This info dict will reflect all
	  attribute changes.

	Exceptions:
	  If the given element does not exist or belongs to another owner
	  an exception *element does not exist* is raised.
	  Various other exceptions can be raised, depending on the element type
	  and state.
	"""
	el = _getElement(int(id))
	el.modify(attrs)
	return el.info()


def element_action(id, action, params=None):  # @ReservedAssignment
	"""
	Performs an action on the element and possibly on its children too.

	The actions that are supported by the element depend on the element
	*type* and can be obtained using
	:py:func:`~hostmanager.tomato.api.host.host_capabilities`
	Action availability can depend on the element *state* which can be
	obtained using :py:func:`~element_info`.

	Note that actions are not restricted to one element. Actions on a parent
	element might (and in reality often will) also cover the child elements.

	Parameter *id*:
	  The parameter *id* identifies the element by giving its unique id.

	Parameter *action*:
	  The parameter *action* is the action to execute on the element.

	Parameter *params*:
	  The parameters for the action (if needed) can be given as the parameter
	  *params*. This parameter must be a dict if given.

	Return value:
	  The return value of this method is  **not the info dict of the element**.
	  Instead this method returns the result of the action. Changes of the
	  action to the element can be checked using :py:func:`~element_info`.

	Exceptions:
	  If the given element does not exist or belongs to another owner
	  an exception *element does not exist* is raised.
	  Various other exceptions can be raised, depending on the element type
	  and state.
	"""
	if not params: params = {}
	el = _getElement(int(id))
	res = el.action(action, params)
	return res


def element_remove(id, recurse=True):  # @ReservedAssignment
	"""
	Removes an element and possibly all its children too.

	Whether elements can be removed in a certain *state* depends on the
	element *type* and can be obtained using
	:py:func:`~hostmanager.tomato.api.host.host_capabilities`
	The element state can be obtained using :py:func:`~element_info`.

	Note that if this element is connected, the connection object will be
	automatically removed before this element is removed. If the connection
	object can not be removed, this method will fail.

	Parameter *id*:
	  The parameter *id* identifies the element by giving its unique id.

	Parameter *recurse*:
	  Since child elements can not exist without their parent element,
	  :py:func:`element_remove` normally fails on elements that have child
	  elements. If *recurse* is set to ``True``, all child elements will be
	  removed before removing the parent element. If child elements child
	  elements of their own, this method will remove them recursively.
	  Note that connections are always removed before their respective element.
	  This means that if this parameter is set to ``True``, all connections
	  of all child elements will also be removed. But even if the parameter is
	  set to ``False`` the connection of the element will be removed
	  automatically.

	Return value:
	  The return value of this method is ``None``.

	Exceptions:
	  If the given element does not exist or belongs to another owner
	  an exception *element does not exist* is raised.
	  Various other exceptions can be raised, depending on the element type
	  and state.
	"""
	el = _getElement(int(id))
	el.remove(recurse)


def element_info(id):  # @ReservedAssignment
	"""
	Retrieves information about an element.

	Parameter *id*:
	  The parameter *id* identifies the element by giving its unique id.

	Return value:
	  The return value of this method is a dict containing information
	  about this element. The information that is returned depends on the
	  *type* and *state* of this element but the following information is
	  always returned.

	``id``
	  The unique id of the element.

	``type``
	  The type of the element.

	``state``
	  The current state this element is in.

	``parent``
	  The unique id of the parent element if this element has one, otherwise
	  ``None``.

	``children``
	  An array of the unique element ids of all child elements. If this element
	  does not have child elements, the array is empty.

	``connection``
	  The unique connection id of the connection of this element, if this
	  element is connected. If this element is not connected this field is
	  ``None``.

	``attrs``
	  A dict of attributes of this element. The contents of this field depends
	  on the *type* and *state* of the element. If this element does not have
	  attributes, this field is ``{}``.

	Exceptions:
	  If the given element does not exist or belongs to another owner
	  an exception *element does not exist* is raised.
	"""
	el = _getElement(int(id))
	return el.info()


def element_list(type_filter=None):
	"""
	Retrieves information about all elements of the user.

	Parameter *type_filter*:
	  If *type_filter* is set, only elements with a matching type will be
	  returned.

	Return value:
	  A list with information entries of all matching elements. Each list entry
	  contains exactly the same information as returned by
	  :py:func:`element_info`. If no element matches, the list is empty.
	"""
	els = elements.getAll(owner=currentUser(), type=type_filter) if type_filter else elements.getAll(
		owner=currentUser())
	return [el.info() for el in els]


from .. import elements, currentUser
from ..lib.error import UserError