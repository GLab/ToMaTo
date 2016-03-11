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
from ..db import *
from ..host.element import HostElement
from . import Element
from .. import elements, host
from .generic import ST_CREATED, ST_PREPARED, ST_STARTED
from ..lib.error import UserError
from ..lib.constants import ActionName, TypeName

class UDPEndpoint(Element):
	element = ReferenceField(HostElement, reverse_delete_rule=NULLIFY)
	name = StringField()
	connect = StringField()

	DIRECT_ATTRS_EXCLUDE = ["timeout"]
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {}

	TYPE = TypeName.UDP_ENDPOINT
	HOST_TYPE = TypeName.UDP_TUNNEL
	CAP_CHILDREN = {}
	CAP_CONNECTABLE = True

	def init(self, *args, **kwargs):
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + str(self.id)
		self.save()
	
	@property
	def mainElement(self):
		return self.element
	
	def modify_connect(self, val):
		self.connect = val
		if self.element:
			self.element.modify({"connect": val})

	def onError(self, exc):
		if self.element:
			try:
				self.element.updateInfo()
			except UserError, err:
				if err.code == UserError.ENTITY_DOES_NOT_EXIST:
					self.element.state = ST_CREATED
			self.setState(self.element.state, True)
			if self.state == ST_CREATED:
				if self.element:
					self.element.remove()
				for iface in self.children:
					iface._remove()
				self.element = None
			self.save()

	def action_prepare(self):
		_host = host.select(elementTypes=[self.HOST_TYPE])
		UserError.check(_host, code=UserError.NO_RESOURCES, message="No matching host found for element", data={"type": self.TYPE})
		attrs = self._remoteAttrs
		attrs.update({
			"connect": self.connect,
		})
		self.element = _host.createElement(self.remoteType, parent=None, attrs=attrs, ownerElement=self)
		self.save()
		self.setState(ST_PREPARED, True)
		
	def action_destroy(self):
		if self.element:
			self.element.remove()
			self.element = None
		self.setState(ST_CREATED, True)

	def action_stop(self):
		if self.element:
			self.element.action(Action.STOP)
		self.setState(ST_PREPARED, True)
		self.triggerConnectionStop()

	def after_start(self):
		self.triggerConnectionStart()

	@property
	def readyToConnect(self):
		return self.state == ST_STARTED

	ATTRIBUTES = Element.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"name": Attribute(field=name),
		"connect": StatefulAttribute(field=connect, set=modify_connect, writableStates=[ST_CREATED, ST_PREPARED])
	})

	ACTIONS = Element.ACTIONS.copy()
	ACTIONS.update({
		Entity.REMOVE_ACTION: StatefulAction(Element._remove, check=Element.checkRemove, allowedStates=[ST_CREATED]),
		ActionName.STOP: StatefulAction(action_stop, allowedStates=[ST_STARTED], stateChange=ST_PREPARED),
		ActionName.PREPARE: StatefulAction(action_prepare, allowedStates=[ST_CREATED], stateChange=ST_PREPARED),
		ActionName.DESTROY: StatefulAction(action_destroy, allowedStates=[ST_PREPARED], stateChange=ST_CREATED),
	})


elements.TYPES[UDPEndpoint.TYPE] = UDPEndpoint