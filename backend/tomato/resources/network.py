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
from .. import resources, host
from ..lib import attributes #@UnresolvedImport
from ..lib.error import UserError

class Network(resources.Resource):
	kind = models.CharField(max_length=50, unique=True)
	preference = models.IntegerField(default=0)
	restricted = attributes.attribute("restricted", bool,False)
	
	TYPE = "network"

	class Meta:
		db_table = "tomato_network"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		attrs = args[0]
		UserError.check("kind" in attrs, code=UserError.INVALID_CONFIGURATION, message="Network needs attribute kind")
		resources.Resource.init(self, *args, **kwargs)
				
	def upcast(self):
		return self
	
	def getBridge(self):
		return self.bridge
	
	def modify_kind(self, val):
		self.kind = val
	
	def modify_preference(self, val):
		self.preference = val

	def info(self):
		info = resources.Resource.info(self)
		info["attrs"]["kind"] = self.kind
		info["attrs"]["preference"] = self.preference
		info["attrs"]["restricted"] = self.restricted
		return info


class NetworkInstance(resources.Resource):
	network = models.ForeignKey(Network, null=False, related_name="instances")
	host = models.ForeignKey(host.Host, null=False, related_name="networks")
	bridge = models.CharField(max_length=20)
	
	TYPE = "network_instance"
	FIELD_NAME = "networkinstance"

	class Meta:
		db_table = "tomato_network_instance"
		app_label = 'tomato'
		unique_together = (("host", "bridge"),)
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		attrs = args[0]
		for attr in ["network", "host", "bridge"]:
			UserError.check(attr in attrs, code=UserError.INVALID_CONFIGURATION, message="Network_Instance needs attribute",
				data={"attribute": attr})
		self.network = get(attrs["network"])
		UserError.check(self.network, code=UserError.ENTITY_DOES_NOT_EXIST, message="Network does not exist",
			data={"network": attrs["kind"]})
		self.host = host.get(name=attrs["host"])
		UserError.check(self.host, code=UserError.ENTITY_DOES_NOT_EXIST, message="Host does not exist",
			data={"network": attrs["host"]})
		self.bridge = attrs["bridge"]
		resources.Resource.init(self, *args, **kwargs)
				
	def upcast(self):
		return self
	
	def getBridge(self):
		return self.bridge
	
	def getKind(self):
		return self.network.kind
	
	def modify_bridge(self, val):
		self.bridge = val
	
	def modify_network(self, val):
		net = get(val)
		UserError.check(net, code=UserError.ENTITY_DOES_NOT_EXIST, message="Network does not exist", data={"network": val})
		self.network = net
	
	def modify_host(self, val):
		h = host.get(name=val)
		UserError.check(h, code=UserError.ENTITY_DOES_NOT_EXIST, message="Host does not exist", data={"host": val})
		self.host = h
	
	def info(self):
		info = resources.Resource.info(self)
		info["attrs"]["network"] = self.network.kind
		info["attrs"]["host"] = self.host.name
		info["attrs"]["bridge"] = self.bridge
		return info

def get(kind):
	return Network.objects.filter(models.Q(kind=kind)|models.Q(kind__startswith=kind+"/")).order_by("-preference")[0]

def getInstance(host, kind):
	instances = NetworkInstance.objects
	if kind:
		instances = instances.filter(models.Q(host=host)&(models.Q(network__kind=kind)|models.Q(network__kind__startswith=kind+"/")))
	UserError.check(instances, code=UserError.NO_RESOURCES, message="No network instances found",
		data={"network": kind, "host": host})
	return instances.order_by("network__preference")[0]

resources.TYPES[Network.TYPE] = Network
resources.TYPES[NetworkInstance.TYPE] = NetworkInstance