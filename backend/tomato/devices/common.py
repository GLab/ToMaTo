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

from tomato.devices import Device, Interface
from tomato.hosts import resources, templates
from tomato import fault, config

import hashlib

class VNCMixin:
	VNC_PORT_SLOT = "vnc"
	
	def getVncPort(self):
		return self.vnc_port.num if self.vnc_port else None
	
	def _assignVncPort(self):
		if not self.vnc_port:
			assert self.host
			self.vnc_port = resources.take(self.host, "port", self, self.VNC_PORT_SLOT)
			self.save()

	def _unassignVncPort(self):
		if self.vnc_port:
			self.vnc_port = None
			self.save()
			resources.give(self, self.VNC_PORT_SLOT)

	def vncPassword(self):
		if not self.getVmid():
			return "---"
		m = hashlib.md5()
		m.update(config.PASSWORD_SALT)
		m.update(str(self.name))
		m.update(str(self.getVmid()))
		m.update(str(self.getVncPort()))
		m.update(str(self.topology.owner))
		return m.hexdigest()
	
	
class VMIDMixin:
	VMID_SLOT = "vmid"
	
	def getVmid(self):
		return self.vmid.num if self.vmid else None

	def _assignVmid(self):
		if not self.vmid:
			assert self.host
			self.vmid = resources.take(self.host, "vmid", self, self.VMID_SLOT)
			self.save()
			
	def _unassignVmid(self):
		if self.vmid:
			self.vmid = None
			self.save()
			resources.give(self, self.VMID_SLOT)

class TemplateMixin:
	def setTemplate(self, value):
		self.template = value
		self.save()

	def getConfiguredTemplate(self):
		return self.template

	def getTemplate(self):
		tpl = templates.findName(self.type, self.template)
		fault.check(tpl, "Template not found")
		return tpl