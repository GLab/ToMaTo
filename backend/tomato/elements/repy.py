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

from .. import elements, host
import generic
from generic import ST_CREATED, ST_PREPARED, ST_STARTED
from ..lib.error import UserError

class Repy(generic.VMElement):
	TYPE = "repy"
	DIRECT_ATTRS_EXCLUDE = ["ram", "diskspace", "cpus", "bandwidth", "timeout", "template"]
	CAP_CHILDREN = {
		"repy_interface": [generic.ST_CREATED, generic.ST_PREPARED],
	}
	PROFILE_ATTRS = ["ram", "diskspace", "cpus", "bandwidth"]
	DIRECT_ACTIONS_EXCLUDE = ["prepare", "destroy", elements.REMOVE_ACTION]
	CUSTOM_ACTIONS = {
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	class Meta:
		db_table = "tomato_repy"
		app_label = 'tomato'
	def action_prepare(self):
		hPref, sPref = self.getLocationPrefs()
		_host = host.select(site=self.site, elementTypes=[self.TYPE]+self.CAP_CHILDREN.keys(), hostPrefs=hPref, sitePrefs=sPref)
		UserError.check(_host, code=UserError.NO_RESOURCES, message="No matching host found for element", data={"type": self.TYPE})
		attrs = self._remoteAttrs()
		attrs.update({
			"template": self._template().name,
		})
		attrs.update(self._profileAttrs())
		self.element = _host.createElement(self.TYPE, parent=None, attrs=attrs, ownerElement=self)
		self.save()
		for iface in self.getChildren():
			iface._create()
		self.setState(generic.ST_PREPARED, True)
	def action_destroy(self):
		if self.element:
			for iface in self.getChildren():
				iface._remove()
			self.element.remove()
			self.element = None
		self.setState(generic.ST_CREATED, True)

	
class Repy_Interface(generic.VMInterface):
	TYPE = "repy_interface"
	CAP_PARENT = [Repy.TYPE]
	
	class Meta:
		db_table = "tomato_repy_interface"
		app_label = 'tomato'
	
elements.TYPES[Repy.TYPE] = Repy
elements.TYPES[Repy_Interface.TYPE] = Repy_Interface