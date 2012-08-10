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

import os
from django.db import models
from tomato import connections, elements, resources, config
from tomato.lib.attributes import attribute

class KVM(elements.Element):
	path = attribute("path", str)
	cpus = attribute("cpus", int)
	ram = attribute("ram", int)
	kblang = attribute("kblang", str)
	usbtablet = attribute("usbtablet", bool)
	template = models.ForeignKey(resources.Resource, null=True)

	ST_CREATED = "created"
	ST_PREPARED = "prepared"
	ST_STARTED = "started"
	TYPE = "kvm"
	CAP_ACTIONS = {
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		"start": [ST_PREPARED],
		"stop": [ST_STARTED],
		"__remove__": [ST_CREATED],
	}
	CAP_ATTRS = {
		"cpus": [ST_CREATED, ST_PREPARED],
		"ram": [ST_CREATED, ST_PREPARED],
		"kblang": [ST_CREATED, ST_PREPARED],
		"usbtablet": [ST_CREATED, ST_PREPARED],
		"template": [ST_CREATED, ST_PREPARED],
	}
	CAP_CHILDREN = {
		"kvm_interface": [ST_CREATED, ST_PREPARED],
	}
	CAP_PARENT = []
	DEFAULT_ATTRS = {"cpus": 1, "ram": 256, "kblang": "de", "usbtablet": True}
	
	class Meta:
		db_table = "tomato_kvm"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = self.ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		self.path = os.path.join(config.DATA_DIR, "kvm", str(self.id))
				
	def modify_cpus(self, cpus):
		self.cpus = cpus

	def modify_ram(self, ram):
		self.ram = ram
		
	def modify_kblang(self, kblang):
		self.kblang = kblang
		
	def modify_usbtablet(self, usbtablet):
		self.usbtablet = usbtablet
		
	def modify_template(self, tmplName):
		self.template = resources.template.get(self.TYPE, tmplName)

	def action_prepare(self):
		#FIXME: implement
		self.setState(self.ST_PREPARED, True)
		
	def action_destroy(self):
		#FIXME: implement
		self.setState(self.ST_CREATED, True)

	def action_start(self):
		#FIXME: implement
		print " ".join(self._buildCmd())
		self.setState(self.ST_STARTED, True)
				
	def action_stop(self):
		#FIXME: implement
		self.setState(self.ST_PREPARED, True)

	def _relPath(self, file_):
		assert self.path
		return os.path.join(self.path, file_)

	def _buildCmd(self):
		cmd = ["kvm", "-daemonize"]
		cmd += ["-smp", str(self.cpus)]
		cmd += ["-chardev", "socket,id=mon,path=%s,server,nowait" % self._relPath("monitor.socket"), "-mon", "chardev=mon"]
		cmd += ["-vnc", "unix:%s,password" % self._relPath("vnc.socket")]
		cmd += ["-pidfile", self._relPath("pidfile")]
		if self.usbtablet:
			cmd += ["-usbdevice", "tablet"]
		cmd += ["-vga", "cirrus"]
		cmd += ["-k", self.kblang]
		cmd += ["-drive", "file=%s" % self._relPath("hda.qcow2")]
		cmd += ["-m", str(self.ram)]
		cmd += ["-cpuunits", "1000"]
		return cmd

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["template"] = self.template.name if self.template else None
		return info


class KVM_Interface(elements.Element):
	name = attribute("name", str)

	TYPE = "kvm_interface"
	CAP_ACTIONS = {
		"__remove__": [KVM.ST_CREATED, KVM.ST_PREPARED]
	}
	CAP_ATTRS = {
		"name": [KVM.ST_CREATED, KVM.ST_PREPARED]
	}
	CAP_CHILDREN = {}
	CAP_PARENT = [KVM.TYPE]
	CAP_CON_PARADIGMS = [connections.PARADIGM_INTERFACE]
	
	class Meta:
		db_table = "tomato_kvm_interface"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = KVM.ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["name"] = self.name
		return info


elements.TYPES[KVM.TYPE] = KVM
elements.TYPES[KVM_Interface.TYPE] = KVM_Interface