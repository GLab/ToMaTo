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
	
def account(user=None):
	"""
	Returns details of the user account. In fact this just returns the given
	user object, but the method is needed for frontends to get information
	about the current user and his groups.
	Note: The password is not part of the user object.
	
	Returns: the user object of the current user
	"""
	return user.toDict()

def task_list(user=None):
	"""
	Returns a list of all tasks.
	
	Returns: a list of all tasks
	"""
	_admin_access(user)
	return [t.dict(False) for t in tasks.processes.values()]

def task_status(task_id, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns the details of a speficic task. The task is identified by a unique
	(and random) id that is assumed to be secure.
	
	Parameters:
		string task_id: task id

	Returns: task details
	"""
	return tasks.processes[task_id].dict(True)

def task_run(task_name, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Runs a named periodic task and returns the task_id.
	
	Parameters:
		string task_name: name of periodic task

	Returns: task id
	"""
	_admin_access(user)
	process = tasks.periodic_processes[task_name]
	return process.start()
	
def errors_all(user=None):
	"""
	Returns a list of all errors in the backend. This method requires admin 
	access.

	Returns: list of all errors
	"""
	_admin_access(user)
	return [f.toDict() for f in fault.errors_all()]

def errors_remove(error_id=None, user=None):
	"""
	Removes an error from the error list. This method requires admin access.

	Parameters:
		int error_id: id of the error
	"""
	_admin_access(user)
	fault.errors_remove(error_id)

def resource_usage_by_user(user=None):
	"""
	Returns a map of resource usage summed up by user (topology owner).
	This method requires admin access.

	Returns: map of resource use by user
	"""
	_admin_access(user)
	usage={}
	for top in topology.all():
		if not str(top.owner) in usage:
			usage[str(top.owner)] = top.resources()
		else:
			d = top.resources()
			for key in d:
				if usage[str(top.owner)].has_key(key):
					usage[str(top.owner)][key] = float(usage[str(top.owner)][key]) + float(d[key]) 
				else:
					usage[str(top.owner)][key] = float(d[key]) 
	return usage
		
def resource_usage_by_topology(user=None):
	"""
	Returns a map of resource usage summed up by topology.
	This method requires admin access.

	Returns: map of resource use by topology
	"""
	_admin_access(user)
	usage={}
	for top in topology.all():
		d = top.resources()
		if d:
			d.update(top_id=top.id)
			usage[top.name]=d
	return usage

def physical_links_get(src_group, dst_group, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns the statistics of a distinct physical link.

	Parameters:
		string src_group: name of source host group 
		string dst_group: name of destination host group 
	
	Returns: physical link statistics
	"""
	return hosts.physical_links.get(src_group, dst_group).toDict()
	
def physical_links_get_all(user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns the statistics of all physical links.

	Returns: list of all physical link statistics
	"""
	return [l.toDict() for l in hosts.physical_links.getAll()]

def admin_public_key(user=None):
	"""
	Returns the public key that is used for accessing the hosts.

	Returns: public key
	"""
	_admin_access(user)
	with open("%s.pub" % config.SSH_KEY, 'r') as f:
		key = f.read()
	return key

# keep internal imports at the bottom to avoid dependency problems
from tomato.api import _admin_access, _top_access
from tomato import hosts, fault, config, topology
from tomato.lib import tasks