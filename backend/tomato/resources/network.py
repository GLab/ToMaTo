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
from .. import resources, fault, host

class Network(resources.Resource):
	kind = models.CharField(max_length=50, unique=True)
	preference = models.IntegerField(default=0)
	
	TYPE = "network"

	class Meta:
		db_table = "tomato_network"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		attrs = args[0]
		fault.check("kind" in attrs, "Network needs attribute kind") 
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
			fault.check(attr in attrs, "Network_Instance needs attribute %s", attr)
		self.network = get(attrs["network"])
		fault.check(self.network, "Network %s does not exist", attrs["kind"])
		self.host = host.get(address=attrs["host"])
		fault.check(self.network, "Host %s does not exist", attrs["host"])
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
		fault.check(net, "No such network: %s", val)
		self.network = net
	
	def modify_host(self, val):
		h = host.get(address=val)
		fault.check(h, "No such host: %s", val)
		self.host = h
	
	def info(self):
		info = resources.Resource.info(self)
		info["attrs"]["network"] = self.network.kind
		info["attrs"]["host"] = self.host.address
		info["attrs"]["bridge"] = self.bridge
		return info

def get(kind):
	return Network.objects.filter(models.Q(kind=kind)|models.Q(kind__startswith=kind+"/")).order_by("preference")[0]

def getInstance(host, kind):
	instances = NetworkInstance.objects
	if kind:
		instances = instances.filter(models.Q(host=host)&(models.Q(network__kind=kind)|models.Q(network__kind__startswith=kind+"/")))
	fault.check(instances, "No network instances found for %s on %s", (kind, host))
	return instances.order_by("network__preference")[0]

resources.TYPES[Network.TYPE] = Network
resources.TYPES[NetworkInstance.TYPE] = NetworkInstance