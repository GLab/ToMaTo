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

import os, sys

# tell django to read config from module tomato.config
os.environ['DJANGO_SETTINGS_MODULE']="tomato.config"


# This is the main tomato api file. All access to tomato must use the following 
# methods. Direct import and usage of other classes of tomato is strongly 
# discouraged as it is likely to break tomato.
#
# Note: since xml-rpc does not support None values all methods must return 
# something and all return values must not contain None.

def db_migrate():
	"""
	NOT CALLABLE VIA XML-RPC
	Migrates the database forward to the current structure using migrations
	from the package tomato.migrations.
	"""
	from django.core.management import call_command
	call_command('syncdb', verbosity=0)
	from south.management.commands import migrate
	cmd = migrate.Command()
	cmd.handle(app="tomato", verbosity=1)
	
import config
	
if not config.MAINTENANCE:
	db_migrate()

from auth import login #@UnresolvedImport, pylint: disable-msg=E0611

import generic, topology, devices, connectors, hosts, fault
from lib import log, tasks

def _top_access(top, role, user):
	"""
	NOT CALLABLE VIA XML-RPC
	Asserts the user has access to a topology.
	
	@type top: topology.Topology
	@param top: The topology
	@type role: string
	@param role: The minimal role the user must have, either "user" or "manager"
	@type user: generic.User
	@param user: The user object  
	@rtype: None
	@raise fault.Error: when the user does not have the required privileges 
	"""
	if not top.checkAccess(role, user):
		raise fault.new(fault.ACCESS_TO_TOPOLOGY_DENIED, "access to topology %s denied" % top.id)

def _admin_access(user):
	"""
	NOT CALLABLE VIA XML-RPC
	Asserts the user has admin access.
	
	@type user: generic.User
	@param user: The user object  
	@rtype: None
	@raise fault.Error: when the user does not have the required privileges 
	"""
	if not user.is_admin:
		raise fault.new(fault.ADMIN_ACCESS_DENIED, "admin access denied")
	
def account(user=None):
	"""
	Returns details of the user account. In fact this just returns the given
	user object, but the method is needed for frontends to get information
	about the current user and his groups.
	Note: The password is not part of the user object.
	
	Returns: the user object of the current user
	"""
	return user

def host_info(hostname, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns details about a host. If the host does not exist False is returned.
	
	Parameters:
		string hostname: the name of the host
		  
	Returns: a dict of host details if host exists or False otherwise
	"""
	try:
		return hosts.get(hostname).toDict()
	except hosts.Host.DoesNotExist: # pylint: disable-msg=E1101
		return False

def host_list(group_filter=None, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns details about all hosts as a list. If group filter is "" all hosts
	will be returned otherwise only the hosts within the group (exact match) .
	
	Parameters:
		string group_filter: host filter by group
		
	Returns: a list of dicts describing all matching hosts 
	"""
	res=[]
	qs = hosts.Host.objects.all() # pylint: disable-msg=E1101
	if group_filter:
		qs=qs.filter(group=group_filter)
	for h in qs:
		res.append(h.toDict())
	return res

def host_add(host_name, group_name, enabled, attrs, user=None):
	"""
	Adds a host to the list of available hosts. First host will be checked,
	then all templates will be uploaded and then finally the host will be 
	available. The result of this method is a task id that can be used to
	observe the check and upload progress. This operation needs admin access.
	
	Parameters:
		string host_name: the host name
		string group_name: the name of the host group
		boolean enabled: whether the host should be enabled
		dict attrs: dictionary with host attributes

	Returns: task id of the task
	
	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	return hosts.create(host_name, group_name, enabled, attrs)

def host_change(host_name, group_name, enabled, attrs, user=None):
	"""
	Changes a host. The new values will only apply to new topologies or on state change.
	This operation needs admin access.
	
	Parameters:
		string host_name: the host name
		string group_name: the name of the host group
		boolean enabled: whether the host should be enabled
		dict attrs: dictionary with host attributes

	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	hosts.change(host_name, group_name, enabled, attrs)

def host_remove(host_name, user=None):
	"""
	Deletes a host so that the host and all elements depending on it are 
	removed from the database. This will not remove or stop topologies from
	the host. This operation needs admin access.

	Parameters:	
		string host_name: the host name
	
	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	hosts.remove(host_name)

def host_debug(host_name, user=None):
	"""
	Returns debug information about the host. This operation needs admin access.
	
	Parameters:
		string host_name: the host name

	Returns: Debug information

	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	host = hosts.get(host_name)
	return host.debugInfo()

def host_check(host_name, user=None):
	"""
	Performs a sanity check on the host. This method will return a task id that
	can be used to obtain the results. This operation needs admin access.
	
	Parameters:
		string host_name: the host name
	
	Returns: task id
	
	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	host = hosts.get(host_name)
	return host.check()

def host_groups(user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns a list of all host groups.
	
	Returns: list of all host group names
	"""
	return hosts.getGroups()

def external_network_add(type, group, params, user=None):
	"""
	Adds an external network. This operation needs admin access.
	
	Parameters:
		string type: type of the external network
		string group: group of the external network
		dict params: dict of all additional parameters

	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	if not params.has_key("max_devices"):
		params["max_devices"] = None
	if not params.has_key("avoid_duplicates"):
		params["avoid_duplicates"] = False
	hosts.ExternalNetwork.objects.create(type=type, group=group, max_devices=params["max_devices"], avoid_duplicates=params["avoid_duplicates"])

def external_network_change(type, group, params, user=None):
	"""
	Changes an external network. This operation needs admin access.

	Parameters:	
		string type: type of the external network
		string group: name of the external network
		dict params: dict of all additional parameters

	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	en = hosts.ExternalNetwork.objects.get(type=type, group=group)
	if not params.has_key("max_devices"):
		params["max_devices"] = None
	if not params.has_key("avoid_duplicates"):
		params["avoid_duplicates"] = False
	en.max_devices = params["max_devices"]
	en.avoid_duplicates = params["avoid_duplicates"]
	en.save()

def external_network_remove(type, group, user=None):
	"""
	Removes an external network. This operation needs admin access.
	
	Parameters:
		string type: type of the external network
		string group: name of the external network
	
	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	en = hosts.ExternalNetwork.objects.get(type=type, group=group)
	if len(en.externalnetworkbridge_set.all()):
		raise fault.new(fault.EXTERNAL_NETWORK_HAS_BRIDGES, "External network still has bridges")
	en.delete()

def external_network_bridge_add(host_name, type, group, bridge, user=None):
	"""
	Adds an external network bridge to a host. This operation needs admin access.
	
	Parameters:
		string host_name: name of the host
		string type: type of the external network
		string group: group of the external network
		string bridge: bridge to connect interfaces to
	
	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	host = hosts.get(host_name)
	host.externalNetworksAdd(type, group, bridge)

def external_network_bridge_remove(host_name, type, group, user=None):
	"""
	Removes an external network bridge to a host. This operation needs admin access.
	
	Parameters:
		string host_name: name of the host
		string type: type of the external network
		string group: group of the external network

	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	host = hosts.get(host_name)
	host.externalNetworksRemove(type, group)

def external_networks(user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns a list of all external networks
	
	Returns: a list of all external networks with all bridges

	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	return hosts.external_networks.getAll()

def top_info(top_id, user=None):
	"""
	Returns detailed information about a topology. The information will vary
	depending on the access level of the user.
	
	Parameters:
		int top_id: id of the topology

	Returns: information about the topology

	Errors:
		fault.Error: if the topology is not found	  
	""" 
	top = topology.get(top_id)
	return top.toDict(top.checkAccess("user", user), True)

def top_list(owner_filter=None, host_filter=None, access_filter=None, user=None):
	"""
	Returns brief information about topologies. The set of topologies that will
	be returned can be filtered by owner, by host (affected by the topology) 
	and by access level of the current user. All filters apply subtractively.
	If a filter has the value "" it is not applied.
	
	Parameters:
		string owner_filter: name of the owner to filter by or ""
		string host_filter: name of the host to filter by or ""
		string access_filter: access level to filter by (either "user" or "manager") or ""

	Returns: a list of brief information about topologies
	""" 
	tops=[]
	all_tops = topology.all()
	if owner_filter:
		all_tops = all_tops.filter(owner=owner_filter)
	if host_filter:
		all_tops = all_tops.filter(device__host__name=host_filter).distinct()
	for t in all_tops:
		if (not access_filter) or t.checkAccess(access_filter, user):
			tops.append(t.toDict(t.checkAccess("user", user), False))
	return tops
	
def top_create(user=None):
	"""
	Creates a new empty topology to be modified via top_modify afterwards.
	The user must be a regular user to create topologies.
	
	Returns: the id of the new topology
	""" 
	if not user.is_user:
		raise fault.new(fault.NOT_A_REGULAR_USER, "only regular users can create topologies")
	top=topology.create(user.name)
	top.save()
	top.logger().log("created", user=user.name)
	return top.id

def top_modify(top_id, mods, direct=False, user=None):
	"""
	Applies the list of modifications to the topology. The user must
	have at least manager access to the topology. The result of this method
	is a task id that runs the modifications.
	This method implicitly renews the topology.
	
	Parameters:
		int top_id: the id of the topology
		list of dict mods: the modifications list
		boolean direct: whether to execute the modification directly

	Returns: the id of the modification task (not direct) or None (direct) 
	""" 
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("modifying topology", user=user.name, bigmessage=str(mods))
	import modification
	res = modification.modifyList(top, mods, direct)
	if not direct:
		top.logger().log("started task %s" % res, user=user.name)
	return res

def top_action(top_id, element_type, element_name, action, attrs={}, direct=False, user=None):
	"""
	Executes the given action on a topology element. The minimum user access
	level depends on the action.
	
	Parameters:
		int top_id: the id of the topology
		string element_type: the type of the element (topology, device or connector)
		string element_name: the name of the element
		string action: the action to perform
		dict attrs: attributes for the action
		boolean direct: whether to execute the action directly (non-detached)

	Returns: the id of the action task (not direct) or None (direct) 
	""" 
	top = topology.get(top_id)
	_top_access(top, "user", user)
	if element_type == "topology":
		element = top
	elif element_type == "device":
		element = top.deviceSetGet(element_name)
	elif element_type == "connector":
		element = top.connectorSetGet(element_name)
	if action == "prepare":
		_top_access(top, "manager", user)
		task_id = element.prepare(direct)
	elif action == "destroy":
		_top_access(top, "manager", user)
		task_id = element.destroy(direct)
	elif action == "start":
		_top_access(top, "user", user)
		task_id = element.start(direct)
	elif action == "stop":
		_top_access(top, "user", user)
		task_id = element.stop(direct)
	elif action == "migrate" and element_type =="device":
		_top_access(top, "manager", user)
		task_id = element.migrate(direct)
	elif action == "execute" and element_type =="device":
		_top_access(top, "user", user)
		if element.isOpenvz:
			return element.upcast().execute(attrs["cmd"])
		raise fault.new(fault.UNKNOWN_DEVICE_TYPE, "Execute is only supported for openvz devices")
	if element_type == "topology":
		if action == "remove":
			_top_access(top, "owner", user)
			task_id = top.remove(direct)
		elif action == "renew":
			_top_access(top, "owner", user)
			top.renew()
			return
	top.logger().log("%s %s %s" % (action, element_type, element_name), user=user.name)
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id	
	
def task_list(user=None):
	"""
	Returns a list of all tasks.
	
	Returns: a list of all tasks
	"""
	_admin_access(user)
	return [t.dict() for t in tasks.processes.values()]

def task_status(task_id, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns the details of a speficic task. The task is identified by a unique
	(and random) id that is assumed to be secure.
	
	Parameters:
		string task_id: task id

	Returns: task details
	"""
	return tasks.processes[task_id].dict()
	
def upload_image_uri(top_id, device_id, redirect, user=None):
	top=topology.get(top_id)
	_top_access(top, "manager", user)
	dev=top.deviceSetGet(device_id)
	if not dev.uploadSupported():
		raise fault.new(fault.UPLOAD_NOT_SUPPORTED, "Upload not supported for device %s" % dev)
	top.logger().log("upload image grant %s" % device_id, user=user.name)
	return dev.uploadImageGrant(redirect)

def use_uploaded_image(top_id, device_id, filename, user=None):
	top=topology.get(top_id)
	_top_access(top, "manager", user)
	dev=top.deviceSetGet(device_id)
	if not dev.uploadSupported():
		raise fault.new(fault.UPLOAD_NOT_SUPPORTED, "Upload not supported for device %s" % dev)
	top.logger().log("use uploaded image %s %s" % (device_id, filename), user=user.name)
	return dev.use_uploaded_image(filename)	

def download_image_uri(top_id, device_id, user=None):
	top=topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("download image grant %s" % device_id, user=user.name)
	return top.download_image_uri(device_id)

def download_capture_uri(top_id, connector_id, ifname, user=None):
	top=topology.get(top_id)
	_top_access(top, "user", user)
	return top.download_capture_uri(connector_id, ifname)

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

def template_remove(name, user=None):
	"""
	Removes a template from the template repository. This method requires admin
	access.

	Parameters:
		string name: template name
	"""
	_admin_access(user)
	hosts.templates.remove(name)

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

def errors_all(user=None):
	"""
	Returns a list of all errors in the backend. This method requires admin 
	access.

	Returns: list of all errors
	"""
	_admin_access(user)
	return [f.toDict() for f in fault.errors_all()]

def errors_remove(error_id, user=None):
	"""
	Removes an error from the error list. This method requires admin access.

	Parameters:
		int error_id: id of the error
	"""
	_admin_access(user)
	fault.errors_remove(error_id)

def permission_set(top_id, user_name, role, user=None):
	"""
	Adds a permission entry to a topology. Acceptable roles are "user" and
	"manager". This method requires owner access to the topology.

	Parameters:
		int top_id: id of the topology
		string user_name: user name
		string role: role of the permission (either "user" or "manager")
	"""
	top = topology.get(top_id)
	_top_access(top, "owner", user)
	if user_name != top.owner:
		top.permissionsRemove(user_name)
	if role:
		top.permissionsAdd(user_name, role)
	top.logger().log("set permission: %s=%s" % (user_name, role))
		
def resource_usage_by_user(user=None):
	"""
	Returns a map of resource usage summed up by user (topology owner).
	This method requires admin access.

	Returns: map of resource use by user
	"""
	_admin_access(user)
	usage={}
	for top in topology.all():
		if not top.owner in usage:
			usage[top.owner] = top.resources()
		else:
			d = top.resources()
			for key in d:
				if usage[top.owner].has_key(key):
					usage[top.owner][key] = float(usage[top.owner][key]) + float(d[key]) 
				else:
					usage[top.owner][key] = float(d[key]) 
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
	with open("%s.pub" % config.remote_ssh_key, 'r') as f:
		key = f.read()
	return key