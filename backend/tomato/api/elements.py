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
	id_ = int(id_)
	el = elements.get(id_)
	UserError.check(el, code=UserError.ENTITY_DOES_NOT_EXIST, message="Element with that id does not exist", data={"id": id_})
	return el

def element_create(top, type, parent=None, attrs=None): #@ReservedAssignment
	"""
	Creates an element of given type and with the given parent element, 
	in the given topology, configuring it with the given attributes by the way.
	
	Parameter *top*:
	  The parameter *top* must be the id of an existing topology that the user
	  has permissions to edit.
	
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
	  If the given parent element does not exist or belongs to another topology
	  an exception *element does not exist* is raised.
	  Various other exceptions can be raised, depending on the given type.
	"""
	if not attrs: attrs = {}
	UserError.check(currentUser(), code=UserError.NOT_LOGGED_IN, message="Unauthorized")
	top = _getTopology(top)
	if parent:
		parent = _getElement(parent)
	el = elements.create(top, type, parent, attrs)
	return el.info()

def element_modify(id, attrs): #@ReservedAssignment
	"""
	Modifies an element, configuring it with the given attributes.
   
	The attributes that are supported by the element depend on the element 
	*type* and *state* and can be obtained using :py:func:`~element_info`.   
	
	Additional to the attributes that are supported by the element,
	all attributes beginning with an underscore (``_``) will be accepted.
	This can be used to store addition information needed by a frontend.
	
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
	UserError.check(currentUser(), code=UserError.NOT_LOGGED_IN, message="Unauthorized")
	el = _getElement(id)
	el.modify(attrs)
	return el.info()

def element_action(id, action, params=None): #@ReservedAssignment
	"""
	Performs an action on the element and possibly on its children too.
	
	The actions that are supported by the element depend on the element 
	*type* and *state* and can be obtained using :py:func:`~element_info`.   

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
	UserError.check(currentUser(), code=UserError.NOT_LOGGED_IN, message="Unauthorized")
	el = _getElement(id)
	return el.action(action, params)

def element_remove(id): #@ReservedAssignment
	"""
	Removes an element and possibly all its children too.
	
	Whether an element can be removed depends on the element *type* and *state*
	and can be obtained using :py:func:`~element_info`.   

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
	UserError.check(currentUser(), code=UserError.NOT_LOGGED_IN, message="Unauthorized")
	el = _getElement(id)
	el.remove()

def element_info(id, fetch=False): #@ReservedAssignment
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
	  
	``topology``
	  The id of the topology this element is in.
	  
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

	``cap_actions``
	  A list of actions that are available on this element. The available 
	  actions depend on the element type and state. If the action list contains
	  ``(remove)``, the element can be removed.
	
	``cap_children``
	  A list of element types that this element accepts as child elements.
	  The accepted child element types depend on the element type and state.
	
	``cap_attrs``
	  This field contains a dict of all attributes that this element supports.
	  The keys of the dict are the names of the attribute and the values 
	  are dicts describing the respective attributes:
	  
	  ``name``
		The name of the field. (This is a repetition)
		
	  ``desc``
		A short string describing the field. This string can be used to prompt
		for the value.
		
	  ``type``
		The type of the attribute contents, this can be ``str`` for strings,
		``int`` for integer numbers, ``float`` for floating-point numbers,
		or ``bool`` for boolean values. If this field is not set, the attribute
		can contain any type of data.
		
	  ``enabled``
		Whether the field can be currently set. This depends on the type and 
		the state of the element.
		
	  ``null``
		Whether this field can be ``None``.
		
	  ``default``
		The default value of this attribute if it is not set.
	  
	  ``unit``
		The unit of numeric values.
	  
	  ``options``
		A dict of possible values (keys) with descriptions ready for display 
		(values).
	  
	  ``minvalue``
		If this field is set, the attribute only accepts values greater or 
		equal to this the minimum value.
		
	  ``maxvalue``
		If this field is set, the attribute only accepts values less or 
		equal to this the minimum value.

	  ``regex``
		If this field is set, all values must match the given regular expression.

	Exceptions:
	  If the given element does not exist or belongs to another owner
	  an exception *element does not exist* is raised.
	"""
	UserError.check(currentUser(), code=UserError.NOT_LOGGED_IN, message="Unauthorized")
	el = _getElement(id)
	if fetch:
		el.fetchInfo()
	return el.info()
	
def element_usage(id): #@ReservedAssignment
	"""
	Retrieves usage statistics for an element.
	
	Parameter *id*:
	  The parameter *id* identifies the element by giving its unique id.

	Return value:
	  Usage statistics for the given element according to 
	  :doc:`/docs/accountingdata`.
	"""
	el = _getElement(id)
	return el.totalUsage.info()	

from .. import elements, currentUser
from topology import _getTopology
from ..lib.error import UserError
