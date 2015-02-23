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

from ..generic import *
from .. import elements, host
from .generic import ST_CREATED, ST_PREPARED, VMElement, VMInterface
from ..lib.error import UserError

class Repy(VMElement):
	TYPE = "repy"
	DIRECT_ATTRS_EXCLUDE = ["ram", "diskspace", "cpus", "bandwidth", "timeout", "template"]
	CAP_CHILDREN = {
		"repy_interface": [ST_CREATED, ST_PREPARED],
	}
	PROFILE_ATTRS = ["ram", "diskspace", "cpus", "bandwidth"]
	DIRECT_ACTIONS_EXCLUDE = ["prepare", "destroy"]

	def action_prepare(self):
		hPref, sPref = self.getLocationPrefs()
		_host = host.select(site=self.site, elementTypes=[self.TYPE]+self.CAP_CHILDREN.keys(), hostPrefs=hPref, sitePrefs=sPref)
		UserError.check(_host, code=UserError.NO_RESOURCES, message="No matching host found for element", data={"type": self.TYPE})
		attrs = self._remoteAttrs
		attrs.update({
			"template": self.template.name,
		})
		attrs.update(self._profileAttrs())
		self.element = _host.createElement(self.TYPE, parent=None, attrs=attrs, ownerElement=self)
		self.save()
		for iface in self.children:
			iface._create()
		self.setState(ST_PREPARED, True)

	def action_destroy(self):
		if self.element:
			for iface in self.children:
				iface._remove()
			self.element.remove()
			self.element = None
		self.setState(ST_CREATED, True)

	ACTIONS = VMElement.ACTIONS.copy()
	ACTIONS.update({
		"prepare": StatefulAction(action_prepare, allowedStates=[ST_CREATED], stateChange=ST_PREPARED),
		"destroy": StatefulAction(action_destroy, allowedStates=[ST_PREPARED], stateChange=ST_CREATED),
	})
	
class Repy_Interface(VMInterface):
	TYPE = "repy_interface"
	CAP_PARENT = [Repy.TYPE]

elements.TYPES[Repy.TYPE] = Repy
elements.TYPES[Repy_Interface.TYPE] = Repy_Interface