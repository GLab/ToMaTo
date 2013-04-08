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
from lib import attributes, db, logging #@UnresolvedImport
from accounting import UsageStatistics
from auth import Flags
from auth.permissions import Permissions, PermissionMixin, Role

class Topology(PermissionMixin, attributes.Mixin, models.Model):
	permissions = models.ForeignKey(Permissions, null=False)
	totalUsage = models.OneToOneField(UsageStatistics, null=True, related_name='+')
	attrs = db.JSONField()
	name = attributes.attribute("name", unicode)
	
	DOC = ""
	CAP_ACTIONS = ["prepare", "destroy", "start", "stop"]
	CAP_ATTRS = ["name"]
	
	class Meta:
		pass
	
	def init(self, owner, attrs={}):
		self.attrs = {}
		self.permissions = Permissions.objects.create()
		self.permissions.set(owner, "owner")
		self.totalUsage = UsageStatistics.objects.create()
		self.save()
		self.name = "Topology #%d" % self.id
		self.modify(attrs)

	def _saveAttributes(self):
		pass #disable automatic attribute saving

	def isBusy(self):
		return hasattr(self, "_busy") and self._busy
	
	def setBusy(self, busy):
		self._busy = busy
		
	def upcast(self):
		return self

	def checkModify(self, attrs):
		"""
		Checks whether the attribute change can succeed before changing the
		attributes.
		If checks whether the attributes are listen in CAP_ATTRS and if the
		current object state is listed in CAP_ATTRS[NAME].
		
		@param attrs: Attributes to change
		@type attrs: dict
		"""
		self.checkRole(Role.manager)
		fault.check(not self.isBusy(), "Object is busy")
		for key in attrs.keys():
			if key.startswith("_"):
				continue
			fault.check(key in self.CAP_ATTRS, "Unsupported attribute for topology: %s", key)
		
	def modify(self, attrs):
		"""
		Sets the given attributes to their given values. This method first
		checks if the change can be made using checkModify() and then executes
		the attribute changes by calling modify_KEY(VALUE) for each key/value
		pair in attrs. After calling all these modify_KEY methods, it will save
		the object.
		
		Classes inheriting from this class should only implement the modify_KEY
		methods and not touch this method.  
		
		@param attrs: Attributes to change
		@type attrs: dict
		"""		
		self.checkModify(attrs)
		logging.logMessage("modify", category="topology", id=self.id, attrs=attrs)
		self.setBusy(True)
		try:
			for key, value in attrs.iteritems():
				if key.startswith("_"):
					self.setAttribute(key, value)
				else:
					getattr(self, "modify_%s" % key)(value)
		finally:
			self.setBusy(False)
		self.save()
		logging.logMessage("info", category="topology", id=self.id, info=self.info())			
		
	
	def checkAction(self, action):
		"""
		Checks if the action can be executed. This method checks if the action
		is listed in CAP_ACTIONS and if the current state is listed in 
		CAP_ACTIONS[action].
		
		@param action: Action to check
		@type action: str
		"""
		self.checkRole(Role.manager)
		fault.check(not self.isBusy(), "Object is busy")
		fault.check(action in self.CAP_ACTIONS, "Unsupported action for topology: %s", action)
	
	def action(self, action, params):
		"""
		Executes the action with the given parameters. This method first
		checks if the action is possible using checkAction() and then executes
		the action by calling action_ACTION(**params). After calling the action
		method, it will save the object.
		
		Classes inheriting from this class should only implement the 
		action_ACTION method and not touch this method. 
		
		@param action: Name of the action
		@type action: str
		@param params: Parameters for the action
		@type params: dict
		"""
		self.checkAction(action)
		logging.logMessage("action start", category="topology", id=self.id, action=action, params=params)
		self.setBusy(True)
		try:
			res = getattr(self, "action_%s" % action)(**params)
		finally:
			self.setBusy(False)
		self.save()
		logging.logMessage("action end", category="topology", id=self.id, action=action, params=params, res=res)
		logging.logMessage("info", category="topology", id=self.id, info=self.info())			
		return res

	def action_prepare(self):
		self._compoundAction(action="prepare", stateFilter=lambda state: state=="created", 
							 typeOrder=["external_network", "kvmqm", "openvz", "repy", "tinc_vpn", "udp_endpoint"],
							 typesExclude=["kvmqm_interface", "openvz_interface", "repy_interface"])
	
	def action_destroy(self):
		self.action_stop()
		self._compoundAction(action="destroy", stateFilter=lambda state: state=="prepared",
							 typeOrder=["tinc_vpn", "udp_endpoint", "external_network", "kvmqm", "openvz", "repy"],
							 typesExclude=["kvmqm_interface", "openvz_interface", "repy_interface"])
	
	def action_start(self):
		self.action_prepare()
		self._compoundAction(action="start", stateFilter=lambda state: state!="started",
							 typeOrder=["tinc_vpn", "udp_endpoint", "external_network", "kvmqm", "openvz", "repy"],
							 typesExclude=["kvmqm_interface", "openvz_interface", "repy_interface"])
		
	
	def action_stop(self):
		self._compoundAction(action="stop", stateFilter=lambda state: state=="started", 
							 typeOrder=["kvmqm", "openvz", "repy", "tinc_vpn", "udp_endpoint", "external_network"],
							 typesExclude=["kvmqm_interface", "openvz_interface", "repy_interface"])

	def _compoundAction(self, action, stateFilter, typeOrder, typesExclude):
		# execute action in order
		for type_ in typeOrder:
			for el in self.getElements():
				if el.type != type_ or not stateFilter(el.state) or el.type in typesExclude:
					continue
				el.action(action)
		# execute action on rest
		for el in self.getElements():
			if not stateFilter(el.state) or el.type in typesExclude:
				continue
			el.action(action)

	def checkRemove(self, recurse=True):
		self.checkRole(Role.owner)
		fault.check(not self.isBusy(), "Object is busy")
		fault.check(recurse or self.elements.exists(), "Cannot remove topology with elements")
		fault.check(recurse or self.connections.exists(), "Cannot remove topology with connections")
		for el in self.getElements():
			el.checkRemove(recurse=recurse)
		for con in self.getConnections():
			con.checkRemove()

	def remove(self, recurse=True):
		self.checkRemove(recurse)
		logging.logMessage("info", category="topology", id=self.id, info=self.info())
		logging.logMessage("remove", category="topology", id=self.id)
		self.permissions.delete()
		#self.totalUsage will be deleted automatically
		self.delete()

	def getElements(self):
		return [el.upcast() for el in self.elements.all()]

	def getConnections(self):
		return [con.upcast() for con in self.connections.all()]

	def modify_name(self, val):
		self.name = val
			
	def setRole(self, user, role):
		fault.check(role in Role.RANKING or not role, "Role must be one of %s", Role.RANKING)
		self.checkRole(Role.owner)
		fault.check(user != currentUser(), "Must not set permissions for yourself")
		logging.logMessage("permission", category="topology", id=self.id, user=user.name, role=role)
		self.permissions.set(user, role)
			
	def info(self, full=False):
		if not currentUser().hasFlag(Flags.Debug):
			self.checkRole(Role.user)
		if full:
			elements = [el.info() for el in self.getElements()]
			connections = [con.info() for con in self.getConnections()]
		else:
			elements = [el.id for el in self.elements.all()]
			connections = [con.id for con in self.connections.all()]
		usage = self.totalUsage.getRecords(type="5minutes").order_by("end")
		return {
			"id": self.id,
			"attrs": self.attrs.copy(),
			"permissions": dict([(str(p.user), p.role) for p in self.permissions.entries.all()]),
			"elements": elements,
			"connections": connections,
			"usage": usage[0].info() if usage else None
		}
		
	def updateUsage(self, now):
		self.totalUsage.updateFrom(now, [el.totalUsage for el in self.getElements()]
								 + [con.totalUsage for con in self.getConnections()])


def get(id_, **kwargs):
	try:
		return Topology.objects.get(id=id_, **kwargs)
	except Topology.DoesNotExist:
		return None

def getAll(**kwargs):
	return list(Topology.objects.filter(**kwargs))

def create(attrs={}):
	fault.check(not currentUser().hasFlag(Flags.NoTopologyCreate), "User can not create new topologies")
	top = Topology()
	top.init(owner=currentUser())
	logging.logMessage("create", category="topology", id=top.id)	
	logging.logMessage("info", category="topology", id=top.id, info=top.info())	
	return top
	
from . import fault, currentUser