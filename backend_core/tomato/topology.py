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

from .db import *
from .generic import *
import time
from lib import logging #@UnresolvedImport
from . import scheduler
from .lib.error import UserError #@UnresolvedImport
from .lib import util
from .lib.topology_role import Role
from .lib.remote_info import get_user_info
from .lib.service import get_backend_users_proxy
from .lib.constants import StateName, ActionName
from .lib.exceptionhandling import wrap_and_handle_current_exception

class TimeoutStep:
	INITIAL = 0
	WARNED = 9
	STOPPED = 10
	DESTROYED = 20

class Permission(ExtDocument, EmbeddedDocument):
	"""
	:type user: str
	:type role: str
	"""
	user = StringField(required=True)
	role = StringField(choices=[Role.owner, Role.manager, Role.user], required=True)


class Topology(Entity, BaseDocument):
	"""
	:type permissions: list of Permission
	:type site: Site
	:type clientData: dict
	"""
	from .host import Site
	permissions = ListField(EmbeddedDocumentField(Permission))
	timeout = FloatField(required=True)
	timeoutStep = IntField(db_field='timeout_step', required=True, default=TimeoutStep.INITIAL)
	site = ReferenceField(Site, reverse_delete_rule=NULLIFY)
	name = StringField()
	clientData = DictField(db_field='client_data')
	meta = {
		'ordering': ['name'],
		'indexes': [
			'name', ('timeout', 'timeoutStep')
		]
	}
	type = 'Topology'

	@property
	def elements(self):
		return elements.Element.objects(topology=self)

	@property
	def connections(self):
		return Connection.objects(topology=self)

	DOC = ""

	def init(self, owner, **attrs):
		"""
		:type owner: auth.User
		"""
		self.set_role(owner, Role.owner, skip_save=True)
		self.timeout = time.time() + settings.get_topology_settings()[Config.TOPOLOGY_TIMEOUT_INITIAL]
		self.timeoutStep = TimeoutStep.WARNED #not sending a warning for initial timeout
		self.save()
		self.name = "Topology [%s]" % self.idStr
		self.modify(**attrs)

	def isBusy(self):
		return hasattr(self, "_busy") and self._busy
	
	def setBusy(self, busy):
		self._busy = busy


	def checkUnknownAttribute(self, key, value):
		UserError.check(key.startswith("_"), code=UserError.UNSUPPORTED_ATTRIBUTE, message="Unsupported attribute")
		return True

	def setUnknownAttributes(self, attrs):
		for key, value in attrs.items():
			if key.startswith("_"):
				self.clientData[key[1:]] = value

	def action_prepare(self):
		self._compoundAction(action="prepare", stateFilter=lambda state: state=="created", 
							 typeOrder=["kvm","kvmqm", "openvz", "repy", "tinc_vpn", "udp_endpoint"],
							 typesExclude=["kvm_interface", "kvmqm_interface", "openvz_interface", "repy_interface", "external_network", "external_network_endpoint", "fixed_bridge", "bridge"])
	
	def action_destroy(self):
		self.action_stop()
		self._compoundAction(action="destroy", stateFilter=lambda state: state=="prepared",
							 typeOrder=["tinc_vpn", "udp_endpoint", "kvm", "kvmqm", "openvz", "repy"],
							 typesExclude=["kvm_interface", "kvmqm_interface", "openvz_interface", "repy_interface", "external_network", "external_network_endpoint", "fixed_bridge", "bridge"])
	
	def action_start(self):
		self.action_prepare()
		self._compoundAction(action="start", stateFilter=lambda state: state!="started",
							 typeOrder=["tinc_vpn", "udp_endpoint", "external_network", "kvm", "kvmqm", "openvz", "repy"],
							 typesExclude=["kvm_interface", "kvmqm_interface", "openvz_interface", "repy_interface"])
		
	
	def action_stop(self):
		self._compoundAction(action="stop", stateFilter=lambda state: state=="started", 
							 typeOrder=["kvm", "kvmqm", "openvz", "repy", "tinc_vpn", "udp_endpoint", "external_network"],
							 typesExclude=["kvm_interface", "kvmqm_interface", "openvz_interface", "repy_interface"])

	def action_renew(self, timeout):
		topology_config = settings.get_topology_settings()
		timeout = float(timeout)
		self.timeout = time.time() + timeout
		self.timeoutStep = TimeoutStep.INITIAL if timeout > topology_config[Config.TOPOLOGY_TIMEOUT_WARNING] else TimeoutStep.WARNED
		
	def _compoundAction(self, action, stateFilter, typeOrder, typesExclude):
		# execute action in order
		for type_ in typeOrder:
			for el in self.elements:
				if el.type != type_ or not stateFilter(el.state) or el.type in typesExclude:
					continue
				el.action(action)
		# execute action on rest
		for el in self.elements:
			if not stateFilter(el.state) or el.type in typesExclude or el.type in typeOrder:
				continue
			el.action(action)
		# execute action on connections
		for con in self.connections:
			if not stateFilter(con.state) or con.type in typesExclude:
				continue
			con.action(action)





	def set_role(self, username, role, skip_save=False):
		"""
		set the role of a user
		:param str username: target user
		:param str role: target role
		:param bool skip_save: skip saving of the current object
		:return: Nothing
		:rtype: NoneType
		"""
		target_permission = None
		for perm in self.permissions:
			if perm.user == username:
				target_permission = perm
				break
		if target_permission is None:
			if role == Role.null:
				return
			else:
				self.permissions.append(Permission(user=username, role=role))
				if not skip_save:
					self.save()
		else:
			if role == Role.null:
				self.permissions.remove(target_permission)
				if not skip_save:
					self.save()
			else:
				target_permission.role = role
				if not skip_save:
					self.save()


	def user_has_role(self, username, role):
		"""
		check whether the given user has at least this role
		:param str username: target user
		:param str role: target role
		:return: Whether the user has at least this role (or a more-permissions-granting one)
		:rtype: bool
		"""
		for perm in self.permissions:
			if perm.user == username:
				return Role.leq(role, perm.role)
		return False

	def organization_has_role(self, organization, role):
		"""
		check whether the given organization has at least this role.
		if true, this means that OrgaTopl* may access the topology as this role.

		:param str organization: target organization
		:param str role: target role
		:return: Whether the organization has at least this role (or a more-permissions-granting one)
		:rtype: bool
		"""
		for perm in self.permissions:
			if get_user_info(perm.user).get_organization_name() == organization:
				return Role.leq(role, perm.role)
		return False




	def checkRemove(self, recurse=True):
		UserError.check(not self.isBusy(), code=UserError.ENTITY_BUSY, message="Object is busy")
		UserError.check(recurse or self.elements.count()==0, code=UserError.NOT_EMPTY,
			message="Cannot remove topology with elements")
		UserError.check(recurse or self.connections.count()==0, code=UserError.NOT_EMPTY,
			message="Cannot remove topology with connections")
		for el in self.elements:
			el.checkRemove(recurse=recurse)
		for con in self.connections:
			con.checkRemove()

	def _remove(self, recurse=True):
		self.checkRemove(recurse)
		logging.logMessage("info", category="topology", id=self.idStr, info=self.info())
		logging.logMessage("remove", category="topology", id=self.idStr)
		if self.id:
			try:
				for con in self.connections:
					con._remove()
				for el in self.elements:
					el._remove(recurse=recurse)
				self.delete()
			except UserError:
				raise
			except:
				self._disown()

	def _disown(self):
		"""
		called when removal failed. Remove all users from topology.
		a task will regularly try to remove user-less topologies.
		:return:
		"""
		logging.logMessage("disown", category="topology", id=self.idStr, info=self.info())
		self.permissions = []
		self.save()

	def modify_site(self, val):
		if val:
			site = Site.get(val)
			UserError.check(site, code=UserError.ENTITY_DOES_NOT_EXIST, message="site does not exist", data={"site": val})
			self.site = site
		else:
			self.site = None

	def modifyRole(self, user, role):
		UserError.check(role in Role.RANKING or not role, code=UserError.INVALID_VALUE, message="Invalid role",
			data={"roles": Role.RANKING})
		logging.logMessage("permission", category="topology", id=self.idStr, user=user.name, role=role)
		self.set_role(user, role)

	def checkModify(self, attr):
		UserError.check(not self.isBusy(), code=UserError.ENTITY_BUSY, message="Object is busy")

	def checkTimeout(self):
		UserError.check(self.timeout > time.time(), code=UserError.TIMED_OUT, message="Topology has timed out")

	def checkCompoundAction(self, action, **params):
		if action in ["start", "prepare"]:
			self.checkTimeout()
		UserError.check(not self.isBusy(), code=UserError.ENTITY_BUSY, message="Object is busy")
		return True

	def sendNotification(self, role, subject, message, fromUser=None):
		user_api = get_backend_users_proxy()
		for permission in self.permissions:
			if Role.leq(role, permission.role):
				user_api.send_message(permission.user, subject, message, fromUser, ref=['topology', self.idStr])

	@property
	def maxState(self):
		states = self.elements.distinct('state')
		for state in [StateName.STARTED, StateName.PREPARED, StateName.CREATED]:
			if state in states:
				return state
		return StateName.CREATED

	def info(self, full=False):
		info = Entity.info(self)
		if full:
			# Speed optimization: use existing information to avoid database accesses
			els = self.elements
			childs = {}
			for el in els:
				if not el.parentId:
					continue
				if not el.parentId in childs:
					childs[el.parentId] = []
				chs = childs[el.parentId]
				chs.append(el.id)
			connections = {}
			for el in els:
				if not el.connectionId:
					continue
				if not el.connectionId in connections:
					connections[el.connectionId] = []
				cons = connections[el.connectionId]
				cons.append(el)
			elements = [el.info(childs.get(el.id,[])) for el in els]
			connections = [con.info(connections.get(con.id, [])) for con in self.connections]
		else:
			elements = [str(el.id) for el in self.elements.only('id')]
			connections = [str(con.id) for con in self.connections.only('id')]
		info.update(elements=elements, connections=connections)
		for key, val in self.clientData.items():
			info["_"+key] = val
		return info

	def __str__(self):
		return "%s [#%s]" % (self.name, self.id)

	def __repr__(self):
		return "Topology(%s)" % self

	ACTIONS = {
		Entity.REMOVE_ACTION: Action(_remove, check=checkRemove),
		ActionName.START: Action(action_start, check=lambda self: self.checkCompoundAction(ActionName.START), paramSchema=schema.Constant({})),
		ActionName.STOP: Action(action_stop, check=lambda self: self.checkCompoundAction(ActionName.STOP), paramSchema=schema.Constant({})),
		ActionName.PREPARE: Action(action_prepare, check=lambda self: self.checkCompoundAction(ActionName.PREPARE), paramSchema=schema.Constant({})),
		ActionName.DESTROY: Action(action_destroy, check=lambda self: self.checkCompoundAction(ActionName.DESTROY), paramSchema=schema.Constant({})),
		ActionName.RENEW: Action(action_renew, check=lambda self, timeout: self.checkCompoundAction(ActionName.RENEW),
			paramSchema=schema.StringMap(items={'timeout': schema.Number(minValue=0.0)}, required=['timeout'])),
	}
	ATTRIBUTES = {
		"id": IdAttribute(),
		"permissions": Attribute(readOnly=True, get=lambda self: {str(p.user): p.role for p in self.permissions},
			schema=schema.StringMap(additional=True)),
		"site": Attribute(get=lambda self: self.site.name if self.site else None, set=modify_site),
		"elements": Attribute(readOnly=True, schema=schema.List()),
		"connections": Attribute(readOnly=True, schema=schema.List()),
		"timeout": Attribute(field=timeout, readOnly=True, schema=schema.Number()),
		"state_max": Attribute(field=maxState, readOnly=True, schema=schema.String()),
		"name": Attribute(field=name, schema=schema.String())
	}

	@classmethod
	def get(cls, id_, **kwargs):
		try:
			return cls.objects.get(id=id_, **kwargs)
		except cls.DoesNotExist:
			return None




def get(id_, **kwargs):
	return Topology.get(id_, **kwargs)

def getAll(**kwargs):
	return list(Topology.objects.filter(**kwargs))

def create(owner, **attrs):
	top = Topology()
	top.init(owner=owner, **attrs)
	logging.logMessage("create", category="topology", id=top.idStr)
	logging.logMessage("info", category="topology", id=top.idStr, info=top.info())
	return top
	
@util.wrap_task
def timeout_task():
	topology_config = settings.get_topology_settings()
	now = time.time()
	for top in Topology.objects.filter(timeoutStep=TimeoutStep.INITIAL, timeout__lte=now+topology_config[Config.TOPOLOGY_TIMEOUT_WARNING]):
		try:
			logging.logMessage("timeout warning", category="topology", id=top.idStr)
			top.sendNotification(role=Role.owner, subject="Topology timeout warning: %s" % top, message="The topology %s will time out soon. This means that the topology will be first stopped and afterwards destroyed which will result in data loss. If you still want to use this topology, please log in and renew the topology." % top)
			top.timeoutStep = TimeoutStep.WARNED
			top.save()
		except:
			wrap_and_handle_current_exception(re_raise=False)
	for top in Topology.objects.filter(timeoutStep=TimeoutStep.WARNED, timeout__lte=now):
		try:
			logging.logMessage("timeout stop", category="topology", id=top.idStr)
			top.action_stop()
			top.sendNotification(role=Role.owner, subject="Topology stopped: %s" % top, message="The topology %s has timed out and is now stopped. Your data is safe for now. The topology will be destroyed in the future, which may result in data loss. To stop this process, please log in and renew your topology, or download your data." % top)
			top.timeoutStep = TimeoutStep.STOPPED
			top.save()
		except:
			wrap_and_handle_current_exception(re_raise=False)
	for top in Topology.objects.filter(timeoutStep=TimeoutStep.STOPPED, timeout__lte=now-topology_config[Config.TOPOLOGY_TIMEOUT_DESTROY]):
		try:
			logging.logMessage("timeout destroy", category="topology", id=top.idStr)
			top.action_destroy()
			top.timeoutStep = TimeoutStep.DESTROYED
			top.save()
		except:
			wrap_and_handle_current_exception(re_raise=False)
	for top in Topology.objects.filter(timeoutStep=TimeoutStep.DESTROYED, timeout__lte=now-topology_config[Config.TOPOLOGY_TIMEOUT_REMOVE]):
		try:
			logging.logMessage("timeout remove", category="topology", id=top.idStr)
			top.remove()
		except:
			wrap_and_handle_current_exception(re_raise=False)

scheduler.scheduleRepeated(600, timeout_task)

@util.wrap_task
def remove_disowned_topologies():
	for top in Topology.objects.filter(permissions__size=0):
		try:
			top.remove()
		except:
			wrap_and_handle_current_exception(re_raise=False)

scheduler.scheduleRepeated(3600*24, remove_disowned_topologies)

import elements
from .connections import Connection
from lib.settings import settings, Config
from .host.site import Site
