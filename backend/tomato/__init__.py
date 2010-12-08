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

"""
This is the main tomato api file. All access to tomato must use the following 
methods. Direct import and usage of other classes of tomato is strongly 
discouraged as it is likely to break tomato.

Note: since xml-rpc does not support None values all methods must return 
something and all return values must not contain None.
"""

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
		raise fault.new(fault.ACCESS_TO_HOST_DENIED, "admin access denied")
	
def login(username, password):
	"""
	Authenticates a user.
	
	@type username: string
	@param username: The users name  
	@type password: string
	@param password: The users password  
	@rtype: generic.User
	@raise fault.Error: when the user does not exist or the password is wrong 
	"""
	if config.auth_dry_run:
		if username=="guest":
			return generic.User(username, False, False)
		elif username=="admin":
			return generic.User(username, True, True)
		else:
			return generic.User(username, True, False)
	else:
		import ldapauth
		return ldapauth.login(username, password)

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

def host_info(hostname, user=None):
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
	except hosts.Host.DoesNotExist:
		return False

def host_list(group_filter="", user=None):
	"""
	Returns details about all hosts as a list. If group filter is "" all hosts
	will be returned otherwise only the hosts within the group (exact match) .
	
	@type user: generic.User  
	@param user: current user
	@type group_filter: string
	@param group_filter: host filter by group 
	"""
	res=[]
	qs = hosts.Host.objects.all()
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
	host = hosts.get_host(host_name)
	host.delete()
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

def host_groups(user=None):
	"""
	Returns a list of all host groups.
	
	@param user: current user
	@type user: generic.User
	@return: all host groups
	@rtype: list of string
	"""
	return hosts.get_host_groups()

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

def special_features_map(user=None):
	"""
	Returns a map of all special features.
	
	@param user: current user
	@type user: generic.User
	@return: a map of all feature types to the available groups of this type
	@rtype: dict of string->string
	@raise fault.Error: if the user does not have enough privileges  
	"""
	return hosts.special_feature_map()

def top_info(id, user=None):
	"""
	Returns detailed information about a topology. The information will vary
	depending on the access level of the user.
	
	@param id: id of the topology
	@type id: int
	@param user: current user
	@type user: generic.User
	@return: information about the topology
	@rtype: dict
	@raise fault.Error: if the topology is not found      
	""" 
	top = topology.get(id)
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
	all = topology.all()
	if owner_filter:
		all = all.filter(owner=owner_filter)
	if host_filter:
		all = all.filter(device__host__name=host_filter).distinct()
	for t in all:
		if (not access_filter) or t.check_access(access_filter, user):
			tops.append(t.to_dict(t.check_access("user", user), False))
	return tops
	
def top_get(top_id, include_ids=False, user=None):
	"""
	Returns the xml specification of a topology. This operation needs user
	access to the topology. If include_ids is True internal values will be
	included in the output.
	
	@param top_id: id of the topology
	@type top_id: number
	@param include_ids: whether to include internal data
	@type include_ids: boolean
	@param user: current user
	@type user: generic.User
	@return: an xml specification of the topology
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "user", user)
	from xml.dom import minidom
	doc = minidom.Document()
	dom = doc.createElement ( "topology" )
	top.save_to(dom, doc, include_ids)
	return dom.toprettyxml(indent="\t", newl="\n")

def top_import(xml, user=None):
	"""
	Creates a new topology by importing a xml topology specification. 
	Internally this method first creates a new empty topology, then converts
	the xml specification to a list of topology modifications and finally
	applies the modifications. The user must be a regular user to create 
	topologies.

	@param xml: xml specification of the topology
	@type xml: string
	@param user: current user
	@type user: generic.User
	@return: the id of the new topology
	@rtype: int
	""" 
	if not user.is_user:
		raise fault.new(fault.NOT_A_REGULAR_USER, "only regular users can create topologies")
	top=topology.create(user.name)
	top.save()
	import modification
	dom = util.parse_xml(xml, "topology")
	modification.apply_spec(top, dom)
	top.logger().log("imported", user=user.name, bigmessage=xml)
	return top.id
	
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

def top_modify(top_id, xml, user=None):
	"""
	Applies the modifications encoded as xml to the topology. The user must
	have at least manager access to the topology. The result of this method
	is a task id that runs the modifications.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param xml: the modifications encoded as xml
	@type xml: int
	@param user: current user
	@type user: generic.User
	@return: the id of the modification task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("modifying topology", user=user.name, bigmessage=xml)
	dom = util.parse_xml(xml, "modifications")
	import modification
	task_id = modification.modify(top, dom)
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id

def top_remove(top_id, user=None):
	"""
	Removes the topology by first bringing all components to the created state
	and then removing it from the database. The result of this method
	is a task id that runs the removal. Only owners of topologies can remove
	them.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param user: current user
	@type user: generic.User
	@return: the id of the task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "owner", user)
	top.logger().log("removing topology", user=user.name)
	task_id = top.remove()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def top_prepare(top_id, user=None):
	"""
	Prepares the topology by bringing all components to the prepared state,
	preparing devices and connectors if needed.
	The result of this method is a task id that runs the state change.
	Only managers of topologies can execute the state change.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param user: current user
	@type user: generic.User
	@return: the id of the task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("preparing topology", user=user.name)
	task_id = top.prepare()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def top_destroy(top_id, user=None):
	"""
	Destroys the topology by bringing all components to the created state,
	stopping and destroying devices and connectors if needed.
	The result of this method is a task id that runs the state change.
	Only managers of topologies can execute the state change.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param user: current user
	@type user: generic.User
	@return: the id of the task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("destroying topology", user=user.name)
	task_id = top.destroy()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def top_start(top_id, user=None):
	"""
	Starts the topology by bringing all components to the started state,
	starting devices and connectors if needed.
	The result of this method is a task id that runs the state change.
	All users of topologies can execute the state change.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param user: current user
	@type user: generic.User
	@return: the id of the task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("starting topology", user=user.name)
	task_id = top.start()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def top_stop(top_id, user=None):
	"""
	Stops the topology by bringing all components to the prepared state,
	stopping devices and connectors if needed.
	The result of this method is a task id that runs the state change.
	All users of topologies can execute the state change.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param user: current user
	@type user: generic.User
	@return: the id of the task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("stopping topology", user=user.name)
	task_id = top.stop()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id

def top_renew(top_id, user=None):
	"""
	This method explicitly renews a topology.
	All users of topologies can execute the renewal.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	""" 
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("renewing topology", user=user.name)
	top.renew()
	return True

def device_prepare(top_id, device_name, user=None):
	"""
	Prepares the device by executing the prepare command on it.	The device
	must be in the created state before, otherwise an exception is raised. 
	The result of this method is a task id that runs the state change.
	Only managers of topologies can execute the state change.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param device_name: the name of the deivce
	@type device_name: string
	@param user: current user
	@type user: generic.User
	@return: the id of the task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("preparing device %s" % device_name, user=user.name)
	device = top.devices_get(device_name)
	task_id = device.prepare()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def device_destroy(top_id, device_name, user=None):
	"""
	Destroys the device by executing the destroy command on it.	The device
	must be in the prepared state before, otherwise an exception is raised. 
	The result of this method is a task id that runs the state change.
	Only managers of topologies can execute the state change.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param device_name: the name of the device
	@type device_name: string
	@param user: current user
	@type user: generic.User
	@return: the id of the task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("destroying device %s" % device_name, user=user.name)
	device = top.devices_get(device_name)
	task_id = device.destroy()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def device_start(top_id, device_name, user=None):
	"""
	Starts the device by executing the start command on it. The device
	must be in the prepared state before, otherwise an exception is raised. 
	The result of this method is a task id that runs the state change.
	All users of topologies can execute the state change.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param device_name: the name of the device
	@type device_name: string
	@param user: current user
	@type user: generic.User
	@return: the id of the task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("starting device %s" % device_name, user=user.name)
	device = top.devices_get(device_name)
	task_id = device.start()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def device_stop(top_id, device_name, user=None):
	"""
	Stops the device by executing the stop command on it. The device
	must be in the started state before, otherwise an exception is raised. 
	The result of this method is a task id that runs the state change.
	All users of topologies can execute the state change.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param device_name: the name of the device
	@type device_name: string
	@param user: current user
	@type user: generic.User
	@return: the id of the task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("stopping device %s" % device_name, user=user.name)
	device = top.devices_get(device_name)
	task_id = device.stop()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id

def connector_prepare(top_id, connector_name, user=None):
	"""
	Prepares the connector by executing the prepare command on it. The connector
	must be in the created state before, otherwise an exception is raised. 
	The result of this method is a task id that runs the state change.
	Only managers of topologies can execute the state change.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param connector_name: the name of the connector
	@type connector_name: string
	@param user: current user
	@type user: generic.User
	@return: the id of the task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("preparing connector %s" % connector_name, user=user.name)
	connector = top.connectors_get(connector_name)
	task_id = connector.prepare()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def connector_destroy(top_id, connector_name, user=None):
	"""
	Destroys the connector by executing the destroy command on it. The connector
	must be in the prepared state before, otherwise an exception is raised. 
	The result of this method is a task id that runs the state change.
	Only managers of topologies can execute the state change.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param connector_name: the name of the connector
	@type connector_name: string
	@param user: current user
	@type user: generic.User
	@return: the id of the task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("destroying connector %s" % connector_name, user=user.name)
	connector = top.connectors_get(connector_name)
	task_id = connector.destroy()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def connector_start(top_id, connector_name, user=None):
	"""
	Starts the connector by executing the start command on it. The connector
	must be in the prepared state before, otherwise an exception is raised. 
	The result of this method is a task id that runs the state change.
	All users of topologies can execute the state change.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param connector_name: the name of the connector
	@type connector_name: string
	@param user: current user
	@type user: generic.User
	@return: the id of the task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("starting connector %s" % connector_name, user=user.name)
	connector = top.connectors_get(connector_name)
	task_id = connector.start()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def connector_stop(top_id, connector_name, user=None):
	"""
	Stops the connector by executing the stop command on it. The connector
	must be in the started state before, otherwise an exception is raised. 
	The result of this method is a task id that runs the state change.
	All users of topologies can execute the state change.
	This method implicitly renews the topology.
	
	@param top_id: the id of the topology
	@type top_id: int
	@param connector_name: the name of the connector
	@type connector_name: string
	@param user: current user
	@type user: generic.User
	@return: the id of the task
	@rtype: string
	""" 
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("stopping connector %s" % connector_name, user=user.name)
	connector = top.connectors_get(connector_name)
	task_id = connector.stop()
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

def task_status(id, user=None):
	"""
	Returns the details of a speficic task. The task is identified by a unique
	(and random) id that is assumed to be secure.
	
	@param id: task id
	@type id: string
	@param user: current user
	@type user: generic.User
	@return: task details
	@rtype: dict  
	"""
	return tasks.TaskStatus.tasks[id].dict()
	
def upload_start(user=None):
	"""
	Start a new upload. This method registers a new upload and returns a
	unique id. The user should upload data chunks using upload_chunk and then
	use the uploaded file.
	
	@param user: current user
	@type user: generic.User
	@return: a unique upload task id
	@rtype: string 
	"""
	task = tasks.UploadTask()
	return task.id

def upload_chunk(upload_id, chunk, user=None):
	"""
	Appends a data chunk to the upload task.
	
	@param upload_id: id of the upload task
	@type upload_id: string
	@param chunk: data chunk
	@type chunk: bytes   
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	"""
	task = tasks.UploadTask.tasks[upload_id]
	task.chunk(chunk.data)
	return True

def upload_image(top_id, device_id, upload_id, user=None):
	"""
	Uses an uploaded file a a disk image for a device. This method might fail 
	if the device is in the wrong state. This operation requires manager 
	access to the topology.
	
	@param top_id: id of the topology
	@type top_id: number
	@param device_id: name of the device
	@type device_id: string
	@param upload_id: id of the upload task
	@type upload_id: string
	@param user: current user
	@type user: generic.User
	@return: task id
	@rtype: string       
	"""
	upload = tasks.UploadTask.tasks[upload_id]
	upload.finished()
	top=topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("uploading image %s" % device_id, user=user.name)
	task_id =  top.upload_image(device_id, upload.filename)
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id

def download_image(top_id, device_id, user=None):
	"""
	Downloads the disk image of a device. This method might fail 
	if the device is in the wrong state. This operation requires manager 
	access to the topology.
	
	@param top_id: id of topology
	@type top_id: number
	@param device_id: name of the device
	@type device_id: string
	@param user: current user
	@type user: generic.User
	@return: id of download task
	@rtype: string
	"""
	top=topology.get(top_id)
	_top_access(top, "manager", user)
	filename = top.download_image(device_id)
	task = tasks.DownloadTask(filename)
	return task.id

def download_capture(top_id, connector_id, device_id, interface_id, user=None):
	"""
	Downloads the captured network data on a connection. This method might fail 
	if the connection is in the wrong state. This operation requires user
	access to the topology.
	
	@param top_id: id of topology
	@type top_id: number
	@param connector_id: name of the connector
	@type connector_id: string
	@param device_id: name of the connected device
	@type device_id: string
	@param interface_id: name of the connected interface
	@type interface_id: string
	@param user: current user
	@type user: generic.User
	@return: id of download task
	@rtype: string
	"""
	top=topology.get(top_id)
	_top_access(top, "user", user)
	filename = top.download_capture(connector_id, device_id, interface_id)
	task = tasks.DownloadTask(filename)
	return task.id

def download_chunk(download_id, user=None):
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

def template_list(type="", user=None):
	"""
	Lists all available templates. The list can be filtered by template type.
	If type is set to "" all templates will be listed, otherwise only 
	templates matching the given type will be listed.

	@param type: template tpye filter
	@type type: string
	@param user: current user
	@type user: generic.User
	@return: list of templates
	@rtype: list of dict
	"""
	if not type:
		type = None
	return [t.to_dict() for t in hosts.get_templates(type)]

def template_add(name, type, url, user=None):
	"""
	Adds a template to the template repository. The template will be fetched 
	from the given url by all hosts. This method requires admin access.

	@param name: template name
	@type name: string
	@param type: template type
	@type type: string
	@param url: template download url
	@type url: string
	@param user: current user
	@type user: generic.User
	@return: task id
	@rtype: string
	"""
	_admin_access(user)
	return hosts.add_template(name, type, url)

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

def template_set_default(type, name, user=None):
	"""
	Selects a template to be the default template for the given type. This
	method requires admin access.

	@param type: template type
	@type type: string
	@param name: template name
	@type name: string
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	"""
	_admin_access(user)
	hosts.get_template(type, name).set_default()
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

def errors_remove(id, user=None):
	"""
	Removes an error from the error list. This method requires admin access.

	@param id: id of the error
	@type id: number
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	"""
	_admin_access(user)
	fault.errors_remove(id)
	return True

def permission_add(top_id, user_name, role, user=None):
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
	top.permissions_add(user_name, role)
	return True
	
def permission_remove(top_id, user_name, user=None):
	"""
	Removes all permissions for the given user on the topology. The owner
	cannot be removed. This method requires owner access to the topology.

	@param top_id: id of the topology
	@type top_id: number
	@param user_name: user name
	@type user_name: string
	@param user: current user
	@type user: generic.User
	@return: True
	@rtype: boolean
	"""
	top = topology.get(top_id)
	_top_access(top, "owner", user)
	top.permissions_remove(user_name)
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

def physical_links_get(src_group, dst_group, user=None):
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
	
def physical_links_get_all(user=None):
	"""
	Returns the statistics of all physical links.

	@param user: current user
	@type user: generic.User
	@return: list of all physical link statistics
	@rtype: list of dict
	"""
	return [l.to_dict() for l in hosts.get_all_physical_links()]