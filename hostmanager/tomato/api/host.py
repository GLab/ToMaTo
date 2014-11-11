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

from ..lib.util import xml_rpc_sanitize #@UnresolvedImport
from ..lib.newcmd.util.cache import cached #@UnresolvedImport

def host_info():
	"""
	Retrieves general information about the host.
	
	This method returns a multi-level dict with the following host information:
	
	``hostmanager``
	  ``version``
		The version of the ``tomato-hostmanager`` debian package  
	``fileserver_port``
	  The port number of the integrated fileserver
	``address``
	  The public address of the host
	``time``
	  The current time of the host in seconds (and fractions) since the epoch
	  (1970-01-01 00:00:00 UTC).
	``resources``
	  ``cpus_present``
		``count``
		  The number of CPUs (cores) present at the node
		``bogomips_avg``
		  The average *bogomips* performance number reported by the operating 
		  system for each CPU
		  Note that bogomips is not a precise performance measurement, 
		  deviations of up to 5% between different runs for the same CPU are
		  normal.  
		``model``
		  The model of the first CPU as reported by the operating system
	  ``memory``
		``total``, ``used``
		  *Total* and *used* memory in the system in KiB.
	  ``loadavg``
		The average load triple as reported by the operating system 
	  ``diskspace``
		``root``
		  ``total``, ``used``, ``free``
			*Total*, *used* and *free* disk space in the root directory ``/``
			in KiB.
		``data``
		  ``total``, ``used``, ``free``
			*Total*, *used* and *free* disk space in the tomato-hostmanager 
			data directory in KiB.		  
	``uptime``
	  Uptime of the host as reported by the operating system in seconds (and
	  fractions)
	``system``
	  ``kernel``
		Current kernel version as reported by python ``platform.release()``
	  ``distribution``
		Operating system distribution as reported by python ``platform.dist()``
	  ``python``
		Python version as reported by python ``platform.python_version()``	  
	  ``processor``
		Processor architecture as reported by python ``platform.machine()``
		
	**Example**::
	
	  {
		"uptime": 83719.26, 
		"address": "131.246.112.10", 
		"system": {
		  "python": "2.6.6", 
		  "kernel": "2.6.32-11-pve", 
		  "distribution": [
			"debian", 
			"6.0.4", 
			""
		  ], 
		  "processor": "x86_64"
		}, 
		"hostmanager": {
		  "version": "0.0.6"
		}, 
		"time": 1351253635.747105, 
		"fileserver_port": 8888,
		"resources": {
		  "cpus_present": {
			"count": 8, 
			"model": "Intel(R) Xeon(R) CPU		   L5420  @ 2.50GHz", 
			"bogomips_avg": 4981.01375
		  }, 
		  "loadavg": [
			0.0, 
			0.02, 
			0.0
		  ], 
		  "diskspace": {
			"root": {
			  "total": "35092160", 
			  "used": "1925068", 
			  "free": "31384516"
			}, 
			"data": {
			  "total": "513358424", 
			  "used": "5800688", 
			  "free": "507557736"
			}
		  }, 
		  "memory": {
			"total": 16429744, 
			"used": 303756
		  }
		}
	  }
	"""
	return {
		"hostmanager": {
			"version": hostinfo.hostmanagerVersion(),
			"updater": hostinfo.updaterVersion()
		},
		"fileserver_port": config.FILESERVER["PORT"],
		"address": config.PUBLIC_ADDRESS,
		"time": time.time(),
		"problems": hostinfo.problems(),
		"resources": {
			"cpus_present": hostinfo.cpuinfo(),
			"memory": hostinfo.meminfo(),
			"loadavg": hostinfo.loadavg(),
			"diskspace": {
				"root": hostinfo.diskinfo("/"),
				"data": hostinfo.diskinfo(config.DATA_DIR),
			},
		},
		"uptime": hostinfo.uptime(),
		"system": hostinfo.system(),
		"dumps": dump.getCount()
	}

def host_capabilities():
	"""
	Retrieves the capabilities of the host. 
	
	This method returns a dict with information about all available elements,
	connections and resources. If contains the following fields:
	
	``elements``
	  This field is a dict that contains the available element types as keys
	  and one dict with the following information per element type as the 
	  values.
	  
	  ``actions``
		This field contains a dict with all available actions as keys and 
		per action a list with states in which this action is available as 
		value.
	  ``next_state``
		This field contains a dict with all actions that are needed to change
		the state of the element as keys and the resulting states as values.
		Note that not all actions that change the state will be listed here.
		Actions that change the state in an indefinite way will not be listed
		here.
	  ``children``
		This field contains a dict with all allowed children types as keys and 
		per child type a list with states in which this child type can be added
		as value.
	  ``parent``
		This field contains a list of allowed parent types. Since the parent
		can only be set upon creation, the state of this element is already 
		known.
	  ``con_concepts``
		This field contains a list of connection concepts that this element
		supports. The entries in the list are used to find matching connection
		types. If this list is empty, this element can not be connected.
	  ``attrs``
		This field contains a dict with all attribute names as the keys and a
		dict with the following fields as values:

		``name``
		  The name of the attribute, this is the same as the key of the parent 
		  dict.
		``unit``
		  The unit of the value if it is numeric.
		``states``
		  A list with object states in which this attribute can be modified. If
		  this field is not set, the attribute can be modified in all states.
		  Attributes that can not be changed at all are not listed here.
		``default``
		  The default value for this field if it is different from ``None``.
		``null``
		  Whether this field can be set to ``None``. Defaults to ``False``.
		``desc``
		  A short description of the attribute.
		``type``
		  The type of the attribute. The type can either be ``int``, ``float``,
		  ``str`` or ``bool``. If the field is not set, all types, even complex
		  ones, are allowed. If the incoming data is not of this type, a 
		  primitive type conversion using the type methods is tried first 
		  before failing.
		``options``
		  If this field is set, it must contain a list of allowed values. 
		  Setting the attribute to any other value will fail.
		``regExp``
		  If this field is set, all incoming data must match the regular 
		  expression contained in this field. 
		``minValue``, ``maxValue``
		  The minimum and maximum allowed values. 
	
	``connections``
	  This field is a dict that contains the available connections types as 
	  keys and one dict with the following information per connection type
	  as the values.
	  
	  ``actions``
		This field has the same content as the field *actions* in *elements*.
	  ``next_state``
		This field has the same content as the field *next_state* in 
		*elements*.
	  ``con_concepts``
		This field contains a list of connection concept tuples. Each tuple
		is a list of two connection concepts. If elements should be connected,
		this field must contain a tuple where one connection concept is 
		supported by one element and the other is supported by the other 
		element. This field will never be empty since such connection types
		would be useless.
	  ``attrs``
		This field has the same content as the field *attrs* in *elements*.
	
	``resources``
	  This field contains a dict of supported resource types as keys and empty
	  dicts (``{}``) as values.

	"""
	element_types = {}
	for type_, class_ in elements.TYPES.iteritems():
		caps = {}
		for cap in ["actions", "next_state", "children", "parent", "con_concepts"]:
			caps[cap] = getattr(class_, "CAP_"+cap.upper())
		caps["attrs"] = class_.cap_attrs()
		element_types[type_] = caps
	connection_types = {}
	for type_, class_ in connections.TYPES.iteritems():
		caps = {}
		for cap in ["actions", "next_state", "con_concepts"]:
			caps[cap] = getattr(class_, "CAP_"+cap.upper())
		caps["attrs"] = class_.cap_attrs()
		connection_types[type_] = caps
	return xml_rpc_sanitize({
		"elements": element_types,
		"connections": connection_types,
		"resources": dict([(type_, {}) for type_ in resources.TYPES]),
	})

def host_ping(dst):
	return net.ping(dst)

@cached(1800)
def host_networks():
	res = []
	for br in net.bridgeList():
		if not filter(lambda iface: iface.startswith("eth"), net.bridgeInterfaces(br)):
			continue
		data = {"bridge": br}
		data["bytes_received"], data["bytes_sent"] = map(str, net.trafficInfo(br))
		data["dhcp_server"] = dhcp.searchServer(br)
		res.append(data)
	return res

from .. import dump, elements, connections, resources, config
from ..lib.cmd import hostinfo, net, dhcp #@UnresolvedImport
import time