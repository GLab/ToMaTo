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
from ..topology import Topology
from ..lib import logging
from ..accounting.quota import UsageStatistics
from ..lib.decorators import *
from ..lib.cache import cached
from ..lib.error import UserError
from ..connections import Connection

TYPES = {}

class Element(LockedStatefulEntity, BaseDocument):
	"""
	:type topology: Topology
	:type parent: Element
	:type connection: connections.Connection
	:type clientData: dict
	:type directData: dict
	:type hostElements: list of host.HostElement
	:type hostConnections: list of host.HostConnection
	"""
	topology = ReferenceField(Topology, required=True, reverse_delete_rule=DENY)
	topologyId = ReferenceFieldId(topology)
	state = StringField(choices=['default', 'created', 'prepared', 'started'], required=True)
	parent = GenericReferenceField()
	parentId = ReferenceFieldId(parent)
	connection = ReferenceField(Connection, reverse_delete_rule=NULLIFY)
	connectionId = ReferenceFieldId(connection)
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True, reverse_delete_rule=DENY)
	hostElements = ListField(ReferenceField('HostElement', reverse_delete_rule=PULL), db_field='host_elements')
	hostConnections = ListField(ReferenceField('HostConnection', reverse_delete_rule=PULL), db_field='host_connections')
	clientData = DictField(db_field='client_data')
	directData = DictField(db_field='direct_data')
	
	meta = {
		'allow_inheritance': True,
		'indexes': [
			'topology', 'state', 'parent',
			{'fields': ['topology'], 'cls': False},
			{'fields': ['parent'], 'cls': False},
		]
	}
	@property
	def children(self):
		return Element.objects(parent=self) if self.id else []
	
	DIRECT_ACTIONS = True
	DIRECT_ACTIONS_EXCLUDE = []

	DIRECT_ATTRS = True
	DIRECT_ATTRS_EXCLUDE = []

	HOST_TYPE = ""
	
	DOC = ""

	CAP_CHILDREN = {}
	CAP_PARENT = []
	CAP_CONNECTABLE = False

	TYPE = None

	@property
	def type(self):
		return self.TYPE

	# whether neighboring elements should be on the same host/site
	SAME_HOST_AFFINITY = -10 #distribute load
	SAME_SITE_AFFINITY = 20 #keep traffic local and latencies low
	
	def init(self, topology, parent=None, attrs=None):
		if not attrs: attrs = {}
		if parent:
			UserError.check(parent.type in self.CAP_PARENT, code=UserError.INVALID_VALUE,
				message="Parent type not allowed for this type", data={"parent_type": parent.type, "type": self.type})
			UserError.check(self.type in parent.CAP_CHILDREN, code=UserError.INVALID_VALUE,
				message="Parent does not allow children of this type", data={"parent_type": parent.type, "type": self.type})
			UserError.check(parent.state in parent.CAP_CHILDREN[self.type], code=UserError.INVALID_STATE,
				message="Parent does not allow children of this type in its current state",
				data={"parent_type": parent.type, "type": self.type, "parent_state": parent.state})
		else:
			UserError.check(None in self.CAP_PARENT, code=UserError.INVALID_CONFIGURATION, message="Type needs parent",
				data={"type": self.type})
		self.topology = topology
		self.permissions = topology.permissions
		self.parent = parent
		self.totalUsage = UsageStatistics.objects.create()
		Entity.init(self, attrs)

	@property
	def hasParent(self):
		return not self.parent is None

	@property
	def mainElement(self):
		return None

	@property
	def remoteType(self):
		return self.HOST_TYPE or self.type

	@property
	def _remoteAttrs(self):
		caps = host.getElementCapabilities(self.remoteType)
		allowed = caps["attributes"].keys() if caps else []
		attrs = {}
		for key, value in self.info().iteritems():
			if key in allowed:
				attrs[key] = value
		return attrs

	def checkUnknownAttribute(self, key, value):
		if key.startswith("_"):
			return True
		UserError.check(self.DIRECT_ATTRS and not key in self.DIRECT_ATTRS_EXCLUDE,
			code=UserError.UNSUPPORTED_ATTRIBUTE, message="Unsupported attribute")
		if self.mainElement:
			allowed = self.mainElement.getAllowedAttributes().keys()
		else:
			caps = host.getElementCapabilities(self.remoteType)
			allowed = caps["attributes"].keys() if caps else []
		UserError.check(key in allowed, code=UserError.UNSUPPORTED_ATTRIBUTE, message="Unsupported attribute")
		return True

	def setUnknownAttributes(self, attrs):
		remoteAttrs = {}
		for key, value in attrs.items():
			if key.startswith("_"):
				self.clientData[key[1:]] = value
			else:
				remoteAttrs[key] = value
		self.directData.update(remoteAttrs)
		if self.mainElement:
			self.mainElement.modify(remoteAttrs)

	def checkUnknownAction(self, action, params=None):
		UserError.check(self.DIRECT_ACTIONS and not action in self.DIRECT_ACTIONS_EXCLUDE,
			code=UserError.UNSUPPORTED_ACTION, message="Unsupported action (no direct actions for this type)")
		UserError.check(self.mainElement, code=UserError.UNSUPPORTED_ACTION, message="Unsupported action (not deployed)")
		if not action in self.mainElement.getAllowedActions():
			self.mainElement.updateInfo()
			self.state = self.mainElement.state
			self.save()
		UserError.check(action in self.mainElement.getAllowedActions(),
			code=UserError.UNSUPPORTED_ACTION, message="Unsupported action (not supported by deployed element)")
		return True

	def executeUnknownAction(self, action, params=None):
		try:
			if hasattr(self, "before_%s" % action):
				getattr(self, "before_%s" % action)(**params)
			res = self.mainElement.action(action, params)
			self.setState(self.mainElement.state, True)
			if hasattr(self, "after_%s" % action):
				getattr(self, "after_%s" % action)(**params)
		except Exception, exc:
			self.onError(exc)
			raise
		return res

	def checkRemove(self, recurse=True):
		UserError.check(recurse or self.children.empty(), code=UserError.NOT_EMPTY, message="Cannot remove element with children")
		for ch in self.children:
			ch.checkRemove(recurse=recurse)
		if self.connection:
			self.connection.checkRemove()
		return True

	def setState(self, state, recursive=False):
		if recursive:
			for ch in self.children:
				ch.setState(state, True)
		self.state = state
		self.save()

	def _remove(self, recurse=True):
		logging.logMessage("info", category="topology", id=self.idStr, info=self.info())
		logging.logMessage("remove", category="topology", id=self.idStr)
		if self.parent:
			self.parent.onChildRemoved(self)
		if self.id:
			for ch in self.children:
				ch.remove()
			for hel in self.hostElements:
				try:
					hel.remove()
				except:
					pass
			for hcon in self.hostConnections:
				try:
					hcon.remove()
				except:
					pass
		if self.connection:
			self.connection.remove()
		if self.id:
			self.delete()
		self.totalUsage.remove()

	def onChildAdded(self, child):
		pass
	
	def onChildRemoved(self, child):
		pass

	@property
	def connectableElement(self):
		return None

	@property
	def connectedElement(self):
		if not self.connection:
			return None
		els = self.connection.elements
		assert len(els) == 2, "Connection %s has %d elements" % (self, len(els))
		if self.id == els[0].id:
			return els[1]
		if self.id == els[1].id:
			return els[0]
		assert False
		
	def getLocationData(self, maxDepth=3):
		"""
		Determines where this element is located and how much it wants other elements to be close by.
		Elements that are mainly connections other elements might overwrite this and use location
		data of these elements instead.
		Since this calculation can get stuck in a loop the depth is limited by a parameter. The
		maxDepth is decremented each time the calculation spans another element group.
		 
		@param maxDepth: Parameter limiting the maximal depth of calculation
		"""
		els = set()
		for el in self.hostElements:
			els.add((el, self.SAME_HOST_AFFINITY, self.SAME_SITE_AFFINITY))
		return els
			
	def getLocationPrefs(self, children=True):
		"""
		Calculate and return host and site preferences by collecting and merging location data
		of connected elements 
		"""
		hostPrefs = {}
		sitePrefs = {}
		if self.connection:
			for el, sha, ssa in self.connectedElement.getLocationData():
				if not el.host:
					return #can this even happen?
				hostPrefs[el.host] = hostPrefs.get(el.host, 0.0) + sha + self.SAME_HOST_AFFINITY
				sitePrefs[el.host.site] = sitePrefs.get(el.host.site, 0.0) + ssa + self.SAME_SITE_AFFINITY
		if children:
			for ch in self.children:
				hPref, sPref = ch.getLocationPrefs()
				for host, pref in hPref.iteritems():
					hostPrefs[host] = hostPrefs.get(host, 0.0) + pref 
				for site, pref in sPref.iteritems():
					sitePrefs[site] = sitePrefs.get(site, 0.0) + pref
		return (hostPrefs, sitePrefs)
			
	def triggerConnectionStart(self):
		if self.connection:
			self.connection.triggerStart()
			
	def triggerConnectionStop(self):
		if self.connection:
			self.connection.triggerStop()

	def onError(self, exc):
		pass

	@classmethod
	def selectCapabilitiesHost(cls, host_):
		if not (cls.DIRECT_ACTIONS or cls.DIRECT_ATTRS):
			return host_
		type_ = cls.HOST_TYPE or cls.TYPE
		if not host_ or not type_ in host_.elementTypes:
			host_ = host.select(elementTypes=[type_], best=False)
		return host_

	@classmethod
	@cached(timeout=3600, maxSize=None)
	def getCapabilities(cls, host_):
		caps = cls.capabilities()
		host_ = cls.selectCapabilitiesHost(host_)
		if cls.DIRECT_ATTRS or cls.DIRECT_ACTIONS:
			host_cap = host_.getElementCapabilities(cls.HOST_TYPE or cls.TYPE)
		if cls.DIRECT_ACTIONS:
			# noinspection PyUnboundLocalVariable
			for action, params in host_cap["actions"].iteritems():
				if action in caps["actions"]: continue
				if not action in cls.DIRECT_ACTIONS_EXCLUDE:
					if action == '__remove__':
						action = Entity.REMOVE_ACTION
					if action in caps["actions"]:
						continue
					if isinstance(params, list):
						params = {'state_change': None, 'param_schema': None, 'description': None, 'allowed_states': params}
					caps["actions"][action] = params
		if cls.DIRECT_ATTRS:
			for attr, params in host_cap["attributes"].iteritems():
				if attr in caps["attributes"]: continue
				if not attr in cls.DIRECT_ATTRS_EXCLUDE:
					caps["attributes"][attr] = params
		caps.update(children=cls.CAP_CHILDREN, parent=cls.CAP_PARENT, connectable=cls.CAP_CONNECTABLE)
		return caps
			
	def info(self, childrenIdsHint=None):
		# Speed optimization: use existing information to avoid database accesses
		if not childrenIdsHint is None:
			self._childrenIds = childrenIdsHint
		mel = self.mainElement
		if isinstance(mel, HostElement):
			info = mel.objectInfo.get("attrs", {})
		else:
			info = {}
		if self.directData:
			info.update(self.directData)
		info.update(LockedStatefulEntity.info(self))
		for key, val in self.clientData.items():
			info["_"+key] = val
		return info

	def fetchInfo(self):
		if self.mainElement:
			self.mainElement.updateInfo()

	def __str__(self):
		return "%s_%s" % (self.type, self.id)
		
	@property
	def readyToConnect(self):
		return False

	@classmethod
	def get(cls, id_, **kwargs):
		try:
			return cls.objects.get(id=id_, **kwargs)
		except cls.DoesNotExist:
			return None

	@classmethod
	def create(cls, top, type_=None, parent=None, attrs=None):
		if not attrs:
			attrs = {}
		if not type_:
			type_ = cls.TYPE
		if parent:
			UserError.check(parent.topology == top, code=UserError.INVALID_CONFIGURATION,
				message="Parent must be from same topology")
		UserError.check(type_ in TYPES, code=UserError.UNSUPPORTED_TYPE, message="Unsupported type", data={"type": type_})
		el = TYPES[type_]()
		try:
			el.init(top, parent, attrs)
			el.save()
		except:
			#el.remove()
			raise
		if parent:
			parent.onChildAdded(el)
		logging.logMessage("create", category="element", id=el.idStr)
		logging.logMessage("info", category="element", id=el.idStr, info=el.info())
		return el

	@property
	def host(self):
		return self.mainElement.host if isinstance(self.mainElement, HostElement) else None

	@property
	def host_info(self):
		host = self.host
		if not host: return None
		return {
			'address': host.address,
			'problems':	host.problems(),
			'site':	host.site.name,
			'fileserver_port': host.hostInfo.get('fileserver_port', None)
		}

	@property
	def childrenIds(self):
		# Speed optimization: use existing information to avoid database accesses
		chs = getattr(self, "_childrenIds", -1)
		if chs == -1:
			chs = [ch.id for ch in self.children.only('id')]
		return map(str, chs)

	ACTIONS = {
		Entity.REMOVE_ACTION: StatefulAction(_remove, check=checkRemove)
	}
	ATTRIBUTES = {
		"id": IdAttribute(),
		"type": Attribute(field=type, readOnly=True, schema=schema.Identifier()),
		"topology": Attribute(field=topologyId, readOnly=True, schema=schema.Identifier()),
		"parent": Attribute(field=parentId, readOnly=True, schema=schema.Identifier(null=True)),
		"state": Attribute(field=state, readOnly=True, schema=schema.Identifier()),
		"children": Attribute(field=childrenIds, readOnly=True, schema=schema.List(items=schema.Identifier())),
		"connection": Attribute(field=connectionId, readOnly=True, schema=schema.Identifier(null=True)),
		"debug": Attribute(get=lambda obj: {
			"host_elements": [(o.host.name, o.num) for o in obj.hostElements],
			"host_connections": [(o.host.name, o.num) for o in obj.hostConnections],
		}, readOnly=True, schema=schema.StringMap(items={
			'host_elements': schema.List(items=schema.List(minLength=2, maxLength=2)),
			'host_connections': schema.List(items=schema.List(minLength=2, maxLength=2))
		}, required=['host_elements', 'host_connections'])),
		"host": Attribute(get=lambda self: self.host.name if self.host else None, readOnly=True),
		"host_info": Attribute(field=host_info, readOnly=True),
	}

from .. import host
from ..host.element import HostElement
from ..host import HostObject

Element.register_delete_rule(Connection, "elementFrom", DENY)
Element.register_delete_rule(Connection, "elementTo", DENY)
Element.register_delete_rule(HostObject, "topologyElement", NULLIFY)