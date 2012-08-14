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
from tomato import connections, elements, resources, config, host
from tomato.lib.attributes import attribute

DOC="""
	Description
	"""

class LXC(elements.Element):
	path = attribute("path", str)
	ram = attribute("ram", int)
	template = models.ForeignKey(resources.Resource, null=True)

	ST_CREATED = "created"
	ST_PREPARED = "prepared"
	ST_STARTED = "started"
	TYPE = "lxc"
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
		"lxc_interface": [ST_CREATED, ST_PREPARED],
	}
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {"ram": 256}
	
	class Meta:
		db_table = "tomato_lxc"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = self.ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		self.path = os.path.join(config.DATA_DIR, "lxc", str(self.id))
				
	def modify_ram(self, ram):
		self.ram = ram
		
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
		self.setState(self.ST_STARTED, True)
				
	def action_stop(self):
		#FIXME: implement
		self.setState(self.ST_PREPARED, True)

	def _relPath(self, file_):
		assert self.path
		return os.path.join(self.path, file_)

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["template"] = self.template.name if self.template else None
		return info


class LXC_Interface(elements.Element):
	name = attribute("name", str)

	TYPE = "lxc_interface"
	CAP_ACTIONS = {
		"__remove__": [LXC.ST_CREATED, LXC.ST_PREPARED]
	}
	CAP_ATTRS = {
		"name": [LXC.ST_CREATED, LXC.ST_PREPARED]
	}
	CAP_CHILDREN = {}
	CAP_PARENT = [LXC.TYPE]
	CAP_CON_PARADIGMS = [connections.PARADIGM_INTERFACE]
	
	class Meta:
		db_table = "tomato_lxc_interface"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = LXC.ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["name"] = self.name
		return info


lxcVersion = host.getDpkgVersion("lxc")

if [0, 7] <= lxcVersion < [0, 8]:
	elements.TYPES[LXC.TYPE] = LXC
	elements.TYPES[LXC_Interface.TYPE] = LXC_Interface
else:
	print "Warning: LXC not supported on lxc version %s" % lxcVersion