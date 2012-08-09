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

from django.db import models
from tomato import elements, resources
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
	CAP_CHILDREN = {}
	CAP_PARENT = []
	
	class Meta:
		db_table = "tomato_kvm"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = self.ST_CREATED
		elements.Element.init(self, *args, **kwargs)
		self.cpus = 1
		self.ram = 256
		self.kblang = "de"
		self.usbtablet = True
				
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
		self.state = self.ST_PREPARED
		
	def action_destroy(self):
		self.state = self.ST_CREATED

	def action_start(self):
		self.state = self.ST_STARTED
				
	def action_stop(self):
		self.state = self.ST_PREPARED

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["template"] = self.template.name if self.template else None
		return info


elements.TYPE_CLASSES[KVM.TYPE] = KVM