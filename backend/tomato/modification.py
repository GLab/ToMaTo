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

import fault, topology, generic

from devices import kvm, openvz, prog
from connectors import external, vpn
from lib import util

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
			if dtype == "kvm":
				dev = kvm.KVMDevice()
			elif dtype == "openvz":
				dev = openvz.OpenVZDevice()
			elif dtype == "prog":
				dev = prog.ProgDevice()
			else:
				raise fault.new("Unknown device type: %s" % type )
			dev.topology = top
			dev.type = dtype
			dev.name = self.properties["name"]
			dev.init()
			dev.save()
			top.deviceSetAdd(dev)
			dev.configure(self.properties)
			dev.save()
		elif self.type == "device-rename":
			#FIXME: any steps to do if device is running ?
			device = top.deviceSetGet(self.element)
			device.name = self.properties["name"]
			device.save()
		elif self.type == "device-configure":
			device = top.deviceSetGet(self.element).upcast()
			device.configure(self.properties)
		elif self.type == "device-delete":
			device = top.deviceSetGet(self.element).upcast()
			fault.check(device.state == generic.State.CREATED, "Cannot delete a running or prepared device")
			device.delete()
		
		elif self.type == "interface-create":
			device = top.deviceSetGet(self.element).upcast()
			name = self.properties["name"]
			device.interfacesAdd(name, self.properties)
		elif self.type == "interface-rename":
			device = top.deviceSetGet(self.element).upcast()
			name = self.subelement
			device.interfacesRename(name, self.properties)
		elif self.type == "interface-configure":
			device = top.deviceSetGet(self.element).upcast()
			name = self.subelement
			device.interfacesConfigure(name, self.properties)
		elif self.type == "interface-delete":
			device = top.deviceSetGet(self.element).upcast()
			name = self.subelement
			device.interfacesDelete(name)
		
		elif self.type == "connector-create":
			ctype = self.properties["type"]
			if ctype == "external":
				con = external.ExternalNetworkConnector()
			elif ctype == "hub" or ctype =="switch" or ctype == "router":
				con = vpn.TincConnector()
			else:
				raise fault.new("Unknown connector type: %s" % type )
			con.type = ctype
			con.topology = top
			con.name = self.properties["name"]
			con.init()
			top.connectorSetAdd(con)
			con.configure(self.properties)
			con.save()
		elif self.type == "connector-rename":
			#FIXME: any steps to do if connector is running ?
			con = top.connectorSetGet(self.element)
			con.name = self.properties["name"]
			con.save()
		elif self.type == "connector-configure":
			con = top.connectorSetGet(self.element).upcast()
			con.configure(self.properties)
		elif self.type == "connector-delete":
			con = top.connectorSetGet(self.element).upcast()
			if not con.isExternal(): 
				fault.check(con.state == generic.State.CREATED, "Cannot delete a running or prepared connector")
			con.delete()
		
		elif self.type == "connection-create":
			con = top.connectorSetGet(self.element).upcast()
			interface = self.properties["interface"]
			con.connectionsAdd(interface, self.properties)
		elif self.type == "connection-configure":
			con = top.connectorSetGet(self.element).upcast()
			name = self.subelement
			con.connectionsConfigure(name, self.properties)
		elif self.type == "connection-delete":
			con = top.connectorSetGet(self.element).upcast()
			name = self.subelement
			con.connectionsDelete(name)
			
		else:
			raise fault.Fault("Unknown modification type: %s" % self.type)
							
def readFromList(mods):
	modlist = []
	for mod in mods:
		modlist.append(Modification(mod["type"], mod["element"], mod["subelement"], mod["properties"]))
	return modlist

def modifyTaskRun(top_id, mods):
	for mod in mods:
		top = topology.get(top_id)
		mod.run(top)

def modify(top, mods, direct):
	from lib import tasks
	proc = tasks.Process("modify-topology")
	proc.add(tasks.Task("renew", top.renew))
	proc.add(tasks.Task("modify", util.curry(modifyTaskRun, [top.id, mods])))
	return top.startProcess(proc, direct)

def modifyList(top, mods, direct):
	mods = readFromList(mods)
	return modify(top, mods, direct)