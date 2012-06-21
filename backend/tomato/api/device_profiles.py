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
	
def device_profile_info(type, name, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns information about a device profile

	Parameters:

	Returns: dict with device profile
	"""
	if not name or name == "auto":
		name = hosts.device_profiles.getDefault(type)
	prfl = hosts.device_profiles.get(type, name)
	if not prfl:
		return None
	return prfl.toDict(user.is_admin)

def device_profile_map(user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Lists all available device profiles grouped by type.

	Parameters:

	Returns: dict of string -> list of device profiles
	"""
	return hosts.device_profiles.getMap(user.is_admin)

def device_profile_add(type, name, properties=[], user=None):
	"""
	Adds a device profile. This method requires admin access.

	Parameters:
		string type: profile type
		string name: profile name
		dict propertries: profile properties
	"""
	_admin_access(user)
	return hosts.device_profiles.add(type, name, properties)

def device_profile_change(type, name, properties, user=None):
	"""
	Changes a device profile. This method requires admin access.

	Parameters:
		string type: profile type
		string name: profile name
		dict properties: properties of the profile
	"""
	_admin_access(user)
	return hosts.device_profiles.change(type, name, properties)

def device_profile_remove(type, name, user=None):
	"""
	Removes a device profile. This method requires admin access.

	Parameters:
		string type: profile type
		string name: profile name
	"""
	_admin_access(user)
	hosts.device_profiles.remove(type, name)

def device_profile_set_default(type, name, user=None):
	"""
	Selects a device profile to be the default profile for the given type. This
	method requires admin access.

	Parameters:
		string type: profile type
		string name: profile name
	"""
	_admin_access(user)
	hosts.device_profiles.get(type, name).setDefault()
	
# keep internal imports at the bottom to avoid dependency problems
from tomato.api import _admin_access
from tomato import hosts	