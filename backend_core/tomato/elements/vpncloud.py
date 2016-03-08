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

import random
from ..db import *
from ..generic import *
from . import Element
from .. import elements, host
from ..host.element import HostElement
from .generic import ConnectingElement
from .generic import ST_CREATED, ST_PREPARED, ST_STARTED
from ..lib.error import UserError
from ..lib.constants import Action, Type

class VpnCloud(ConnectingElement, Element):
	name = StringField()
	network_id = LongField()

	DIRECT_ATTRS = False
	DIRECT_ATTRS_EXCLUDE = []
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {}

	TYPE = Type.VPNCLOUD
	HOST_TYPE = None
	DIRECT_ACTIONS = False
	DIRECT_ACTIONS_EXCLUDE = []
	CAP_CHILDREN = {Type.VPNCLOUD_ENDPOINT: [ST_CREATED, ST_PREPARED]}
	
	def init(self, *args, **kwargs):
		self.state = ST_CREATED
		Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + self.idStr
		self.network_id = random.randint(0, 2**63)
		self.save()
	
	def onChildAdded(self, iface):
		if self.state == ST_PREPARED: #self is correct
			iface.action(Action.PREPARE, {})
			self._crossConnect()

	def onChildRemoved(self, iface):
		if iface.state == ST_PREPARED: #iface is correct
			iface.action(Action.DESTROY, {})
			self._crossConnect()

	def _crossConnect(self):
		common_peers = []
		for ch in self.children[:3]:
			assert isinstance(ch, VpnCloudEndpoint)
			assert ch.element
			addr = "%s:%d" % (ch.element.host.address, ch.element.getAttrs()['port'])
			common_peers.append(addr)
		for ch in self.children:
			assert isinstance(ch, VpnCloudEndpoint)
			assert ch.element
			addr = "%s:%d" % (ch.element.host.address, ch.element.getAttrs()['port'])
			ch.modify({"peers": filter(lambda p: p!=addr, common_peers)})

	def _parallelChildActions(self, childList, action, params=None, maxThreads=10):
		if not params: params = {}
		lock = threading.RLock()
		class WorkerThread(threading.Thread):
			def run(self):
				while True:
					with lock:
						if not childList:
							return
						ch = childList.pop()
					ch.action(action, params)
		threads = []
		for _ in xrange(0, min(len(childList), maxThreads)):
			thread = WorkerThread()
			threads.append(thread)
			thread.start()
		for thread in threads:
			thread.join()

	@property
	def _childsByState(self):
		childs = {ST_CREATED:[], ST_PREPARED:[], ST_STARTED:[]}
		for ch in self.children:
			childs[ch.state].append(ch)
		return childs

	def action_prepare(self):
		self._parallelChildActions(self._childsByState[ST_CREATED], Action.PREPARE)
		self.setState(ST_PREPARED)
		try:
			self._crossConnect()
		except:
			self.action_destroy()
			raise
		
	def action_destroy(self):
		self._parallelChildActions(self._childsByState[ST_STARTED], Action.STOP)
		self._parallelChildActions(self._childsByState[ST_PREPARED], Action.DESTROY)
		self.setState(ST_CREATED)

	def action_stop(self):
		self._parallelChildActions(self._childsByState[ST_STARTED], Action.STOP)
		self.setState(ST_PREPARED)

	def action_start(self):
		self._parallelChildActions(self._childsByState[ST_CREATED], Action.PREPARE)
		self._parallelChildActions(self._childsByState[ST_PREPARED], Action.START)
		self.setState(ST_STARTED)

	def _nextName(self, baseName):
		num = 0
		names = [ch.name for ch in self.children]
		while baseName + str(num) in names:
			num += 1
		return baseName + str(num)

	ATTRIBUTES = Element.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"name": Attribute(field=name, label="Name"),
	})

	ACTIONS = Element.ACTIONS.copy()
	ACTIONS.update({
		Entity.REMOVE_ACTION: StatefulAction(Element._remove, check=Element.checkRemove, allowedStates=[ST_CREATED]),
		Action.START: StatefulAction(action_start, allowedStates=[ST_PREPARED], stateChange=ST_STARTED),
		Action.STOP: StatefulAction(action_stop, allowedStates=[ST_STARTED], stateChange=ST_PREPARED),
		Action.PREPARE: StatefulAction(action_prepare, allowedStates=[ST_CREATED], stateChange=ST_PREPARED),
		Action.DESTROY: StatefulAction(action_destroy, allowedStates=[ST_PREPARED], stateChange=ST_CREATED),
	})


class VpnCloudEndpoint(ConnectingElement, Element):
	"""
	:type element: HostElement
	"""

	element = ReferenceField(HostElement, reverse_delete_rule=NULLIFY)
	name = StringField()

	DIRECT_ACTIONS_EXCLUDE = [Action.PREPARE, Action.DESTROY]
	DIRECT_ATTRS_EXCLUDE = ["timeout", "network_id"]
	CAP_PARENT = [None, VpnCloud.TYPE]
	DEFAULT_ATTRS = {}

	TYPE = Type.VPNCLOUD_ENDPOINT
	HOST_TYPE = Type.VPNCLOUD
	CAP_CHILDREN = {}
	CAP_CONNECTABLE = True
	
	SAME_HOST_AFFINITY = 1000 #we definitely want to be on the same host as our connected elements
	
	def init(self, *args, **kwargs):
		self.state = ST_CREATED
		Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.parent._nextName("port")
		self.save()
	
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
				else:
					raise
			self.setState(self.element.state, True)
			if self.state == ST_CREATED:
				if self.element:
					self.element.remove()
				self.element = None
			self.save()

	def action_prepare(self):
		hPref, sPref = self.getLocationPrefs()
		_host = host.select(elementTypes=[self.HOST_TYPE], hostPrefs=hPref, sitePrefs=sPref)
		UserError.check(_host, code=UserError.NO_RESOURCES, message="No matching host found for element", data={"type": self.TYPE})
		attrs = self._remoteAttrs
		attrs.update(network_id=self.parent.network_id)
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
		"name": Attribute(field=name, label="Name")
	})

	ACTIONS = Element.ACTIONS.copy()
	ACTIONS.update({
		Entity.REMOVE_ACTION: StatefulAction(Element._remove, check=Element.checkRemove, allowedStates=[ST_CREATED]),
		Action.STOP: StatefulAction(action_stop, allowedStates=[ST_STARTED], stateChange=ST_PREPARED),
		Action.PREPARE: StatefulAction(action_prepare, allowedStates=[ST_CREATED], stateChange=ST_PREPARED),
		Action.DESTROY: StatefulAction(action_destroy, allowedStates=[ST_PREPARED], stateChange=ST_CREATED),
	})



elements.TYPES[VpnCloud.TYPE] = VpnCloud
elements.TYPES[VpnCloudEndpoint.TYPE] = VpnCloudEndpoint
