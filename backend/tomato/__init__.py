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
	Migrates the database forward to the current structure using migrations
	from the package tomato.migrations.
	"""
	from django.core.management import call_command
	call_command('syncdb', verbosity=0)
	from south.management.commands import migrate
	cmd = migrate.Command()
	cmd.handle(app="tomato", verbosity=1)
db_migrate()

import config, util
from auth import login #@UnresolvedImport, pylint: disable-msg=E0611

import log, generic, topology, hosts, fault, tasks
import tinc, kvm, openvz

def _top_access(top, role, user):
	"""
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
	if not top.check_access(role, user):
		raise fault.new(fault.ACCESS_TO_TOPOLOGY_DENIED, "access to topology %s denied" % top.id)

def _admin_access(user):
	"""
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
	
	@type user: generic.User  
	@param user: current user
	@rtype: generic.User
	@return: the user object of the current user 
	"""
	return user

def host_info(hostname, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns details about a host. If the host does not exist False is returned.
	
	@type user: generic.User  
	@param user: current user
	@type hostname: string
	@param hostname: the name of the host  
	@rtype: dict or boolean
	@return: a dict of host details if host exists or False otherwise
	"""
	try:
		return hosts.get_host(hostname).to_dict()
	except hosts.Host.DoesNotExist: # pylint: disable-msg=E1101
		return False

def host_list(group_filter="", user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns details about all hosts as a list. If group filter is "" all hosts
	will be returned otherwise only the hosts within the group (exact match) .
	
	@type user: generic.User  
	@param user: current user
	@type group_filter: string
	@param group_filter: host filter by group 
	"""
	res=[]
	qs = hosts.Host.objects.all() # pylint: disable-msg=E1101
	if group_filter:
		qs=qs.filter(group=group_filter)
	for h in qs:
		res.append(h.to_dict())
	return res

def host_add(host_name, group_name, enabled, vmid_start, vmid_count, port_start, port_count, bridge_start, bridge_count, user=None):
	"""
	Adds a host to the list of available hosts. First host will be checked,
	then all templates will be uploaded and then finally the host will be 
	available. The result of this method is a task id that can be used to
	observe the check and upload progress. This operation needs admin access.
	
	@param host_name: the host name
	@type host_name: string
	@param group_name: the name of the host group
	@type group_name: string
	@param enabled: whether the host should be enabled
	@type enabled: boolean
	@param vmid_start: first virtual machine id to be used on this host
	@type vmid_start: number        
	@param vmid_count: number of virtual machine ids to be used on this host
	@type vmid_count: number        
	@param port_start: first port number to be used on this host
	@type port_start: number        
	@param port_count: number of ports to be used on this host
	@type port_count: number        
	@param bridge_start: first bridge id to be used on this host
	@type bridge_start: number        
	@param bridge_count: number of bridge ids to be used on this host
	@type bridge_count: number        
	@param user: current user
	@type user: generic.User
	@return: task id of the task
	@rtype: string
	@raise fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	return hosts.create(host_name, group_name, enabled, vmid_start, vmid_count, port_start, port_count, bridge_start, bridge_count)

def host_change(host_name, group_name, enabled, vmid_start, vmid_count, port_start, port_count, bridge_start, bridge_count, user=None):
	"""
	Changes a host. The new values will only apply to new topologies or on state change.
	This operation needs admin access.
	
	@param host_name: the host name
	@type host_name: string
	@param group_name: the name of the host group
	@type group_name: string
	@param enabled: whether the host should be enabled
	@type enabled: boolean
	@param vmid_start: first virtual machine id to be used on this host
	@type vmid_start: number        
	@param vmid_count: number of virtual machine ids to be used on this host
	@type vmid_count: number        
	@param port_start: first port number to be used on this host
	@type port_start: number        
	@param port_count: number of ports to be used on this host
	@type port_count: number        
	@param bridge_start: first bridge id to be used on this host
	@type bridge_start: number        
	@param bridge_count: number of bridge ids to be used on this host
	@type bridge_count: number        
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	@raise fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	hosts.change(host_name, group_name, enabled, vmid_start, vmid_count, port_start, port_count, bridge_start, bridge_count)
	return True

def host_remove(host_name, user=None):
	"""
	Deletes a host so that the host and all elements depending on it are 
	removed from the database. This will not remove or stop topologies from
	the host. This operation needs admin access.
	
	@param host_name: the host name
	@type host_name: string
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	@raise fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	hosts.remove(host_name)
	return True

def host_debug(host_name, user=None):
	"""
	Returns debug information about the host. This operation needs admin access.
	
	@param host_name: the host name
	@type host_name: string
	@param user: current user
	@type user: generic.User
	@return: Debug infromation
	@rtype: string
	@raise fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	host = hosts.get_host(host_name)
	return host.debug_info()

def host_check(host_name, user=None):
	"""
	Performs a sanity check on the host. This method will return a task id that
	can be used to obtain the results. This operation needs admin access.
	
	@param host_name: the host name
	@type host_name: string
	@param user: current user
	@type user: generic.User
	@return: task id
	@rtype: string
	@raise fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	host = hosts.get_host(host_name)
	return hosts.host_check(host)

def host_groups(user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns a list of all host groups.
	
	@param user: current user
	@type user: generic.User
	@return: all host groups
	@rtype: list of string
	"""
	return hosts.get_host_groups()

def special_feature_group_add(feature_type, group_name, params, user=None):
	"""
	Adds a special feature group. This operation needs admin access.
	
	@param feature_type: type of the special feature group
	@type feature_type: string
	@param group_name: name of the special feature group
	@type group_name: string
	@param params: dict of all additional parameters
	@type params: dict 
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	@raise fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	if not params.has_key("max_devices"):
		params["max_devices"] = None
	if not params.has_key("avoid_duplicates"):
		params["avoid_duplicates"] = False
	hosts.SpecialFeatureGroup.objects.create(feature_type=feature_type, group_name=group_name, max_devices=params["max_devices"], avoid_duplicates=params["avoid_duplicates"])
	return True

def special_feature_group_change(feature_type, group_name, params, user=None):
	"""
	Changes a special feature group. This operation needs admin access.
	
	@param feature_type: type of the special feature group
	@type feature_type: string
	@param group_name: name of the special feature group
	@type group_name: string
	@param params: dict of all additional parameters
	@type params: dict 
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	@raise fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	sfg = hosts.SpecialFeatureGroup.objects.get(feature_type=feature_type, group_name=group_name)
	if not params.has_key("max_devices"):
		params["max_devices"] = None
	if not params.has_key("avoid_duplicates"):
		params["avoid_duplicates"] = False
	sfg.max_devices = params["max_devices"]
	sfg.avoid_duplicates = params["avoid_duplicates"]
	sfg.save()
	return True

def special_feature_group_remove(feature_type, group_name, user=None):
	"""
	Removes a special feature group. This operation needs admin access.
	
	@param feature_type: type of the special feature group
	@type feature_type: string
	@param group_name: name of the special feature group
	@type group_name: string
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	@raise fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	sfg = hosts.SpecialFeatureGroup.objects.get(feature_type=feature_type, group_name=group_name)
	if len(sfg.special_feature_set):
		raise fault.new(fault.SPECIAL_FEATURE_GROUP_NOT_EMPTY, "Special feature group is not empty")
	sfg.remove()
	return True


def special_features_add(host_name, feature_type, feature_group, bridge, user=None):
	"""
	Adds a special feature to a host. This operation needs admin access.
	
	@param host_name: name of the host
	@type host_name: string
	@param feature_type: type of the special feature
	@type feature_type: string
	@param feature_group: group of the special feature
	@type feature_group: string
	@param bridge: bridge to connect interfaces to
	@type bridge: string       
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	@raise fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	host = hosts.get_host(host_name)
	host.special_features_add(feature_type, feature_group, bridge)
	return True

def special_features_remove(host_name, feature_type, feature_group, user=None):
	"""
	Removes a special feature to a host. This operation needs admin access.
	
	@param host_name: name of the host
	@type host_name: string
	@param feature_type: type of the special feature
	@type feature_type: string
	@param feature_group: group of the special feature
	@type feature_group: string
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	@raise fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	host = hosts.get_host(host_name)
	host.special_features_remove(feature_type, feature_group)
	return True

def special_features(user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns a list of all special features.
	
	@param user: current user
	@type user: generic.User
	@return: a list of all feature groups with all instances
	@rtype: list of dict
	@raise fault.Error: if the user does not have enough privileges  
	"""
	return hosts.special_features()

def top_info(top_id, user=None):
	"""
	Returns detailed information about a topology. The information will vary
	depending on the access level of the user.
	
	@param top_id: id of the topology
	@type top_id: int
	@param user: current user
	@type user: generic.User
	@return: information about the topology
	@rtype: dict
	@raise fault.Error: if the topology is not found      
	""" 
	top = topology.get(top_id)
	return top.to_dict(top.check_access("user", user), True)

def top_list(owner_filter, host_filter, access_filter, user=None):
	"""
	Returns brief information about topologies. The set of topologies that will
	be returned can be filtered by owner, by host (affected by the topology) 
	and by access level of the current user. All filters apply subtractively.
	If a filter has the value "" it is not applied.
	
	@param owner_filter: name of the owner to filter by or ""
	@type owner_filter: string
	@param host_filter: name of the host to filter by or ""
	@type host_filter: string
	@param access_filter: access level to filter by (either "user" or "manager") or ""
	@type access_filter: string
	@param user: current user
	@type user: generic.User
	@return: a list of brief information about topologies
	@rtype: list of dict
	""" 
	tops=[]
	all_tops = topology.all()
	if owner_filter:
		all_tops = all_tops.filter(owner=owner_filter)
	if host_filter:
		all_tops = all_tops.filter(device__host__name=host_filter).distinct()
	for t in all_tops:
		if (not access_filter) or t.check_access(access_filter, user):
			tops.append(t.to_dict(t.check_access("user", user), False))
	return tops
	
def top_create(user=None):
	"""
	Creates a new empty topology to be modified via top_modify afterwards.
	The user must be a regular user to create topologies.
	
	@param user: current user
	@type user: generic.User
	@return: the id of the new topology
	@rtype: int
	""" 
	if not user.is_user:
		raise fault.new(fault.NOT_A_REGULAR_USER, "only regular users can create topologies")
	top=topology.create(user.name)
	top.save()
	top.logger().log("created", user=user.name)
	return top.id

def top_modify(top_id, mods, direct, user=None):
	"""
	Applies the list of modifications to the topology. The user must
	have at least manager access to the topology. The result of this method
	is a task id that runs the modifications.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param mods: the modifications list
	@type mods: list of dict
	@param direct: whether to execute the modification directly
	@type direct: boolean
	@param user: current user
	@type user: generic.User
	@return: the id of the modification task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("modifying topology", user=user.name, bigmessage=str(mods))
	import modification
	res = modification.modify_list(top, mods, direct)
	if not direct:
		top.logger().log("started task %s" % res, user=user.name)
	return res

def top_action(top_id, element_type, element_name, action, attrs={}, user=None):
	top = topology.get(top_id)
	_top_access(top, "user", user)
	if element_type == "topology":
		element = top
	elif element_type == "device":
		element = top.device_set_get(element_name)
	elif element_type == "connector":
		element = top.connector_set_get(element_name)
	if action == "prepare":
		_top_access(top, "manager", user)
		task_id = element.prepare()
	elif action == "destroy":
		_top_access(top, "manager", user)
		task_id = element.destroy()
	elif action == "start":
		_top_access(top, "user", user)
		task_id = element.start()
	elif action == "stop":
		_top_access(top, "user", user)
		task_id = element.stop()
	if element_type == "topology":
		if action == "remove":
			_top_access(top, "owner", user)
			task_id = top.remove()
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
	
	@param user: current user
	@type user: generic.User
	@return: a list of all tasks
	@rtype: list of dict
	"""
	_admin_access(user)
	return [t.dict() for t in tasks.TaskStatus.tasks.values()]

def task_status(task_id, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns the details of a speficic task. The task is identified by a unique
	(and random) id that is assumed to be secure.
	
	@param task_id: task id
	@type task_id: string
	@param user: current user
	@type user: generic.User
	@return: task details
	@rtype: dict  
	"""
	return tasks.TaskStatus.tasks[task_id].dict()
	
def upload_image_uri(top_id, device_id, redirect, user=None):
	top=topology.get(top_id)
	_top_access(top, "manager", user)
	dev=top.device_set_get(device_id)
	if not dev.upload_supported():
		raise fault.new(fault.UPLOAD_NOT_SUPPORTED, "Upload not supported for device %s" % dev)
	top.logger().log("upload image grant %s" % device_id, user=user.name)
	return dev.upload_image_grant(redirect)

def use_uploaded_image(top_id, device_id, filename, user=None):
	top=topology.get(top_id)
	_top_access(top, "manager", user)
	dev=top.device_set_get(device_id)
	if not dev.upload_supported():
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

def download_chunk(download_id, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Downloads one chunk of data from the download task. Each chunhk contains up
	to 1MB of data. The last chunk is always empty, all others will contain 
	data. After reading the last chunk the download taask is finished. Reading
	chunks from a finished download task will result in an error.
	
	@param download_id: id of the download task
	@type download_id: string
	@param user: current user
	@type user: generic.User
	@return: chunk of data
	@rtype: bytes
	"""
	task = tasks.DownloadTask.tasks[download_id]
	data = task.chunk()
	import xmlrpclib
	return xmlrpclib.Binary(data)

def template_list(template_type="", user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Lists all available templates. The list can be filtered by template type.
	If template_type is set to "" all templates will be listed, otherwise only 
	templates matching the given type will be listed.

	@param template_type: template type filter
	@type template_type: string
	@param user: current user
	@type user: generic.User
	@return: list of templates
	@rtype: list of dict
	"""
	if not template_type:
		template_type = None
	return [t.to_dict() for t in hosts.get_templates(template_type)]

def template_add(name, template_type, url, user=None):
	"""
	Adds a template to the template repository. The template will be fetched 
	from the given url by all hosts. This method requires admin access.

	@param name: template name
	@type name: string
	@param template_type: template type
	@type template_type: string
	@param url: template download url
	@type url: string
	@param user: current user
	@type user: generic.User
	@return: task id
	@rtype: string
	"""
	_admin_access(user)
	return hosts.add_template(name, template_type, url)

def template_remove(name, user=None):
	"""
	Removes a template from the template repository. This method requires admin
	access.

	@param name: template name
	@type name: string
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	"""
	_admin_access(user)
	hosts.remove_template(name)
	return True

def template_set_default(template_type, name, user=None):
	"""
	Selects a template to be the default template for the given type. This
	method requires admin access.

	@param template_type: template type
	@type template_type: string
	@param name: template name
	@type name: string
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	"""
	_admin_access(user)
	hosts.get_template(template_type, name).set_default()
	return True

def errors_all(user=None):
	"""
	Returns a list of all errors in the backend. This method requires admin 
	access.

	@param user: current user
	@type user: generic.User
	@return: list of all errors
	@rtype: list of dict
	"""
	_admin_access(user)
	return [f.to_dict() for f in fault.errors_all()]

def errors_remove(error_id, user=None):
	"""
	Removes an error from the error list. This method requires admin access.

	@param error_id: id of the error
	@type error_id: number
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	"""
	_admin_access(user)
	fault.errors_remove(error_id)
	return True

def permission_set(top_id, user_name, role, user=None):
	"""
	Adds a permission entry to a topology. Acceptable roles are "user" and
	"manager". This method requires owner access to the topology.

	@param top_id: id of the topology
	@type top_id: number
	@param user_name: user name
	@type user_name: string
	@param role: role of the permission (either "user" or "manager")
	@type role: string
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	"""
	top = topology.get(top_id)
	_top_access(top, "owner", user)
	if user_name != top.owner:
		top.permissions_remove(user_name)
	if role:
		top.permissions_add(user_name, role)
	top.logger().log("set permission: %s=%s" % (user_name, role))
	return True
		
def resource_usage_by_user(user=None):
	"""
	Returns a map of resource usage summed up by user (topology owner).
	This method requires admin access.

	@param user: current user
	@type user: generic.User
	@return: map of resource use by user
	@rtype: dict of string->dict
	"""
	_admin_access(user)
	usage={}
	for top in topology.all():
		if top.resources:
			if not top.owner in usage:
				usage[top.owner] = top.resources.encode()
			else:
				usage[top.owner] = generic.add_encoded_resources(usage[top.owner], top.resources.encode())
	return usage
		
def resource_usage_by_topology(user=None):
	"""
	Returns a map of resource usage summed up by topology.
	This method requires admin access.

	@param user: current user
	@type user: generic.User
	@return: map of resource use by topology
	@rtype: dict of string->dict
	"""
	_admin_access(user)
	usage={}
	for top in topology.all():
		if top.resources:
			d = top.resources.encode()
			d.update(top_id=top.id)
			usage[top.name]=d
	return usage

def physical_links_get(src_group, dst_group, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns the statistics of a dictinct physical link.

	@param src_group: name of source host group 
	@type src_group: string 
	@param dst_group: name of destination host group 
	@type dst_group: string 
	@param user: current user
	@type user: generic.User
	@return: physical link statistics
	@rtype: dict
	"""
	return hosts.get_physical_link(src_group, dst_group).to_dict()
	
def physical_links_get_all(user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns the statistics of all physical links.

	@param user: current user
	@type user: generic.User
	@return: list of all physical link statistics
	@rtype: list of dict
	"""
	return [l.to_dict() for l in hosts.get_all_physical_links()]

def admin_public_key(user=None):
	"""
	Returns the public key that is used for accessing the hosts.

	@param user: current user
	@type user: generic.User
	@return: public key
	@rtype: string
	"""
	_admin_access(user)
	with open("%s.pub" % config.remote_ssh_key, 'r') as f:
		key = f.read()
	return key