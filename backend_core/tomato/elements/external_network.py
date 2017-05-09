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
from ..elements import Element
from ..host.element import HostElement
from .. import host, elements
from ..resources.network import Network, NetworkInstance
from .generic import ST_CREATED, ST_STARTED, ConnectingElement
from ..lib.error import UserError
from ..lib.constants import ActionName, TypeName

class ExternalNetwork(Element):
	name = StringField()
	samenet = BooleanField(default=False)
	kind = StringField(default='internet')
	network = ReferenceField(Network, reverse_delete_rule=DENY)

	DIRECT_ATTRS = False
	DIRECT_ATTRS_EXCLUDE = []
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {"state": ST_CREATED}

	TYPE = TypeName.EXTERNAL_NETWORK
	DIRECT_ACTIONS = False
	DIRECT_ACTION_EXCLUDE = []
	CAP_CHILDREN = {TypeName.EXTERNAL_NETWORK_ENDPOINT: [ST_CREATED]}
	
	def init(self, *args, **kwargs):
		self.state = ST_CREATED
		Element.init(self, *args, **kwargs)
		if not self.name:
			self.name = self.TYPE + str(self.id)
			self.update_or_save(name=self.name)

	def check_kind(self, val):
		network = Network.get(val)
		UserError.check(network, code=UserError.ENTITY_DOES_NOT_EXIST, message="Network not found")
		return True

	def modify_kind(self, val):
		self.kind = val
		for ch in self.children:
			ch.modify(kind=val)

	def action_stop(self):
		for ch in self.children:
			ch.action(ActionName.STOP, {})
		self.setState(ST_CREATED)

	def action_start(self):
		if self.samenet:
			self.network = Network.get(self.kind)
		for ch in self.children:
			if not ch.state == ST_STARTED:
				ch.action(ActionName.START, {})
		self.setState(ST_STARTED)

	def _nextName(self, baseName):
		num = 0
		names = [ch.name for ch in self.children]
		while baseName + str(num) in names:
			num += 1
		return baseName + str(num)

	ATTRIBUTES = Element.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"name": Attribute(field=name, schema=schema.String(), label="Name"),
		"samenet": StatefulAttribute(field=samenet, writableStates=[ST_CREATED], schema=schema.Bool(), label="Same network"),
		"kind": StatefulAttribute(field=kind, set=modify_kind, check=check_kind, writableStates=[ST_CREATED],
			schema=schema.Identifier(), label="Kind")
	})

	ACTIONS = {
		ActionName.START: StatefulAction(action_start, check=Element.checkTopologyTimeout, allowedStates=[ST_CREATED], stateChange=ST_STARTED),
		ActionName.STOP: StatefulAction(action_stop, allowedStates=[ST_STARTED], stateChange=ST_CREATED),
		Entity.REMOVE_ACTION: StatefulAction(Element._remove, check=Element.checkRemove, allowedStates=[ST_CREATED])
	}


class ExternalNetworkEndpoint(Element, ConnectingElement):
	"""
	:type parent: ExternalNetwork
	:type network: NetworkInstance
	"""
	parent = Element.parent
	_kind = StringField(db_field="kind") #not used anymore
	element = ReferenceField(HostElement, reverse_delete_rule=NULLIFY)
	name = StringField()
	network = ReferenceField(NetworkInstance, reverse_delete_rule=DENY)

	TYPE = TypeName.EXTERNAL_NETWORK_ENDPOINT
	HOST_TYPE = TypeName.EXTERNAL_NETWORK
	CAP_CHILDREN = {}
	
	DIRECT_ATTRS_EXCLUDE = ["network", "timeout"]
	CAP_PARENT = [ExternalNetwork.TYPE]
	DEFAULT_ATTRS = {}
	CAP_CONNECTABLE = True

	SAME_HOST_AFFINITY = 1000 #we definitely want to be on the same host as our connected elements
	
	class Meta:
		db_table = "tomato_external_network_endpoint"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.parent._nextName("port")
			self.update_or_save(name=self.name)

	@property
	def mainElement(self):
		return self.element
	
	def onError(self, exc):
		if self.element:
			try:
				self.element.updateInfo()
			except UserError, err:
				if err.code == UserError.ENTITY_DOES_NOT_EXIST:
					self.element.state = ST_CREATED
			if self.state == ST_CREATED:
				if self.element:
					self.element.remove()
				for iface in self.children:
					iface._remove()
				self.element = None
			self.update_or_save(element=self.element)

	def action_start(self):
		hPref, sPref = self.getLocationPrefs()
		kind = self.parent.network.kind if self.parent and self.parent.samenet else self.parent.kind
		_host = host.select(elementTypeConfigurations=[[TypeName.EXTERNAL_NETWORK]], networkKinds=[kind], hostPrefs=hPref, sitePrefs=sPref)
		UserError.check(_host, code=UserError.NO_RESOURCES, message="No matching host found for element",
			data={"type": self.TYPE})
		if self.parent and self.parent.samenet:
			self.network = NetworkInstance.get(_host, self.parent.network.kind)
		else:
			self.network = NetworkInstance.get(_host, self.parent.kind)
		attrs = {"network": self.network.network.kind}
		self.element = _host.createElement(TypeName.EXTERNAL_NETWORK, parent=None, attrs=attrs, ownerElement=self)
		self.setState(ST_STARTED)
		self.triggerConnectionStart()
		
	def action_stop(self):
		self.triggerConnectionStop()
		if self.element:
			self.element.remove()
			self.element = None
		self.setState(ST_CREATED, True)

	@property
	def readyToConnect(self):
		return bool(self.element)

	ATTRIBUTES = Element.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"name": Attribute(field=name)
	})

	ACTIONS = Element.ACTIONS.copy()
	ACTIONS.update({
		Entity.REMOVE_ACTION: StatefulAction(Element._remove, check=Element.checkRemove, allowedStates=[ST_CREATED]),
		ActionName.START: StatefulAction(action_start, check=Element.checkTopologyTimeout, allowedStates=[ST_CREATED, "default"], stateChange=ST_STARTED),
		ActionName.STOP: StatefulAction(action_stop, allowedStates=[ST_STARTED, ST_CREATED, "default"], stateChange=ST_CREATED)
	})

elements.TYPES[ExternalNetwork.TYPE] = ExternalNetwork
elements.TYPES[ExternalNetworkEndpoint.TYPE] = ExternalNetworkEndpoint