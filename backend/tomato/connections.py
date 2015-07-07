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

import time

from .db import *
from .generic import *
from .topology import Topology
from .auth import Flags
from .auth.permissions import Permission, PermissionMixin, Role
from .lib import logging #@UnresolvedImport
from .lib.error import UserError, InternalError
from .accounting import UsageStatistics
from .lib.cache import cached #@UnresolvedImport

REMOVE_ACTION = "(remove)"

ST_CREATED = "created"
ST_STARTED = "started"

LOCKS = {}
LOCKS_LOCK = threading.RLock()

def getLock(obj):
	with LOCKS_LOCK:
		if not obj.id in LOCKS:
			LOCKS[obj.id] = threading.RLock()
		return LOCKS[obj.id]
	
def removeLock(obj):
	with LOCKS_LOCK:
		with getLock(obj):
			del LOCKS[obj.id]

starting_list = set()
starting_list_lock = threading.RLock()
stopping_list = set()
stopping_list_lock = threading.RLock()

class Connection(LockedStatefulEntity, PermissionMixin, BaseDocument):
	"""
	:type topology: Topology
	:type clientData: dict
	:type directData: dict
	:type elementFrom: elements.Element
	:type elementTo: elements.Element
	:type connectionFrom: host.HostConnection
	:type connectionTo: host.HostConnection
	:type connectionElementFrom: host.HostElement
	:type connectionElementTo: host.HostElement
	"""
	topology = ReferenceField(Topology, required=True, reverse_delete_rule=DENY)
	topologyId = ReferenceFieldId(topology)
	state = StringField(choices=['default', 'created', 'prepared', 'started'], required=True)
	permissions = ListField(EmbeddedDocumentField(Permission))
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True, reverse_delete_rule=DENY)
	elementFrom = ReferenceField('Element', db_field='element_from', required=True) #reverse_delete_rule=DENY defined at bottom of element/__init__.py
	elementFromId = ReferenceFieldId(elementFrom)
	elementTo = ReferenceField('Element', db_field='element_to', required=True) #reverse_delete_rule=DENY defined at bottom of element/__init__.py
	elementToId = ReferenceFieldId(elementTo)
	from .host.connection import HostConnection, HostElement
	connectionFrom = ReferenceField(HostConnection, db_field='connection_from', reverse_delete_rule=NULLIFY)
	connectionTo = ReferenceField(HostConnection, db_field='connection_to', reverse_delete_rule=NULLIFY)
	connectionElementFrom = ReferenceField(HostElement, db_field='connection_element_from', reverse_delete_rule=NULLIFY)
	connectionElementTo = ReferenceField(HostElement, db_field='connection_element_to', reverse_delete_rule=NULLIFY)
	clientData = DictField(db_field='client_data')
	directData = DictField(db_field='direct_data')
	meta = {
		'allow_inheritance': True,
		'indexes': [
			'topology', 'state', 'elementFrom', 'elementTo'
		]
	}

	DIRECT_ACTIONS = True
	DIRECT_ACTIONS_EXCLUDE = ["start", "stop", "prepare", "destroy", REMOVE_ACTION]
	CUSTOM_ACTIONS = {REMOVE_ACTION: [ST_CREATED]}
	
	DIRECT_ATTRS = True
	DIRECT_ATTRS_EXCLUDE = []
	CUSTOM_ATTRS = {}
	
	DEFAULT_ATTRS = {"emulation": True, "bandwidth_to": 10000, "bandwidth_from": 10000}
	
	DOC=""

	# noinspection PyMethodOverriding
	def init(self, topology, el1, el2, attrs=None):
		if not attrs: attrs = {}
		self.topology = topology
		self.permissions = topology.permissions
		self.state = ST_CREATED
		self.totalUsage = UsageStatistics.objects.create()
		self.elementFrom = el1
		self.elementTo = el2
		Entity.init(self, attrs)
		
	@classmethod
	def canConnect(cls, el1, el2):
		return el1.CAP_CONNECTABLE and el2.CAP_CONNECTABLE
		
	@property
	def mainConnection(self):
		return self.connectionFrom

	@property
	def elements(self):
		return [self.elementFrom, self.elementTo]

	@property
	def remoteType(self):
		return self.mainConnection.type if self.mainConnection else "bridge"

	def _adaptAttrs(self, attrs):
		tmp = {}
		reversed = not self._correctDirection() #@ReservedAssignment
		for key, value in attrs.iteritems():
			if reversed:
				if key.endswith("_from"):
					key = key[:-5] + "_to"
				elif key.endswith("_to"):
					key = key[:-3] + "_from"
			tmp[key] = value
		return tmp

	@property
	def _remoteAttrs(self):
		caps = getConnectionCapabilities(self.remoteType)
		allowed = caps["attributes"].keys() if caps else []
		attrs = {}
		for key, value in self.directData.iteritems():
			if key in allowed:
				attrs[key] = value
		attrs = self._adaptAttrs(attrs)
		return attrs

	def checkUnknownAttribute(self, key, value):
		self.checkRole(Role.manager)
		if key.startswith("_"):
			return True
		UserError.check(self.DIRECT_ATTRS and not key in self.DIRECT_ATTRS_EXCLUDE,
			code=UserError.UNSUPPORTED_ATTRIBUTE, message="Unsupported attribute")
		if self.mainConnection:
			allowed = self.mainConnection.getAllowedAttributes().keys()
		else:
			caps = getConnectionCapabilities(self.remoteType)
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
		if self.mainConnection:
			self.mainConnection.modify(remoteAttrs)

	def checkUnknownAction(self, action, params=None):
		self.checkRole(Role.manager)
		if action in ["prepare", "start", "upload_grant"]:
			UserError.check(not currentUser().hasFlag(Flags.OverQuota), code=UserError.DENIED, message="Over quota")
			UserError.check(self.topology.timeout > time.time(), code=UserError.TIMED_OUT, message="Topology has timed out")
		UserError.check(self.DIRECT_ACTIONS and not action in self.DIRECT_ACTIONS_EXCLUDE,
			code=UserError.UNSUPPORTED_ACTION, message="Unsupported action")
		UserError.check(self.mainConnection, code=UserError.UNSUPPORTED_ACTION, message="Unsupported action")
		if not action in self.mainConnection.getAllowedActions():
			self.mainConnection.updateInfo()
			self.state = self.mainConnection.state
			self.save()
		UserError.check(action in self.mainConnection.getAllowedActions(),
			code=UserError.UNSUPPORTED_ACTION, message="Unsupported action")
		return True

	def executeUnknownAction(self, action, params=None):
		try:
			if hasattr(self, "before_%s" % action):
				getattr(self, "before_%s" % action)(**params)
			res = self.mainConnection.action(action, params)
			self.setState(self.mainConnection.state)
			if hasattr(self, "after_%s" % action):
				getattr(self, "after_%s" % action)(**params)
		except Exception, exc:
			self.onError(exc)
			raise
		return res

	def _checkRemove(self):
		self.checkRole(Role.manager)
		return True

	def _remove(self):
		try:
			self.reload()
		except Connection.DoesNotExist:
			return
		self._checkRemove()
		logging.logMessage("info", category="topology", id=self.idStr, info=self.info())
		logging.logMessage("remove", category="topology", id=self.idStr)
		self.triggerStop()
		for el in self.elements:
			el.connection = None
			el.save()
		self.delete()
		self.totalUsage.remove()

	def setState(self, state):
		self.state = state
		self.save()

	@property
	def hostElements(self):
		return filter(bool, [self.connectionElementFrom, self.connectionElementTo])

	@property
	def hostConnections(self):
		return filter(bool, [self.connectionFrom, self.connectionTo])

	def onError(self, exc):
		pass

	def _correctDirection(self):
		"""
		Find out whether the directions are correct
		"""
		el1 = self.elementFrom.mainElement
		InternalError.check(el1, code=InternalError.INVALID_STATE,
			message="Can not check directions on unprepared element", data={"element": self.elementFrom.id})
		id1 = el1.num
		if self.connectionElementFrom:
			id2 = self.connectionElementFrom.num
		else:
			el2 = self.elementTo.mainElement
			InternalError.check(el2, code=InternalError.INVALID_STATE,
				message="Can not check directions on unprepared element", data={"element": self.elementTo.id})
			id2 = el2.num
		return id1 < id2
		
	def _start(self):
		if self.state == ST_STARTED:
			return
		el1, el2 = self.elementFrom.mainElement, self.elementTo.mainElement
		InternalError.check(el1 and el2, code=InternalError.INVALID_STATE, message="Can not connect unprepared element")
		# First create connection, then set attributes
		if el1.host == el2.host:
			# simple case: both elements are on same host
			self.connectionFrom = el1.connectWith(el2, attrs={}, ownerConnection=self)
			if self.connectionFrom.state == ST_CREATED:
				self.connectionFrom.action("start")
		else:
			# complex case: helper elements needed to connect elements on different hosts
			self.connectionElementFrom = el1.host.createElement("udp_tunnel", ownerConnection=self)
			self.connectionElementTo = el2.host.createElement("udp_tunnel", attrs={
				"connect": "%s:%d" % (el1.host.address, self.connectionElementFrom.objectInfo["attrs"]["port"])
			}, ownerConnection=self)
			self.connectionFrom = el1.connectWith(self.connectionElementFrom, attrs={}, ownerConnection=self)
			self.connectionTo = el2.connectWith(self.connectionElementTo, attrs={}, ownerConnection=self)
			if "emulation" in self.connectionTo.getAllowedAttributes():
				self.connectionTo.modify({"emulation": False})
			self.save()
			self.connectionElementFrom.action("start")
			self.connectionElementTo.action("start")
			if self.connectionFrom.state == ST_CREATED:
				self.connectionFrom.action("start")
			if self.connectionTo.state == ST_CREATED:
				self.connectionTo.action("start")
		# Find out and set allowed attributes
		allowed = self.connectionFrom.getAllowedAttributes()
		attrs = dict(filter(lambda (k, v): k in allowed, self._remoteAttrs.items()))
		self.connectionFrom.modify(attrs)
		# Unset all disallowed attributes
		for key in self._remoteAttrs.keys():
			if not key in allowed:
				del self._remoteAttrs[key]
		self.setState(ST_STARTED)
			
	def _stop(self):
		if self.connectionFrom:
			if self.connectionFrom.state == ST_STARTED:
				self.connectionFrom.action("stop")
			self.connectionFrom.remove()
			self.connectionFrom = None
			self.save()
		if self.connectionTo:
			if self.connectionTo.state == ST_STARTED:
				self.connectionTo.action("stop")
			self.connectionTo.remove()
			self.connectionTo = None
			self.save()
		if self.connectionElementFrom:
			if self.connectionElementFrom.state == ST_STARTED:
				self.connectionElementFrom.action("stop")
			self.connectionElementFrom.remove()
			self.connectionElementFrom = None
			self.save()
		if self.connectionElementTo:
			if self.connectionElementTo.state == ST_STARTED:
				self.connectionElementTo.action("stop")
			self.connectionElementTo.remove()
			self.connectionElementTo = None
			self.save()
		self.setState(ST_CREATED)

	def triggerStart(self):
		for el in self.elements:
			if not el.readyToConnect:
				return
		# This is very important
		# To avoid race conditions where two elements are started at the same time and then trigger
		# the connection start at the same time, a lock is used to guarantee that only one instance
		# of _start runs at the same time.
		# To avoid the case that the second element uses old connection data and runs _start again,
		# the object is fetched freshly from the database.
		with starting_list_lock:
			if self in starting_list:
				return
			starting_list.add(self)
		try: 
			with getLock(self):
				obj = Connection.objects.get(id=self.id)
				obj._start()
		finally:
			with starting_list_lock:
				starting_list.remove(self)
		
	def triggerStop(self):
		# This is very important, see the comment on triggerStart 
		with stopping_list_lock:
			if self in stopping_list:
				return
			stopping_list.add(self)
		try: 
			with getLock(self):
				try:
					obj = Connection.objects.get(id=self.id)
					obj._stop()
				except Connection.DoesNotExist:
					# Other end of connection deleted the connection, no need to stop it
					pass
		finally:
			with stopping_list_lock:
				stopping_list.remove(self)

	@classmethod
	@cached(timeout=3600, maxSize=None)
	def getCapabilities(cls, type_, host_):
		caps = cls.capabilities()
		if not host_ and (cls.DIRECT_ACTIONS or cls.DIRECT_ATTRS):
			host_ = select(connectionTypes=[type_])
		if cls.DIRECT_ATTRS or cls.DIRECT_ACTIONS:
			host_cap = host_.getConnectionCapabilities(type_)
		if cls.DIRECT_ACTIONS:
			# noinspection PyUnboundLocalVariable
			for action, params in host_cap["actions"].iteritems():
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
				if not attr in cls.DIRECT_ATTRS_EXCLUDE:
					caps["attributes"][attr] = params
		return caps

	@property
	def type(self):
		if self.mainConnection:
			return self.mainConnection.type
		# Speed optimization: use existing information to avoid database accesses
		els = getattr(self, "_elementsHint", -1)
		if els == -1:
			els = self.elements
		for el in els:
			if el.type == "external_network_endpoint":
				return "fixed_bridge"
		return "bridge"
			
	def fetchInfo(self):
		mcon = self.mainConnection
		if mcon:
			mcon.updateInfo()
			
	def info(self, elementsHint=None):
		# Speed optimization: use existing information to avoid database accesses
		if not elementsHint is None:
			self._elementsHint = elementsHint
		if not (currentUser() is True or currentUser().hasFlag(Flags.Debug)):
			self.checkRole(Role.user)
		mcon = self.mainConnection
		if isinstance(mcon, HostConnection):
			info = mcon.objectInfo.get("attrs", {})
		else:
			info = {}
		if self.directData:
			info.update(self.directData)
		info.update(LockedStatefulEntity.info(self))
		for key, val in self.clientData.items():
			info["_"+key] = val
		return info

	@property
	def host(self):
		return self.mainConnection.host if self.mainConnection else None

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

	ACTIONS = {
		Entity.REMOVE_ACTION: StatefulAction(_remove, check=_checkRemove)
	}
	ATTRIBUTES = {
		"id": IdAttribute(),
		"type": Attribute(field=type, readOnly=True, schema=schema.Identifier()),
		"topology": Attribute(field=topologyId, readOnly=True, schema=schema.Identifier()),
		"state": Attribute(field=state, readOnly=True, schema=schema.Identifier()),
		"elements": Attribute(get=lambda obj: [obj.elementFromId, obj.elementToId], readOnly=True, schema=schema.List(items=schema.Identifier())),
		"debug": Attribute(get=lambda obj: {
			"host_elements": [(o.host.name, o.num) for o in obj.hostElements],
			"host_connections": [(o.host.name, o.num) for o in obj.hostConnections],
		}, readOnly=True, schema=schema.StringMap(items={
			'host_elements': schema.List(items=schema.List(minLength=2, maxLength=2)),
			'host_connections': schema.List(items=schema.List(minLength=2, maxLength=2))
		}, required=['host_elements', 'host_connections'])),
		"host": Attribute(get=lambda self: self.host.name if self.host else None, readOnly=True),
		"host_info": Attribute(field=host_info, readOnly=True)
	}
		
	def updateUsage(self):
		self.totalUsage.updateFrom([el.usageStatistics for el in self.hostElements]
								 + [con.usageStatistics for con in self.hostConnections])
		

	@classmethod
	def get(cls, id_, **kwargs):
		try:
			return cls.objects.get(id=id_, **kwargs)
		except Connection.DoesNotExist:
			return None

	@classmethod
	def create(cls, el1, el2, attrs=None):
		if not attrs: attrs = {}
		UserError.check(el1 != el2, code=UserError.INVALID_CONFIGURATION, message="Cannot connect element with itself")
		UserError.check(not el1.connection, code=UserError.ALREADY_CONNECTED, message="Element is already connected",
			data={"element": el1.id})
		UserError.check(not el2.connection, code=UserError.ALREADY_CONNECTED, message="Element is already connected",
			data={"element": el2.id})
		UserError.check(el1.CAP_CONNECTABLE, code=UserError.INVALID_VALUE, message="Element can not be connected",
			data={"element": el1.id})
		UserError.check(el2.CAP_CONNECTABLE, code=UserError.INVALID_VALUE, message="Element can not be connected",
			data={"element": el2.id})
		UserError.check(el1.topology == el2.topology, code=UserError.INVALID_VALUE,
			message="Can only connect elements from same topology")
		el1.topology.checkRole(Role.manager)
		con = cls()
		con.init(el1.topology, el1, el2, attrs)
		con.save()
		el1.connection = con
		el1.save()
		el2.connection = con
		el2.save()
		con.triggerStart()
		logging.logMessage("create", category="connection", id=con.idStr)
		logging.logMessage("info", category="connection", id=con.idStr, info=con.info())
		return con

from . import currentUser
from .host import getConnectionCapabilities, select
from .host.connection import HostConnection