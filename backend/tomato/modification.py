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

import util, fault, topology, generic

class Modification():
	def __init__(self, mtype, element, subelement, properties):
		self.type = mtype
		self.element = element
		self.subelement = subelement
		self.properties = properties
		
	def __str__(self):
		return "%s %s %s (%s)" % (self.type, self.element, self.subelement, self.properties)
		
	def run(self, top):
		#print "applying %s" % self
		if self.type == "topology-rename":
			top.name = self.properties["name"]
			top.save()
		elif self.type == "device-create":
			dtype = self.properties["type"]
			import kvm, openvz
			if dtype == "kvm":
				dev = kvm.KVMDevice()
			elif dtype == "openvz":
				dev = openvz.OpenVZDevice()
			else:
				raise fault.new(fault.UNKNOWN_DEVICE_TYPE, "Unknown device type: %s" % type )
			dev.type = dtype
			dev.topology = top
			dev.name = self.properties["name"]
			top.device_set_add(dev)
			dev.configure(self.properties)
			dev.save()
		elif self.type == "device-rename":
			#FIXME: any steps to do if device is running ?
			device = top.device_set_get(self.element)
			device.name = self.properties["name"]
			device.save()
		elif self.type == "device-configure":
			device = top.device_set_get(self.element).upcast()
			device.configure(self.properties)
		elif self.type == "device-delete":
			device = top.device_set_get(self.element).upcast()
			assert device.state == generic.State.CREATED, "Cannot delete a running or prepared device"
			device.delete()
		
		elif self.type == "interface-create":
			device = top.device_set_get(self.element).upcast()
			name = self.properties["name"]
			device.interfaces_add(name, self.properties)
		elif self.type == "interface-rename":
			device = top.device_set_get(self.element).upcast()
			name = self.subelement
			device.interfaces_rename(name, self.properties)
		elif self.type == "interface-configure":
			device = top.device_set_get(self.element).upcast()
			name = self.subelement
			device.interfaces_configure(name, self.properties)
		elif self.type == "interface-delete":
			device = top.device_set_get(self.element).upcast()
			name = self.subelement
			device.interfaces_delete(name)
		
		elif self.type == "connector-create":
			ctype = self.properties["type"]
			import tinc, external
			if ctype == "external":
				con = external.ExternalNetworkConnector()
			elif ctype == "hub" or ctype =="switch" or ctype == "router":
				con = tinc.TincConnector()
			else:
				raise fault.new(fault.UNKNOWN_CONNECTOR_TYPE, "Unknown connector type: %s" % type )
			con.type = ctype
			con.topology = top
			con.name = self.properties["name"]
			top.connector_set_add(con)
			con.configure(self.properties)
			con.save()
		elif self.type == "connector-rename":
			#FIXME: any steps to do if connector is running ?
			con = top.connector_set_get(self.element)
			con.name = self.properties["name"]
			con.save()
		elif self.type == "connector-configure":
			con = top.connector_set_get(self.element).upcast()
			con.configure(self.properties)
		elif self.type == "connector-delete":
			con = top.connector_set_get(self.element).upcast()
			if not con.is_external(): 
				assert con.state == generic.State.CREATED, "Cannot delete a running or prepared connector"
			con.delete()
		
		elif self.type == "connection-create":
			con = top.connector_set_get(self.element).upcast()
			interface = self.properties["interface"]
			con.connections_add(interface, self.properties)
		elif self.type == "connection-configure":
			con = top.connector_set_get(self.element).upcast()
			name = self.subelement
			con.connections_configure(name, self.properties)
		elif self.type == "connection-delete":
			con = top.connector_set_get(self.element).upcast()
			name = self.subelement
			con.connections_delete(name)
			
		else:
			raise fault.Fault(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Unknown modification type: %s" % self.type)
							
def read_from_list(mods):
	modlist = []
	for mod in mods:
		modlist.append(Modification(mod["type"], mod["element"], mod["subelement"], mod["properties"]))
	return modlist

def modify_task_run(top_id, mods):
	for mod in mods:
		top = topology.get(top_id)
		mod.run(top)

def modify(top, mods, direct):
	import tasks
	proc = tasks.Process("modify-topology")
	proc.addTask(tasks.Task("renew", top.renew))
	proc.addTask(tasks.Task("modify", util.curry(modify_task_run, [top.id, mods])))
	return top.start_process(proc, direct)

def modify_list(top, mods, direct):
	mods = read_from_list(mods)
	return modify(top, mods, direct)