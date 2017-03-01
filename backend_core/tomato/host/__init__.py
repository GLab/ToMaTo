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
import traceback, threading

from .. import starttime, scheduler
from ..db import *
from ..generic import *
from ..lib import rpc, util, logging, error
from ..lib.cache import cached
from ..lib.error import TransportError, InternalError, UserError, Error
from ..lib.exceptionhandling import wrap_and_handle_current_exception, deprecated
from ..lib.service import get_backend_users_proxy, get_backend_accounting_proxy
from ..lib.settings import settings, Config
from ..lib.userflags import Flags
from ..lib.constants import TechName, TypeName, TypeTechTrans
from ..lib.references import Reference


element_caps = {}
connection_caps = {}

class RemoteWrapper:
	def __init__(self, url, host, *args, **kwargs):
		self._url = url
		self._host = host
		self._args = args
		self._kwargs = kwargs
		self._proxy = None

	def __repr__(self):
		return "RemoteWrapper(host=%s, url=%s)" % (self._host, self._url)

	def __str__(self):
		return "RemoteWrapper(host=%s, url=%s)" % (self._host, self._url)

	def __getattr__(self, name):
		def call(*args, **kwargs):
			retries = 3
			while True:
				retries -= 1
				try:
					if not self._proxy or not rpc.isReusable(self._proxy):
						self._proxy = rpc.createProxy(self._url, *self._args, **self._kwargs)
					return getattr(self._proxy, name)(*args, **kwargs)
				except Error as err:
					if isinstance(err, TransportError):
						err.todump = False
						self._proxy = None
						if retries >= 0:
							print >>sys.stderr, "Retrying after error on %s: %s, retries left: %d" % (self._host, err, retries)
							continue
						if not err.data:
							err.data = {}
						err.data["host"] = self._host
					raise err, None, sys.exc_info()[2]
				except Exception as exc:
					print >>sys.stderr, "Warning: received unwrapped error:"
					import traceback
					traceback.print_exc()
					raise InternalError(code=InternalError.UNKNOWN, message=repr(exc), module="hostmanager",
							data={"host": self._host}), None, sys.exc_info()[2]
		return call


_caching = True
_proxies = {}


def stopCaching():
	global _proxies
	_proxies = {}
	global _caching
	_caching = False

class Host(Entity, BaseDocument):
	"""
	:type site: tomato.host.site.Site
	"""
	name = StringField(required=True, unique=True)
	address = StringField(required=True)
	rpcurl = StringField(required=True, unique=True)
	from .site import Site
	site = ReferenceField(Site, required=True, reverse_delete_rule=DENY)
	elementTypes = ListField(db_field='element_types')
	connectionTypes = ListField(db_field='connection_types')
	hostInfo = DictField(db_field='host_info')
	hostInfoTimestamp = FloatField(db_field='host_info_timestamp', required=True)
	accountingTimestamp = FloatField(db_field='accounting_timestamp', required=True)
	lastResourcesSync = FloatField(db_field='last_resource_sync', required=True)
	enabled = BooleanField(default=True)
	componentErrors = IntField(default=0, db_field='component_errors')
	problemAge = FloatField(db_field='problem_age')
	problemMailTime = FloatField(db_field='problem_mail_time')
	availability = FloatField(default=1.0)
	description = StringField()
	hostNetworks = ListField(db_field='host_networks')
	meta = {
		'ordering': ['site', 'name'],
		'indexes': [
			'name', 'site'
		]
	}

	@property
	def elements(self):
		from .element import HostElement
		return HostElement.objects(host=self)

	@property
	def connections(self):
		from .connection import HostConnection
		return HostConnection.objects(host=self)

	@property
	def networks(self):
		from ..resources.network import NetworkInstance
		return NetworkInstance.objects(host=self)


	def action_forced_update(self):
		self.update()
		self.synchronizeResources(True)
		return self.info()

	ACTIONS = {"forced_update": Action(fn=action_forced_update)}
	ATTRIBUTES = {
		"name": Attribute(field=name, schema=schema.Identifier()),
		"address": Attribute(field=address, schema=schema.String(regex="\d+\.\d+.\d+.\d+")),
		"rpcurl": Attribute(field=rpcurl, schema=schema.String(regex="[a-zA-Z0-9+_-]+://[a-zA-Z0-9._-]+:\d+")),
		"site": Attribute(
			check=lambda obj, val: Site.get(val),
			set=lambda obj, val: setattr(obj, "site", Site.get(val)),
			get=lambda obj: obj.site.name,
			schema=schema.Identifier()
		),
		"enabled": Attribute(field=enabled, schema=schema.Bool()),
		"description": Attribute(field=description, schema=schema.String(null=True)),
		"organization": Attribute(readOnly=True, get=lambda obj: obj.site.organization, schema=schema.Identifier()),
		"problems": Attribute(readOnly=True, get=lambda obj: obj.problems(), schema=schema.List(items=schema.String())),
		"component_errors": Attribute(field=componentErrors, readOnly=True, schema=schema.Int()),
		"load": Attribute(readOnly=True, get=lambda obj: obj.getLoad(), schema=schema.List(items=schema.Number())),
		"element_types": Attribute(field=elementTypes, readOnly=True, schema=schema.List(items=schema.Identifier())),
		"connection_types": Attribute(field=connectionTypes, readOnly=True, schema=schema.List(items=schema.Identifier())),
		"host_info": Attribute(field=hostInfo, readOnly=True, schema=schema.StringMap(additional=True)),
		"host_info_timestamp": Attribute(field=hostInfoTimestamp, readOnly=True, schema=schema.Number()),
		"availability": Attribute(field=availability, readOnly=True, schema=schema.Number()),
		"networks": Attribute(field=hostNetworks, readOnly=True, schema=schema.List())
	}

	def init(self, **attrs):
		self.hostInfoTimestamp = 0
		self.accountingTimestamp = 0
		self.lastResourcesSync = 0
		if attrs:
			self.modify(**attrs)
		self.update()
		self.synchronizeResources()

	def save_if_exists(self):
		try:
			Host.objects.get(id=self.id)
		except Host.DoesNotExist:
			return
		self.save()

	def getProxy(self, always_try=False):
		if not self.is_reachable() and not always_try:
			raise TransportError(code=TransportError.CONNECT, message="host is unreachable", module="backend", data={"host": self.name}, todump=False)
		if not _caching:
			return RemoteWrapper(self.rpcurl, self.name, sslcert=settings.get_ssl_cert_filename(), sslkey=settings.get_ssl_key_filename(), sslca=settings.get_ssl_ca_filename(), timeout=settings.get_rpc_timeout())
		# locking doesn't matter here, since in case of a race condition, there would only be a second proxy for a small amount of time.
		if not self.rpcurl in _proxies:
			_proxies[self.rpcurl] = RemoteWrapper(self.rpcurl, self.name, sslcert=settings.get_ssl_cert_filename(), sslkey=settings.get_ssl_key_filename(), sslca=settings.get_ssl_ca_filename(), timeout=settings.get_rpc_timeout())
		return _proxies[self.rpcurl]

	def incrementErrors(self):
		# count all component errors {element|connection}_{create|action|modify}
		# this value is reset on every sync
		logging.logMessage("component error", category="host", host=self.name)
		self.componentErrors += 1
		self.save_if_exists()

	def update(self):
		self.availability *= settings.get_host_connections_settings()[Config.HOST_AVAILABILITY_FACTOR]
		self.save_if_exists()
		if not self.enabled:
			return
		before = time.time()
		self.hostInfo = self.getProxy(True).host_info()
		after = time.time()
		self.hostInfoTimestamp = (before + after) / 2.0
		self.hostInfo["query_time"] = after - before
		self.hostInfo["time_diff"] = self.hostInfo["time"] - self.hostInfoTimestamp
		try:
			self.hostNetworks = self.getProxy().host_networks()
		except:
			self.hostNetworks = []
		hostCapabilities = self.getProxy().host_capabilities()
		caps = self._convertCapabilities(hostCapabilities)
		self.elementTypes = caps["elements"].keys()
		global element_caps
		for k, v in caps["elements"].iteritems():
			if not k in element_caps:
				element_caps[k] = v
			else:
				if len(repr(element_caps[k])) < len(repr(v)):
					element_caps[k] = v
		self.connectionTypes = caps["connections"].keys()
		global connection_caps
		for k, v in caps["connections"].iteritems():
			if not k in connection_caps:
				connection_caps[k] = v
			else:
				if len(repr(connection_caps[k])) < len(repr(v)):
					connection_caps[k] = v
		self.componentErrors = max(0, self.componentErrors / 2)
		if not self.problems():
			self.availability += 1.0 - settings.get_host_connections_settings()[Config.HOST_AVAILABILITY_FACTOR]
		self.save_if_exists()
		logging.logMessage("info", category="host", name=self.name, info=self.hostInfo)
		logging.logMessage("capabilities", category="host", name=self.name, capabilities=caps)

	def _convertCapabilities(self, caps):
		def convertActions(actions, next_state):
			res = {}
			for action, states in actions.items():
				if type(states) == type(dict()):
					res[action] = StatefulAction(None, allowedStates=states['allowed_states'], stateChange=states['state_change']).info()
				else:
					res[action] = StatefulAction(None, allowedStates=states, stateChange=next_state.get(action)).info()
			return res
		def convertAttributes(attrs):
			res = {}
			for attr, desc in attrs.items():
				options = desc.get('options', {})
				optionsDesc = []
				if isinstance(options, dict):
					optionsDesc = [options[k] for k in options.keys()]
					options = options.keys()
				params = {
					"options": options, "optionsDesc": optionsDesc,
					"minValue": desc.get('minvalue'), "maxValue": desc.get('maxvalue'),
					"null": desc.get('null', True)
				}
				if not desc.get('unit') is None:
					params['unit'] = desc.get('unit')
				if desc.get('type') == "int":
					sch = schema.Int(**params)
				elif desc.get('type') == "float":
					sch = schema.Number(**params)
				elif desc.get('type') == "str":
					sch = schema.String(regex=desc.get("regexp"), **params)
				elif desc.get('type') == "bool":
					sch = schema.Bool(**params)
				else:
					sch = schema.Any(**params)
				res[attr] = StatefulAttribute(writableStates=desc.get('states'), readOnly=desc.get('read_only'), label=desc.get('desc'), schema=sch, default=desc.get('default')).info()
			return res
		elems = {}
		for name, info in caps['elements'].items():
			attributes = info.get('attrs')
			if not attributes and attributes != {}:
				attributes = info.get('attributes')
			elems[name] = {
				"actions": convertActions(info.get('actions'), info.get('next_state')),
				"attributes": convertAttributes(attributes),
				"children": {n: {"allowed_states": states} for n, states in info.get('children').items()},
				"parent": info.get('parent'),
				"connectability": [{"concept": n, "allowed_states": None} for n in info.get('con_concepts')]
			}
		cons = {}

		for name, info in caps['connections'].items():
			attributes = info.get('attrs')
			if not attributes and attributes != {}:
				attributes = info.get('attributes')
			cons[name] = {
				"actions": convertActions(info.get('actions'), info.get('next_state')),
				"attributes": convertAttributes(attributes),
				"connectability": [{"concept_from": names[0], "concept_to": names[1]} for names in
								   info.get('con_concepts')]
			}
		return {
			"elements": elems,
			"connections": cons,
			"resources": caps.get('resources')
		}

	def _info(self):
		return self.getProxy().host_info()

	@classmethod
	def getElementCapabilities(self, type_):
		#fixme: proper calculation of capabilities

		#fixme: proper calculation of full/container capabilities, not this:
		if type_ == TypeName.FULL_VIRTUALIZATION:
			type_ = TechName.KVMQM
		elif type_ == TypeName.CONTAINER_VIRTUALIZATION:
			type_ = TechName.OPENVZ
		elif type_ == TypeName.FULL_VIRTUALIZATION_INTERFACE:
			type_ = TechName.KVMQM_INTERFACE
		elif type_ == TypeName.CONTAINER_VIRTUALIZATION_INTERFACE:
			type_ = TechName.OPENVZ_INTERFACE

		global element_caps
		return element_caps.get(type_)

	@classmethod
	def getConnectionCapabilities(self, type_):
		#fixme: proper calculation of capabilities
		global connection_caps
		return connection_caps.get(type_)

	def createElement(self, type_, parent=None, attrs=None, ownerElement=None, ownerConnection=None):
		if not attrs:
			attrs = {}
		assert not parent or parent.host == self
		try:
			el = self.getProxy().element_create(type_, parent.num if parent else None, attrs)
		except error.Error:
			self.incrementErrors()
			raise
		from .element import HostElement
		hel = HostElement(type=el["type"], state=el["state"], host=self, num=el["id"], topologyElement=ownerElement, topologyConnection=ownerConnection)
		hel.objectInfo = el
		#Workaround
		hel["num"] = str(hel["num"])
		hel.save()
		if ownerElement:
			ownerElement.hostElements.append(hel)
			ownerElement.save()
		if ownerConnection:
			ownerConnection.hostElements.append(hel)
			ownerConnection.save()
		logging.logMessage("element_create", category="host", host=self.name, element=el,
						   ownerElement=(
							   ownerElement.__class__.__name__.lower(), ownerElement.idStr) if ownerElement else None,
						   ownerConnection=(
							   ownerConnection.__class__.__name__.lower(),
							   ownerConnection.idStr) if ownerConnection else None)
		return hel

	def getElement(self, num):
		return self.elements.get(num=num)

	def createConnection(self, hel1, hel2, type_=None, attrs=None, ownerElement=None, ownerConnection=None):
		"""
		:type ownerElement: elements.Element
		:type ownerConnection: backend.tomato.connections.Connection
		"""
		if not attrs:
			attrs = {}
		assert hel1.host == self
		assert hel2.host == self
		try:
			con = self.getProxy().connection_create(hel1.num, hel2.num, type_, attrs)
		except error.Error:
			self.incrementErrors()
			raise
		from .connection import HostConnection
		hcon = HostConnection(host=self, num=con["id"], topologyElement=ownerElement,
							  topologyConnection=ownerConnection, state=con["state"], type=con["type"],
							  elementFrom=hel1, elementTo=hel2)
		hcon.objectInfo = con
		hcon.save()
		hel1.connection = hcon
		hel1.save()
		hel2.connection = hcon
		hel2.save()
		if ownerElement:
			ownerElement.hostConnections.append(hcon)
			ownerElement.save()
		if ownerConnection:
			ownerConnection.hostConnections.append(hcon)
			ownerConnection.save()
		logging.logMessage("connection_create", category="host", host=self.name, element=con,
						   ownerElement=(
							   ownerElement.__class__.__name__.lower(), ownerElement.idStr) if ownerElement else None,
						   ownerConnection=(
							   ownerConnection.__class__.__name__.lower(),
							   ownerConnection.idStr) if ownerConnection else None)
		return hcon

	def getConnection(self, num):
		return self.connections.get(num=num)

	def grantUrl(self, grant, action):
		return "http://%s:%d/%s/%s" % (self.address, self.hostInfo["fileserver_port"], grant, action)


	def synchronizeResources(self, forced=False):
		if time.time() - self.lastResourcesSync < settings.get_host_connections_settings()[Config.HOST_RESOURCE_SYNC_INTERVAL] and not forced:
			return
		if not self.enabled:
			return

		logging.logMessage("resource_sync begin", category="host", name=self.name)
		# TODO: implement for other resources
		from ..resources import template

		hostNets = {}
		for net in self.getProxy().resource_list("network"):
			hostNets[net["attrs"]["bridge"]] = net
		for net in self.networks.all():
			key = net.bridge
			attrs = {"bridge": net.bridge, "kind": net.getKind(), "preference": net.network.preference}
			if not key in hostNets:
				# create resource
				self.getProxy().resource_create("network", attrs)
				logging.logMessage("network create", category="host", name=self.name, network=attrs)
			else:
				hNet = hostNets[key]
				if hNet["attrs"] != attrs:
					# update resource
					self.getProxy().resource_modify(hNet["id"], attrs)
					logging.logMessage("network update", category="host", name=self.name, network=attrs)
		tpls = {}
		for tpl in self.getProxy().resource_list("template"):
			tpls[(tpl["attrs"]["tech"], tpl["attrs"]["name"])] = tpl
		avail = []
		for tpl in template.Template.objects():
			type_ = tpl.type
			attrs_base = tpl.info_for_hosts()
			# for multitech element types: inflate
			for tech in TypeTechTrans.TECH_DICT.get(type_, type_):
				if tech in self.elementTypes:
					attrs = attrs_base.copy()
					attrs["tech"] = tech
					if not (attrs["tech"], attrs["name"]) in tpls:
						# create resource
						self.getProxy().resource_create("template", attrs)

						logging.logMessage("template create", category="host", name=self.name, template=attrs)
					else:
						hTpl = tpls[(attrs["tech"], attrs["name"])]
						if hTpl["attrs"].get("checksum") != tpl.checksum:
							self.getProxy().resource_modify(hTpl["id"], attrs)
							logging.logMessage("template update", category="host", name=self.name, template=attrs)
						else:
							avail.append(tpl)
		for tpl in template.Template.objects():
			tpl.update_host_state(self, tpl in avail)
		logging.logMessage("resource_sync end", category="host", name=self.name)
		self.lastResourcesSync = time.time()
		self.save_if_exists()

	def updateAccountingData(self):
		logging.logMessage("accounting_sync begin", category="host", name=self.name)
		try:
			orig_data = self.getProxy().accounting_statistics(type="single", after=self.accountingTimestamp)
			data = {"elements": {}, "connections": {}}
			max_timestamp = self.accountingTimestamp

			# check for completeness
			for el in self.elements.all():
				if not str(el.num) in orig_data["elements"]:
					print >>sys.stderr, "Missing accounting data for element #%s on host %s" % (str(el.num), self.name)
			for con in self.connections.all():
				if not str(con.num) in orig_data["connections"]:
					print >>sys.stderr, "Missing accounting data for connection #%s on host %s" % (str(con.num), self.name)
					continue

			# transform
			for type_ in ("elements", "connections"):
				for obj_id, obj_recs in orig_data[type_].iteritems():
					id_ = "%s@%s" % (obj_id, self.name)
					for obj_rec in obj_recs:
						new_rec = (int(obj_rec["begin"]), obj_rec["usage"]["memory"], obj_rec["usage"]["diskspace"], obj_rec["usage"]["traffic"], obj_rec["usage"]["cputime"])
						max_timestamp = max(obj_rec["begin"], max_timestamp)
						if obj_id in data[type_]:
							data[type_][id_].append(new_rec)
						else:
							data[type_][id_] = [new_rec]

			get_backend_accounting_proxy().push_usage(data["elements"], data["connections"])
			self.accountingTimestamp = max_timestamp + 1  # one second greater than last record.
			self.save_if_exists()
		finally:
			logging.logMessage("accounting_sync end", category="host", name=self.name)

	def getNetworkKinds(self):
		nets = [net.getKind() for net in self.networks.all()]
		for net in nets:
			if "/" in net:
				kind, _ = net.split("/", 1)
				nets.append(kind)
		if nets:
			nets.append(None)
		return nets

	def getTopologyElements(self):
		from elements import Element

		return (el.upcast() for el in Element.objects.filter(host_elements__host=self))

	def getUsers(self):
		res = []
		for type_, obj in [("element", el) for el in self.elements.all()] + [("connection", con) for con in
																			 self.connections.all()]:
			data = {"type": type_, "onhost_id": obj.num, "element_id": None, "connection_id": None, "topology_id": None,
					"state": obj.state}
			if obj.topologyElement:
				tel = obj.topologyElement
				data["element_id"] = tel.idStr
				data["topology_id"] = tel.topologyId
			if obj.topologyConnection:
				tcon = obj.topologyConnection
				data["connection_id"] = tcon.idStr
				data["topology_id"] = tcon.topologyId
			res.append(data)
		return res

	def remove(self, params=None):
		if self.id:
			UserError.check(not self.elements.all(), code=UserError.NOT_EMPTY, message="Host still has active elements")
			UserError.check(not self.connections.all(), code=UserError.NOT_EMPTY, message="Host still has active connections")
		logging.logMessage("remove", category="host", name=self.name)
		if self.id:
			try:
				for res in self.getProxy().resource_list():
					self.getProxy().resource_remove(res["id"])
			except:
				pass
		from ..resources.template import Template
		for t in Template.objects():
			if self.name in t.hosts:
				t.hosts.remove(self.name)
				t.save()
		if self.id:
			self.delete()

	def is_reachable(self):
		return time.time() - self.hostInfoTimestamp <= 2 * settings.get_host_connections_settings()[Config.HOST_UPDATE_INTERVAL]

	def problems(self):
		problems = []
		if not self.enabled:
			problems.append("Manually disabled")
		hi = self.hostInfo
		if time.time() - self.hostInfoTimestamp > 2 * settings.get_host_connections_settings()[Config.HOST_UPDATE_INTERVAL] + 300:
			problems.append("Host unreachable")
		if problems:
			return problems
		if time.time() - self.lastResourcesSync > 2 * settings.get_host_connections_settings()[Config.HOST_RESOURCE_SYNC_INTERVAL] + 300:
			problems.append("Host is not synchronized")
		if not hi:
			problems.append("Node info is missing")
			return problems
		if hi["uptime"] < 10 * 60:
			problems.append("Node just booted")
		if hi["time_diff"] > 5 * 60:
			problems.append("Node clock is out of sync")
		if hi["query_time"] > 5:
			problems.append("Last query took very long")
		res = hi["resources"]
		cpus = res["cpus_present"]
		if not cpus["count"]:
			problems.append("No CPUS ?!?")
		if cpus["bogomips_avg"] < 1000:
			problems.append("Slow CPUs")
		if res["loadavg"][1] > cpus["count"]:
			problems.append("High load")
		disks = res["diskspace"]
		if int(disks["root"]["total"]) - int(disks["root"]["used"]) < 1e6:
			problems.append("Root disk full")
		if int(disks["data"]["total"]) - int(disks["data"]["used"]) < 10e6:
			problems.append("Data disk full")
		if int(res["memory"]["total"]) - int(res["memory"]["used"]) < 1e6:
			problems.append("Memory full")
		if self.componentErrors > 2:
			problems.append("Multiple component errors")
		if "dumps" in hi and hi["dumps"] >= 100:
			problems.append("Lots of error dumps")
		if "problems" in hi:
			problems += hi["problems"]
		return problems

	def sendMessageToHostManagers(self, title, message, ref, subject_group):
		api = get_backend_users_proxy()
		api.broadcast_message_multifilter(title=title, message=message, ref=ref, subject_group=subject_group,
																			filters = [
																				(None, Flags.GlobalHostManager),
																				(self.site.organization, Flags.OrgaHostManager),
																				(None, Flags.GlobalHostContact),
																				(self.site.organization, Flags.OrgaHostContact)
																			])

	def checkProblems(self):
		if time.time() - starttime < 600:
			return
		problems = self.problems()
		if problems and not self.problemAge:
			# a brand new problem, wait until it is stable
			self.problemAge = time.time()
		if self.problemAge and not problems:
			if self.problemMailTime >= self.problemAge:
				# problem is resolved and mail has been sent for this problem
				self.sendMessageToHostManagers(
					title="Host %s: Problems resolved" % self,
					message="Problems on host %s have been resolved." % self,
					ref=Reference.host(self.name),
					subject_group="host failure"
				)
			self.problemAge = 0
		if problems and (self.problemAge < time.time() - settings.get_host_connections_settings()[Config.HOST_UPDATE_INTERVAL] * 5):
			if self.problemMailTime < self.problemAge:
				# problem exists and no mail has been sent so far
				self.problemMailTime = time.time()
				self.sendMessageToHostManagers(
					title="Host %s: Problems" % self,
					message="Host %s has the following problems:\n\n%s" % (self, ", ".join(problems)),
					ref=Reference.host(self.name),
					subject_group="host failure"
				)
			if self.problemAge < time.time() - 6 * 60 * 60:
				# persistent problem older than 6h
				if 2 * (time.time() - self.problemMailTime) >= time.time() - self.problemAge:
					import datetime
					self.problemMailTime = time.time()
					duration = datetime.timedelta(hours=int(time.time()-self.problemAge)/3600)
					self.sendMessageToHostManagers(
						title="Host %s: Problems persist" % self,
						message="Host %s has the following problems since %s:\n\n%s" % (self, duration, ", ".join(problems)),
						ref=Reference.host(self.name),
						subject_group="host failure"
					)
		self.save_if_exists()

	def getLoad(self):
		"""
		Returns the host load on a scale from 0 (no load) to 1.0 (fully loaded)
		"""
		hi = self.hostInfo
		if not hi:
			return -1
		res = hi["resources"]
		cpus = res["cpus_present"]
		disks = res["diskspace"]
		load = []
		load.append(res["loadavg"][1] / cpus["count"])
		load.append(float(res["memory"]["used"]) / int(res["memory"]["total"]))
		load.append(float(disks["data"]["used"]) / int(disks["data"]["total"]))
		return min(max(load), 1.0)

	def __str__(self):
		return self.name

	def __repr__(self):
		return "Host(%s)" % self.name

	@classmethod
	def get(cls, **kwargs):
		try:
			return Host.objects.get(**kwargs)
		except Host.DoesNotExist:
			return None

	@classmethod
	def getAll(cls, **kwargs):
		return Host.objects.filter(**kwargs)

	@classmethod
	def create(cls, name, site, **attrs):
		UserError.check(Host.get(name=name) is None, code=UserError.ALREADY_EXISTS, message="Host with that name (\"\") already exists")
		UserError.check('/' not in name, code=UserError.INVALID_VALUE, message="Host name may not include a '/'") #FIXME: find out if still used
		for attr in ["address", "rpcurl"]:
			UserError.check(attr in attrs.keys(), code=UserError.INVALID_CONFIGURATION, message="Missing attribute for host: %s" % attr)
		host = Host(name=name, site=site)
		try:
			attrs_ = attrs.copy()
			host.init(**attrs_)
			host.save()
			logging.logMessage("create", category="host", info=host.info())
		except:
			host.remove()
			raise
		return host


class HostObject(BaseDocument):
	"""
	:type host: Host
	:type topologyElement: element.Element
	:type topologyConnection: connection.Connection
	"""
	host = ReferenceField(Host, required=True, reverse_delete_rule=CASCADE)
	num = StringField(unique_with='host', required=True)
	topologyElement = ReferenceField('Element', db_field='topology_element') #reverse_delete_rule=NULLIFY defined at bottom of element/__init__.py
	topologyConnection = ReferenceField('Connection', db_field='topology_connection')  #reverse_delete_rule=NULLIFY defined at bottom of connections.py
	state = StringField(required=True)
	type = StringField(required=True)
	objectInfo = DictField(db_field='object_info')
	meta = {
		"abstract": True
	}

	@property
	def capabilities(self):
		raise NotImplemented()

	def getAllowedActions(self):
		caps = self.capabilities["actions"]
		res = {}
		for key, info in caps.iteritems():
			if self.state in info["allowed_states"]:
				res[key] = info
		return res

	def getAllowedAttributes(self):
		caps = self.capabilities["attributes"]
		ret = {}
		for key, info in caps.iteritems():
			states = info.get("states_writable")
			if states is None or self.state in states:
				ret[key] = info
		return ret


def select(site=None, elementTypeConfigurations=None, connectionTypes=None, networkKinds=None, hostPrefs=None, sitePrefs=None, best=True, template=None):
	# STEP 1: limit host choices to what is possible
	if not sitePrefs: sitePrefs = {}
	if not hostPrefs: hostPrefs = {}
	if not networkKinds: networkKinds = []
	if not connectionTypes: connectionTypes = []
	if not elementTypeConfigurations: elementTypeConfigurations = [[]]
	all_ = Host.getAll(site=site) if site else Host.getAll()
	hosts = []
	for host in all_:
		if host.problems():
			continue

		fulfillsConfig = False  # accept host if one config is fulfilled
		for elementTypes in elementTypeConfigurations:
			if not (set(elementTypes) - set(host.elementTypes)):
				fulfillsConfig = True
				break
		if not fulfillsConfig:
			continue

		if connectionTypes and set(connectionTypes) - set(host.connectionTypes):
			continue
		if networkKinds and set(networkKinds) - set(host.getNetworkKinds()):
			continue
		if template and host.name not in template.hosts:
			continue
		if not best:
			return host
		hosts.append(host)
	UserError.check(hosts, code=UserError.INVALID_CONFIGURATION, message="No hosts found for requirements", data={
		'site': site.name if site else None, 'element_type_configurations': elementTypeConfigurations, 'connection_types': connectionTypes, 'network_kinds': networkKinds
	})
	# any host in hosts can handle the request
	prefs = dict([(h, 0.0) for h in hosts])
	# STEP 2: calculate preferences based on host load
	els = 0.0
	cons = 0.0
	for h in hosts:
		prefs[h] -= h.componentErrors * 25  # discourage hosts with previous errors
		prefs[h] -= h.getLoad() * 100  # up to -100 points for load
		els += h.elements.count()
		cons += h.connections.count()
	avgEls = els / len(hosts)
	avgCons = cons / len(hosts)
	for h in hosts:
		# between -30 and +30 points for element/connection over-/under-population
		if avgEls:
			prefs[h] -= max(-20.0, min(10.0 * (h.elements.count() - avgEls) / avgEls, 20.0))
		if avgCons:
			prefs[h] -= max(-10.0, min(10.0 * (h.connections.count() - avgCons) / avgCons, 10.0))
		# STEP 3: calculate preferences based on host location
	for h in hosts:
		if h in hostPrefs:
			prefs[h] += hostPrefs[h]
		if h.site in sitePrefs:
			prefs[h] += sitePrefs[h.site]
	#STEP 4: select the best host
	hosts.sort(key=lambda h: prefs[h], reverse=True)
	logging.logMessage("select", category="host", result=hosts[0].name,
					   prefs=dict([(k.name, v) for k, v in prefs.iteritems()]),
					   site=site.name if site else None, element_types=elementTypes, connection_types=connectionTypes,
					   network_types=networkKinds,
					   host_prefs=dict([(k.name, v) for k, v in hostPrefs.iteritems()]),
					   site_prefs=dict([(k.name, v) for k, v in sitePrefs.iteritems()]))
	return hosts[0]


def getElementTypes():
	global element_caps
	return element_caps.keys()

@deprecated("host.Host.getElementCapabilites")
def getElementCapabilities(type_):
	return Host.getElementCapabilities(type_)


def getConnectionTypes():
	global connection_caps
	return connection_caps.keys()

@deprecated("host.Host.getConnectionCapabilites")
def getConnectionCapabilities(type_):
	return Host.getConnectionCapabilities(type_)


checkingHostsLock = threading.RLock()
checkingHosts = set()


@util.wrap_task
def synchronizeHost(host_name):
	try:
		host = Host.objects.get(name=host_name)
	except DoesNotExist:
		return  # nothing to synchronize
	with checkingHostsLock:
		if host in checkingHosts:
			return
		checkingHosts.add(host)
	try:
		try:
			try:
				host.update()
				host.synchronizeResources()
			except Exception as e:
				print >>sys.stderr, "Error updating host information from %s" % host_name
				if isinstance(e, TransportError):
					e.todump = False
				else:
					traceback.print_exc()
				wrap_and_handle_current_exception(re_raise=True)
		finally:
			host.checkProblems()
	finally:
		with checkingHostsLock:
			checkingHosts.remove(host)

updatingAccountingHostsLock = threading.RLock()
updatingAccountingHosts = set()

@util.wrap_task
def updateAccounting(host_name):
	try:
		host = Host.objects.get(name=host_name)
	except DoesNotExist:
		return  # I refuse to do this impossible task. Hopefully the scheduler will not call me again with this.
	with updatingAccountingHostsLock:
		if host in updatingAccountingHosts:
			return
		updatingAccountingHosts.add(host)
	try:
		host.updateAccountingData()
	except Exception as e:
		print >>sys.stderr, "Error updating accounting information from %s" % host_name
		if isinstance(e, TransportError):
			e.todump = False
		else:
			traceback.print_exc()
		wrap_and_handle_current_exception(re_raise=True)
	finally:
		with updatingAccountingHostsLock:
			updatingAccountingHosts.remove(host)

from .site import Site

def list_host_names():
	return [h.name for h in Host.getAll().only("name")]

scheduler.scheduleMaintenance(settings.get_host_connections_settings()[Config.HOST_UPDATE_INTERVAL],
                              list_host_names, synchronizeHost)
scheduler.scheduleMaintenance(settings.get_host_connections_settings()[Config.HOST_UPDATE_INTERVAL],
                              list_host_names, updateAccounting)
