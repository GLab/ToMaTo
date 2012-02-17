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
	
def template_info(type, name, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns information about a template

	Parameters:

	Returns: dict of string -> list of templates
	"""
	if not name or name == "auto":
		name = hosts.templates.getDefault(type)
	tpl = hosts.templates.get(type, name)
	if not tpl:
		return None
	return tpl.toDict(user.is_admin)

def template_map(user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Lists all available templates grouped by type.

	Parameters:

	Returns: dict of string -> list of templates
	"""
	return hosts.templates.getMap(user.is_admin)

def template_add(type, name, properties=[], user=None):
	"""
	Adds a template to the template repository. This method requires admin
	access.

	Parameters:
		string type: template type
		string name: template name
		dict propertries: template properties

	Returns: task id
	"""
	_admin_access(user)
	return hosts.templates.add(type, name, properties)

def template_change(type, name, properties, user=None):
	"""
	Changes a template in the template repository. This method requires admin
	access.

	Parameters:
		string type: template type
		string name: template name
		string url: template download url
	"""
	_admin_access(user)
	return hosts.templates.change(type, name, properties)

def template_remove(type, name, user=None):
	"""
	Removes a template from the template repository. This method requires admin
	access.

	Parameters:
		string type: template type
		string name: template name
	"""
	_admin_access(user)
	hosts.templates.remove(type, name)

def template_set_default(type, name, user=None):
	"""
	Selects a template to be the default template for the given type. This
	method requires admin access.

	Parameters:
		string type: template type
		string name: template name
	"""
	_admin_access(user)
	hosts.templates.get(type, name).setDefault()
	
# keep internal imports at the bottom to avoid dependency problems
from tomato.api import _admin_access
from tomato import hosts	