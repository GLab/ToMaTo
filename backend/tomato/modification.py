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
		
	def run(self, top, task):
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
			dev.type = type
			dev.topology = top
			dev.name = self.properties["name"]
			top.device_set_add(dev)
			dev.configure(self.properties, task)
			dev.save()
		elif self.type == "device-rename":
			#FIXME: any steps to do if device is running ?
			device = top.device_set_get(self.element)
			device.name = self.properties["name"]
			device.save()
		elif self.type == "device-configure":
			device = top.device_set_get(self.element).upcast()
			device.configure(self.properties, task)
		elif self.type == "device-delete":
			device = top.device_set_get(self.element).upcast()
			assert device.state == generic.State.CREATED, "Cannot delete a running or prepared device"
			device.delete()
		
		elif self.type == "interface-create":
			device = top.device_set_get(self.element).upcast()
			name = self.properties["name"]
			device.interfaces_add(name, self.properties, task)
		elif self.type == "interface-rename":
			device = top.device_set_get(self.element).upcast()
			name = self.subelement
			device.interfaces_rename(name, self.properties, task)
		elif self.type == "interface-configure":
			device = top.device_set_get(self.element).upcast()
			name = self.subelement
			device.interfaces_configure(name, self.properties, task)
		elif self.type == "interface-delete":
			device = top.device_set_get(self.element).upcast()
			name = self.subelement
			device.interfaces_delete(name, task)
		
		elif self.type == "connector-create":
			ctype = self.properties["type"]
			import tinc, special
			if ctype == "special":
				con = special.SpecialFeatureConnector()
				con.state = generic.State.STARTED
			elif ctype == "hub" or ctype =="switch" or ctype == "router":
				con = tinc.TincConnector()
			else:
				raise fault.new(fault.UNKNOWN_CONNECTOR_TYPE, "Unknown connector type: %s" % type )
			con.type = type
			con.topology = top
			con.name = self.properties["name"]
			top.connector_set_add(con)
			con.configure(self.properties, task)
			con.save()
		elif self.type == "connector-rename":
			#FIXME: any steps to do if connector is running ?
			con = top.connector_set_get(self.element)
			con.name = self.properties["name"]
			con.save()
		elif self.type == "connector-configure":
			con = top.connector_set_get(self.element).upcast()
			con.configure(self.properties, task)
		elif self.type == "connector-delete":
			con = top.connector_set_get(self.element).upcast()
			if not con.is_special(): 
				assert con.state == generic.State.CREATED, "Cannot delete a running or prepared connector"
			con.delete()
		
		elif self.type == "connection-create":
			con = top.connector_set_get(self.element).upcast()
			interface = self.properties["interface"]
			con.connections_add(interface, self.properties, task)
		elif self.type == "connection-configure":
			con = top.connector_set_get(self.element).upcast()
			name = self.subelement
			con.connections_configure(name, self.properties, task)
		elif self.type == "connection-delete":
			con = top.connector_set_get(self.element).upcast()
			name = self.subelement
			con.connections_delete(name, task)
			
		else:
			raise fault.Fault(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Unknown modification type: %s" % self.type)
							
def read_from_dom(dom):
	modlist = []
	for mod in dom.getElementsByTagName("modification"):
		mtype = mod.getAttribute("type")
		element = util.get_attr(mod, "element", None)
		subelement = util.get_attr(mod, "subelement", None)
		properties = {}
		for pr in mod.getElementsByTagName("properties"):
			properties.update(_xml_attrs_to_dict(pr.attributes))
		modlist.append(Modification(mtype, element, subelement, properties))
	return modlist

def _xml_attrs_to_dict(xml):
	res = {}
	for k in xml.keys():
		res[k] = xml[k].value
	return res

def convert_specification(dom):
	modlist = []
	if "name" in dom.attributes.keys():
		modlist.append(Modification("topology-rename", None, None, {"name": dom.attributes["name"].value}))
	for dev in dom.getElementsByTagName("device"):
		devname = dev.getAttribute("name")
		modlist.append(Modification("device-create", None, None, _xml_attrs_to_dict(dev.attributes)))
		for iface in dev.getElementsByTagName("interface"):
			modlist.append(Modification("interface-create", devname, None, _xml_attrs_to_dict(iface.attributes)))
	for con in dom.getElementsByTagName("connector"):
		conname = con.getAttribute("name")
		modlist.append(Modification("connector-create", None, None, _xml_attrs_to_dict(con.attributes)))
		for conn in con.getElementsByTagName("connection"):
			modlist.append(Modification("connection-create", conname, None, _xml_attrs_to_dict(conn.attributes)))
	return modlist

def modify_run(top_id, mods, task):
	for mod in mods:
		top = topology.get(top_id)
		mod.run(top, task)
		task.subtasks_done = task.subtasks_done + 1
	task.done()

def modify(top, dom):
	top.renew()
	mods = read_from_dom(dom)
	task = top.start_task(modify_run, top.id, mods)
	task.subtasks_total = len(mods)
	return task.id

def apply_spec(top, dom):
	top.renew()
	mods = convert_specification(dom)
	task = top.start_task(modify_run, top.id, mods)
	task.subtasks_total = len(mods)
	return task.id