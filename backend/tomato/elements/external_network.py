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
from .. import elements, resources, host
from ..resources import network as r_network
from ..lib.attributes import Attr #@UnresolvedImport
from generic import ST_CREATED, ST_STARTED
from .. import currentUser
from ..auth import Flags
from ..lib.error import UserError

class External_Network(elements.generic.ConnectingElement, elements.Element):
	name_attr = Attr("name", desc="Name")
	name = name_attr.attribute()
	samenet_attr = Attr("samenet", desc="Single network segment", states=[ST_CREATED], type="bool", default=False)
	samenet = samenet_attr.attribute()
	kind_attr = Attr("kind", type="str", states=[ST_CREATED], default="internet")
	kind = kind_attr.attribute()
	network = models.ForeignKey(r_network.Network, null=True)
	
	CUSTOM_ACTIONS = {
		"start": [ST_CREATED],
		"stop": [ST_STARTED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CUSTOM_ATTRS = {
		"name": name_attr,
		"samenet": samenet_attr,
		"kind": kind_attr,
	}

	DIRECT_ATTRS = False
	DIRECT_ATTRS_EXCLUDE = []
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {}

	TYPE = "external_network"
	DIRECT_ACTIONS = False
	DIRECT_ACTION_EXCLUDE = []
	CAP_CHILDREN = {"external_network_endpoint": [ST_CREATED]}
	
	class Meta:
		db_table = "tomato_external_network"
		app_label = 'tomato'

	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + str(self.id)
		self.save()
	
	def mainElement(self):
		return None
	
	def modify_name(self, val):
		self.name = val

	def modify_samenet(self, val):
		self.samenet = val

	def modify_kind(self, val):
		network = resources.network.get(val)
		if network.restricted and not self.kind == val:
			UserError.check(currentUser().hasFlag(Flags.RestrictedNetworks), code=UserError.DENIED, message="Network is restricted")
		self.kind = val
		for ch in self.getChildren():
			ch.modify({"kind": val})

	def action_stop(self):
		for ch in self.getChildren():
			ch.action("stop", {})
		self.setState(ST_CREATED)

	def action_start(self):
		if self.samenet:
			self.network = r_network.get(self.kind)
		for ch in self.getChildren():
			if not ch.state == ST_STARTED:
				ch.action("start", {})
		self.setState(ST_STARTED)

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["samenet"] = self.samenet
		info["attrs"]["restricted"] = resources.network.get(self.kind).restricted
		return info


class External_Network_Endpoint(elements.generic.ConnectingElement, elements.Element):
	element = models.ForeignKey(host.HostElement, null=True, on_delete=models.SET_NULL)
	name_attr = Attr("name", desc="Name")
	name = name_attr.attribute()
	kind_attr = Attr("kind", type="str", states=[ST_CREATED], default="internet")
	kind = kind_attr.attribute()
	network = models.ForeignKey(r_network.NetworkInstance, null=True)

	TYPE = "external_network_endpoint"
	HOST_TYPE = "external_network"
	CAP_CHILDREN = {}
	
	CUSTOM_ACTIONS = {
		"start": [ST_CREATED, "default"],
		"stop": [ST_STARTED, "default"],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CUSTOM_ATTRS = {
		"name": name_attr,
		"kind": kind_attr,
	}
	DIRECT_ATTRS_EXCLUDE = ["network", "timeout"]
	CAP_PARENT = [None, External_Network.TYPE]
	DEFAULT_ATTRS = {}
	CAP_CONNECTABLE = True

	SAME_HOST_AFFINITY = 50 #we definitely want to be on the same host as our connected elements
	
	class Meta:
		db_table = "tomato_external_network_endpoint"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + str(self.id)
		self.save()
	
	def mainElement(self):
		return self.element
	
	def modify_name(self, val):
		self.name = val

	def modify_kind(self, val):
		self.kind = val

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
				for iface in self.getChildren():
					iface._remove()
				self.element = None
			self.save()

	def action_start(self):
		hPref, sPref = self.getLocationPrefs()
		kind = self.getParent().network.kind if self.parent and self.getParent().samenet else self.kind
		_host = host.select(elementTypes=["external_network"], networkKinds=[kind], hostPrefs=hPref, sitePrefs=sPref)
		UserError.check(_host, code=UserError.NO_RESOURCES, message="No matching host found for element",
			data={"type": self.TYPE})
		if self.parent and self.getParent().samenet:
			self.network = r_network.getInstance(_host, self.getParent().network.kind)
		else:
			self.network = r_network.getInstance(_host, self.kind)			
		attrs = {"network": self.network.network.kind}
		self.element = _host.createElement("external_network", parent=None, attrs=attrs, ownerElement=self)
		self.setState(ST_STARTED)
		self.triggerConnectionStart()
		
	def action_stop(self):
		self.triggerConnectionStop()
		if self.element:
			self.element.remove()
			self.element = None
		self.setState(ST_CREATED, True)

	def readyToConnect(self):
		return bool(self.element)

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		return info

elements.TYPES[External_Network.TYPE] = External_Network	
elements.TYPES[External_Network_Endpoint.TYPE] = External_Network_Endpoint