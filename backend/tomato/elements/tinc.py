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

import threading
import random, math
from django.db import models
from .. import elements, host
from ..lib.attributes import Attr #@UnresolvedImport
from generic import ST_CREATED, ST_PREPARED, ST_STARTED
from ..lib.error import UserError, assert_

class Tinc_VPN(elements.generic.ConnectingElement, elements.Element):
	name_attr = Attr("name", desc="Name", type="str")
	name = name_attr.attribute()
	mode_attr = Attr("mode", desc="Mode", options={"switch": "Switch (learning)", "hub": "Hub (broadcast)"}, default="switch", states=[ST_CREATED, ST_PREPARED])
	mode = mode_attr.attribute()
	
	CUSTOM_ACTIONS = {
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		"start": [ST_PREPARED],
		"stop": [ST_STARTED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CUSTOM_ATTRS = {
		"name": name_attr,
		"mode": mode_attr,
	}

	DIRECT_ATTRS = False
	DIRECT_ATTRS_EXCLUDE = []
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {}

	TYPE = "tinc_vpn"
	HOST_TYPE = None
	DIRECT_ACTIONS = False
	DIRECT_ACTIONS_EXCLUDE = []
	CAP_CHILDREN = {"tinc_endpoint": [ST_CREATED, ST_PREPARED]}
	
	class Meta:
		db_table = "tomato_tinc_vpn"
		app_label = 'tomato'

	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + str(self.id)
		self.save()
	
	def onChildAdded(self, iface):
		if self.state == ST_PREPARED: #self is correct
			iface.action("prepare", {})
			self._crossConnect()

	def onChildRemoved(self, iface):
		if iface.state == ST_PREPARED: #iface is correct
			iface.action("destroy", {})
			self._crossConnect()

	def modify_name(self, val):
		self.name = val

	def modify_mode(self, val):
		self.mode = val
		for ch in self.getChildren():
			ch.modify({"mode": self.mode})

	def _crossConnect(self):
		def _isEndpoint(obj):
			return not isinstance(obj, list)
		def _clusterByFilter(nodes, fn):
			clustered = {}
			for n in nodes:
				id_ = fn(n)
				if not id_ in clustered:
					clustered[id_] = []
				clustered[id_].append(n)
			return clustered.values()
		def _balance(nodes, max_):
			if _isEndpoint(nodes):
				return nodes
			if len(nodes) == 1:
				return _balance(nodes[0], max_)
			if len(nodes) > max_:
				clusters = []
				for i in xrange(0, max_):
					clusters.append([])
				i = 0
				while nodes:
					clusters[i].append(nodes.pop())
					i = (i+1) % max_
				nodes = _balance(clusters, max_)
			nodes = map(lambda n: _balance(n, max_), nodes)
			if sum(map(lambda n: 1 if _isEndpoint(n) else len(n), nodes)) <= max_:
				nodes = sum([[n] if _isEndpoint(n) else n for n in nodes], [])
			return nodes				
		def _cluster(nodes):
			clustered = _clusterByFilter(nodes, lambda n: n.element.host.site)
			clustered = map(lambda cluster: _clusterByFilter(cluster, lambda n: n.element.host), clustered)
			clustered = _balance(clustered, 5)
			return clustered
		def _representative(cluster):
			if _isEndpoint(cluster):
				return cluster
			return _representative(random.choice(cluster))
		def _connections(clusters):
			cons = []
			if _isEndpoint(clusters):
				return []
			for c in clusters:
				cons += _connections(c)
			for c1 in clusters:
				for c2 in clusters:
					if c2 == c1:
						if _isEndpoint(c1):	break
						else: continue
					r1 = _representative(c1)
					r2 = _representative(c2)
					cons.append((r1, r2))
					cons.append((r2, r1))
			return cons
		def _check(nodes, connections):
			assert_(len(cons)/2 <= len(nodes) * len(nodes), "Tinc clustering resulted in too many connections")
			if not nodes:
				return
			connected = set()
			connected.add(random.choice(nodes).id)
			changed = True
			iterations = 0
			while changed and len(connected) < len(nodes):
				changed = False
				for src, dst in cons:
					if src.id in connected and not dst.id in connected:
						connected.add(dst.id)
						changed = True
				iterations += 1
			assert_(len(connected) == len(nodes), "Tinc clustering resulted in disconnected nodes")
			assert_(iterations <= math.ceil(math.log(len(nodes), 5)), "Tinc clustering resulted in too many hops")
		assert self.state == ST_PREPARED
		children = self.getChildren()
		peerInfo = {}
		peers = {}
		for ch in children:
			assert ch.element
			info = ch.info()
			peerInfo[ch.id] = {
				"host": ch.element.host.address,
				"port": info["attrs"]["port"],
				"pubkey": info["attrs"]["pubkey"],
			}
			peers[ch.id] = []
		clusters = _cluster(children)
		cons = _connections(clusters)
		_check(children, cons)
		for src, dst in cons:
			peers[src.id].append(peerInfo[dst.id])
		for ch in children:
			info = ch.info()
			ch.modify({"peers": peers[ch.id]})

	def _parallelChildActions(self, childList, action, params=None, maxThreads=10):
		if not params: params = {}
		lock = threading.RLock()
		user = currentUser()
		class WorkerThread(threading.Thread):
			def run(self):
				setCurrentUser(user)
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

	def _childsByState(self):
		childs = {ST_CREATED:[], ST_PREPARED:[], ST_STARTED:[]}
		for ch in self.getChildren():
			childs[ch.state].append(ch)
		return childs

	def action_prepare(self):
		self._parallelChildActions(self._childsByState()[ST_CREATED], "prepare")
		self.setState(ST_PREPARED)
		try:
			self._crossConnect()
		except:
			self.action_destroy()
			raise
		
	def action_destroy(self):
		self._parallelChildActions(self._childsByState()[ST_STARTED], "stop")
		self._parallelChildActions(self._childsByState()[ST_PREPARED], "destroy")
		self.setState(ST_CREATED)

	def action_stop(self):
		self._parallelChildActions(self._childsByState()[ST_STARTED], "stop")
		self.setState(ST_PREPARED)

	def action_start(self):
		self._parallelChildActions(self._childsByState()[ST_CREATED], "prepare")
		self._parallelChildActions(self._childsByState()[ST_PREPARED], "start")
		self.setState(ST_STARTED)

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["mode"] = self.mode
		return info



class Tinc_Endpoint(elements.generic.ConnectingElement, elements.Element):
	element = models.ForeignKey(host.HostElement, null=True, on_delete=models.SET_NULL)
	name_attr = Attr("name", desc="Name", type="str")
	name = name_attr.attribute()
	mode_attr = Attr("mode", desc="Mode", options={"switch": "Switch (learning)", "hub": "Hub (broadcast)"}, default="switch", states=[ST_CREATED, ST_PREPARED])
	mode = mode_attr.attribute()
	peers_attr = Attr("peers", desc="Peers", default=[], states=[ST_CREATED, ST_PREPARED])
	peers = peers_attr.attribute()
	
	DIRECT_ACTIONS_EXCLUDE = ["prepare", "destroy", elements.REMOVE_ACTION]
	CUSTOM_ACTIONS = {
		"stop": [ST_STARTED],
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CUSTOM_ATTRS = {
		"name": name_attr,
		"mode": mode_attr,
		"peers": peers_attr,
	}
	DIRECT_ATTRS_EXCLUDE = ["timeout"]
	CAP_PARENT = [None, Tinc_VPN.TYPE]
	DEFAULT_ATTRS = {}

	TYPE = "tinc_endpoint"
	HOST_TYPE = "tinc"
	CAP_CHILDREN = {}
	CAP_CONNECTABLE = True
	
	SAME_HOST_AFFINITY = 1000 #we definitely want to be on the same host as our connected elements
	
	class Meta:
		db_table = "tomato_tinc_endpoint"
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

	def modify_mode(self, val):
		self.mode = val
		if self.element:
			self.element.modify({"mode": val})

	def modify_peers(self, val):
		self.peers = val
		if self.element:
			self.element.modify({"peers": val})

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
				for iface in self.getChildren():
					iface._remove()
				self.element = None
			self.save()

	def action_prepare(self):
		hPref, sPref = self.getLocationPrefs()
		_host = host.select(elementTypes=["tinc"], hostPrefs=hPref, sitePrefs=sPref)
		UserError.check(_host, code=UserError.NO_RESOURCES, message="No matching host found for element", data={"type": self.TYPE})
		attrs = self._remoteAttrs()
		attrs.update({
			"mode": self.mode,
			"peers": self.peers,
		})
		self.element = _host.createElement(self.remoteType(), parent=None, attrs=attrs, ownerElement=self)
		self.save()
		self.setState(ST_PREPARED, True)
		
	def action_destroy(self):
		if self.element:
			self.element.remove()
			self.element = None
		self.setState(ST_CREATED, True)

	def action_stop(self):
		if self.element:
			self.element.action("stop")
		self.setState(ST_PREPARED, True)
		
	def upcast(self):
		return self

	def after_start(self):
		self.triggerConnectionStart()
		
	def after_stop(self):
		self.triggerConnectionStop()

	def readyToConnect(self):
		return self.state == ST_STARTED

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["mode"] = self.mode
		info["attrs"]["peers"] = self.peers
		return info
	
elements.TYPES[Tinc_VPN.TYPE] = Tinc_VPN	
elements.TYPES[Tinc_Endpoint.TYPE] = Tinc_Endpoint

from .. import currentUser, setCurrentUser