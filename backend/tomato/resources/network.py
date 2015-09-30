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

from ..db import *
from ..generic import *
from ..host import Host
from ..lib.error import UserError

class Network(Entity, BaseDocument):
	kind = StringField(required=True, unique=True)
	preference = IntField(default=0, required=True)
	restricted = BooleanField(default=False)
	label = StringField()
	description = StringField()
	big_icon = BooleanField(default=False)
	show_as_common = BooleanField(default=False)
	meta = {
		'ordering': ['-preference', 'kind'],
		'indexes': [
			('kind', 'preference')
		]
	}
	@property
	def instances(self):
		return NetworkInstance.objects(network=self)

	def _remove(self):
		self.delete()

	def _checkRemove(self):
		UserError.check(not self.instances.count(), code=UserError.NOT_EMPTY, message="Cannot remove network with instances")
		return True

	ACTIONS = {
		Entity.REMOVE_ACTION: Action(fn=_remove, check=_checkRemove)
	}
	ATTRIBUTES = {
		"id": IdAttribute(),
		"kind": Attribute(field=kind, schema=schema.String()),
		"preference": Attribute(field=preference, schema=schema.Int(minValue=0)),
		"restricted": Attribute(field=restricted, schema=schema.Bool()),
		"big_icon": Attribute(field=big_icon, schema=schema.Bool()),
		"show_as_common": Attribute(field=show_as_common, schema=schema.Bool()),
		"label": Attribute(field=label, schema=schema.String()),
		"description": Attribute(field=description, schema=schema.String())
	}

	def init(self, *args, **kwargs):
		attrs = args[0]
		UserError.check("kind" in attrs, code=UserError.INVALID_CONFIGURATION, message="Network needs attribute kind")
		Entity.init(self, attrs)

	@classmethod
	def get(cls, kind):
		for net in cls.objects:
			if net.kind == kind or net.kind.startswith(kind+"/"):
				return net

	@classmethod
	def create(cls, attrs):
		obj = cls()
		obj.init(attrs)
		obj.save()
		return obj

class NetworkInstance(Entity, BaseDocument):
	"""
	:type network: Network
	:type host: Host
	"""
	from ..host import Host
	network = ReferenceField(Network, required=True, reverse_delete_rule=CASCADE)
	host = ReferenceField(Host, required=True, reverse_delete_rule=CASCADE)
	bridge = StringField(required=True)
	meta = {
		'collection': 'network_instance',
		'ordering': ['network', 'host', 'bridge'],
		'indexes': [
			'network', 'host'
		]
	}

	def remove(self):
		self.delete()

	ACTIONS = {
		Entity.REMOVE_ACTION: Action(fn=remove)
	}
	ATTRIBUTES = {
		"id": IdAttribute(),
		"network": Attribute(set=lambda obj, val: obj.modify_network(val), get=lambda obj: obj.network.kind),
		"host": Attribute(set=lambda obj, val: obj.modify_host(val), get=lambda obj: obj.host.name),
		"bridge": Attribute(field=bridge, schema=schema.Identifier(strict=True))
	}

	def init(self, attrs):
		for attr in ["network", "host", "bridge"]:
			UserError.check(attr in attrs, code=UserError.INVALID_CONFIGURATION, message="Network_Instance needs attribute",
				data={"attribute": attr})
		Entity.init(self, attrs)

	def getBridge(self):
		return self.bridge

	def getKind(self):
		return self.network.kind

	def modify_network(self, val):
		net = Network.get(val)
		UserError.check(net, code=UserError.ENTITY_DOES_NOT_EXIST, message="Network does not exist", data={"network": val})
		self.network = net

	def modify_host(self, val):
		h = Host.get(name=val)
		UserError.check(h, code=UserError.ENTITY_DOES_NOT_EXIST, message="Host does not exist", data={"host": val})
		self.host = h

	@classmethod
	def get(cls, host, kind):
		for net in host.networks:
			k = net.getKind()
			if k == kind or k.startswith(kind+"/"):
				return net
		raise UserError(code=UserError.NO_RESOURCES, message="No network instances found", data={"network": kind, "host": host})

	@classmethod
	def create(cls, attrs):
		obj = cls()
		obj.init(attrs)
		obj.save()
		return obj