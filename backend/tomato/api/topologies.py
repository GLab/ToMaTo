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
	_top_access(top, "user", user)
	return top.toDict(user, True)

def top_list(owner_filter=None, host_filter=None, user=None):
	"""
	Returns brief information about topologies. The set of topologies that will
	be returned can be filtered by owner and by host (affected by the topology) 
	All filters apply subtractively. If a filter has the value "" it is not 
	applied.
	
	Parameters:
		string owner_filter: name of the owner to filter by or ""
		string host_filter: name of the host to filter by or ""

	Returns: a list of brief information about topologies
	""" 
	tops=[]
	all_tops = topology.all()
	if owner_filter:
		from tomato import auth
		owner = auth.getUser(owner_filter)
		fault.check(owner, "Unknown user: %s", owner_filter)
		all_tops = all_tops.filter(owner=owner)
	if host_filter:
		all_tops = all_tops.filter(device__host__name=host_filter).distinct()
	for t in all_tops:
		if t.checkAccess("user", user):
			tops.append(t.toDict(user, False))
	return tops
	
def top_create(user=None):
	"""
	Creates a new empty topology to be modified via top_modify afterwards.
	The user must be a regular user to create topologies.
	
	Returns: the id of the new topology
	""" 
	fault.check(user.is_user, "only regular users can create topologies")
	top=topology.create(user)
	top.save()
	top.log("created", user=user.name)
	return top.id

def top_modify(top_id, mods, direct=False, user=None):
	"""
	Applies the list of modifications to the topology. The user must
	have at least manager access to the topology. The result of this method
	is a task id that runs the modifications.
	This method implicitly renews the topology.
	
	Parameters:
		int top_id: the id of the topology
		list mods: list of modification entries
		boolean direct: whether to execute the modification directly

	Modification syntax:
		Modifications are given as a dict describing the modification.
		string type: the type of the modification
		string element: the name of the element that is targeted by the 
			modification (must be either a device name or a connector name or
			None)
		string subelement: the name of the second-level element that is
		    targeted by the modification (must be either a connection name or
		    an interface name or None)
		dict properties: the properties to give to the element for the 
			modification
			
	Modification types:
		"topology-rename": Renames the topology. The new name must be contained
			in the properties dict as "name". Element and subelement parameters
			are ignored.
		"topology-configure": Configures the topology. The entries of the 
			properties dict will be used for configuration. The element and
			subelement parameters are ignored.
		"device-create": Creates a new device with a given type and name. The 
			name of the device must be contained in the properties dict as 
			"name" (not in the element attribute!). The type of the device must
			be contained in the properties dict as "type". Additional 
			properties for the device can be given in the properties dict but 
			name and type are mandatory. Element and subelement parameters are 
			ignored. 
		"device-rename": Renames a device. The element attribute must contain
			the old name of the device. The new name must be contained in the
			properties dict as "name". The subelement parameter is ignored.
		"device-configure": Configures a device. The element attribute must 
			contain	the name of the device. The entries of the properties dict
			will be sent to the device for configuration. The subelement 
			parameter is ignored.
		"device-delete": Deletes a device. The element attribute must contain
			the name of the device. The subelement parameter and the properties
			dict are ignored.
		"interface-create": Creates a new interface on the given device. The 
			name of the parent device must be given in the element parameter. 
			The name of the interface must be contained in the properties dict
			as "name" (not in the subelement attribute!). Additional properties
			for the interface can be given in the properties dict but the name
			is mandatory. The subelement parameters is ignored. 
		"interface-rename": Renames an interface. The name of the parent device
			must be given in the element parameter. The subelement attribute 
			must contain the old name of the interface. The new name must be 
			contained in the properties dict as "name".
		"interface-configure": Configures an interface. The name of the parent
			device must be given in the element parameter. The subelement 
			attribute must contain the name of the interface. The entries of
			the properties dict will be sent to the interface for
			configuration.
		"interface-delete": Deletes an interface. The name of the parent device
			must be given in the element parameter. The subelement attribute 
			must contain the name of the interface. The properties dict is 
			ignored.
		"connector-create": Creates a new connector with a given type and name.
			The	name of the connector must be contained in the properties dict
			as "name" (not in the element attribute!). The type of the
			connector must be contained in the properties dict as "type".
			Additional properties for the connector can be given in the
			properties dict but	name and type are mandatory. Element and 
			subelement parameters are ignored. 
		"connector-rename": Renames a connector. The element attribute must 
			contain the old name of the connector. The new name must be 
			contained in the properties dict as "name". The subelement 
			parameter is ignored.
		"connector-configure": Configures a connector. The element attribute 
			must contain	the name of the connector. The entries of the 
			properties dict will be sent to the connector for configuration.
			The subelement parameter is ignored.
		"connector-delete": Deletes a connector. The element attribute must 
			contain the name of the connector. The subelement parameter and
			the properties dict are ignored.
		"connection-create": Creates a new connection on the given connector.
			The name of the parent connector must be given in the element 
			parameter. The interface to connect must be given in the format
			DEVICE_NAME.INTERFACE_NAME in the properties dict as "interface"
			(not in the subelement attribute!). The subelement parameter is
			ignored. 
		There is no modification called "connection-rename" !
		"connection-configure": Configures a connection. The name of the parent
			connector must be given in the element parameter. The subelement 
			attribute must contain the connected interface in the format 
			DEVICE_NAME.INTERFACE_NAME. The entries of the properties dict will
			be sent to the connection for configuration.
		"connection-delete": Deletes a connection. The name of the parent 
			connector must be given in the element parameter. The subelement
			attribute must contain the  connected interface in the format
			DEVICE_NAME.INTERFACE_NAME. The properties dict is ignored.

	Returns: the id of the modification task (not direct) or None (direct) 
	""" 
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.log("modifying topology", user=user.name, bigmessage=str(mods))
	from tomato import modification
	res = modification.modifyList(top, mods, direct)
	if not direct:
		top.log("started task %s" % res, user=user.name)
	return res

def top_action(top_id, action, element_type="topology", element_name=None, attrs={}, direct=False, user=None):
	"""
	Executes the given action on a topology element. The minimum user access
	level depends on the action.
	
	Parameters:
		int top_id: the id of the topology
		string action: the action to perform
		string element_type: the type of the element ("topology", "device" or
			 "connector")
		string element_name: the name of the element (None for topology)
		dict attrs: attributes for the action
		boolean direct: whether to execute the action directly (non-detached)

	Available actions:
		"start": Starts the element. Devices and connectors must be in the 
			prepared state before this action. For topologies this means that
			all elements will be first prepared (if needed) and then started
			(if needed). (Supported on topology, device and connector) 
		"stop": Stops the element. Devices and connectors must be in the 
			started state before this action. For topologies this means that
			all elements will be stopped (if needed). (Supported on topology,
			device and connector) 
		"prepare": Prepares the element. Devices and connectors must be in the 
			created state before this action. For topologies this means that
			all elements will be prepared (if needed). (Supported on topology,
			device and connector) 
		"destroy": Destroys the element. Devices and connectors must be in the 
			prepared state before this action. For topologies this means that
			all elements will be first stopped (if needed) and then destroyed
			(if needed). (Supported on topology, device and connector) 

		"remove": Removes a topology. The topology will be stopped and 
			destroyed if needed and finally be removed. (Supported only on 
			topology) 
		"renew": Renews the topology. The timeout timers for the topology will
			be reset to the longest possible values. (Supported only on 
			topology)
			 
		"migrate": Migrates a device onto another host. The host will be select
			by the load balancing algorithm. Migration will be careful to not
			destroy any state. I.e. for started devices a live-migration will
			executed. (Supported only on device) 
		"upload_image_prepare": Prepares a URL for image upload. The image 
			file must then be uploaded to the given URL and then the action
			"upload_image_use" must be called. The result will be a dict
			containing the upload URL as "upload_url" and a filename reference
			for internal use as "filename". If the optional attribute 
			"redirect" is given, a HTML redirect to the given redirect URL
			will be sent after a successful upload. If the redirect URL 
			contains the string "%(filename)s" this string will be replaced by
			the filename. The resulting URL will be returned as "redirect_url"
			(Supported only on device) 
		"upload_image_use": Uses a previously uploaded image for a device. 
			The device must be in state prepared for this action. The mandatory
			attribute "filename" must be internal file reference returned by
			"upload_image_prepare" (Supported only on device) 
		"download_image": Prepares a URL for image download. The returned URL
			can be used to download the image. (Supported only on device) 

		"send_keys": Send keycodes to a KVM device. The keycodes are given as
			an array named "keycodes" in the attributes. Note that the keycodes
			do not directly map to characters. The mapping depends on the 
			keyboard layout that is configured on the device. Key combinations
			can be created by joining them with dashes. (e.g. "ctrl-c" or 
			"ctrl-alt-del"). (Only supported on KVM devices)
		"execute": Execute a command on an OpenVZ device. The command is 
			executed in a shell and the result is returned as a result. Note 
			that interactive commands or commands that do not exit will block
			the call until a timeout occurs. (Only supported on OpenVZ devices)
			
		"download_capture": Prepares a URL to download the captured packets
			of a connection. The connector of the connection must be referenced
			with the element_type and element_name fields. The connection must 
			be given as an attribute named "iface" in the format 
			DEVICE_NAME.INTERFACE_NAME using the device and interface it is
			connected to. (Only supported on some connectors)
			
	Note: the capabilities returned by top_info contain all possible actions 
		of the element and whether they are currently available. 			 
			 
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
	else:
		fault.check(False, "Unknown element type: %s", element_type)
	top.log("%s %s %s" % (action, element_type, element_name), user=user.name)
	return element.action(user, action, attrs, direct)
	
def permission_set(top_id, user_name, role, user=None):
	"""
	Adds a permission entry to a topology. Acceptable roles are "user",
	"manager" and "". This method requires owner access to the topology.
	If the role is empty, existing permissions for the user will be revoked.

	Parameters:
		int top_id: id of the topology
		string user_name: user name
		string role: role of the permission (either "user", "manager" or "")
	"""
	top = topology.get(top_id)
	_top_access(top, "owner", user)
	if user_name != top.owner:
		top.permissionsRemove(user_name)
	if role:
		top.permissionsAdd(user_name, role)
	top.log("set permission: %s=%s" % (user_name, role))
	
# keep internal imports at the bottom to avoid dependency problems
from tomato.api import _top_access
from tomato import topology, fault