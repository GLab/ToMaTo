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
	
def template_list(template_type="", user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Lists all available templates. The list can be filtered by template type.
	If template_type is set to "" all templates will be listed, otherwise only 
	templates matching the given type will be listed.

	Parameters:
		string template_type: template type filter

	Returns: list of templates
	"""
	if not template_type:
		template_type = None
	return [t.toDict() for t in hosts.templates.getAll(template_type)]

def template_add(name, template_type, url, user=None):
	"""
	Adds a template to the template repository. The template will be fetched 
	from the given url by all hosts. This method requires admin access.

	Parameters:
		string name: template name
		string template_type: template type
		atring url: template download url

	Returns: task id
	"""
	_admin_access(user)
	return hosts.templates.add(name, template_type, url)

def template_remove(template_type, name, user=None):
	"""
	Removes a template from the template repository. This method requires admin
	access.

	Parameters:
		string template_type: template type
		string name: template name
	"""
	_admin_access(user)
	hosts.templates.remove(template_type, name)

def template_set_default(template_type, name, user=None):
	"""
	Selects a template to be the default template for the given type. This
	method requires admin access.

	Parameters:
		string template_type: template type
		string name: template name
	"""
	_admin_access(user)
	hosts.templates.get(template_type, name).setDefault()
	
# keep internal imports at the bottom to avoid dependency problems
from tomato.api import _admin_access
from tomato import hosts	