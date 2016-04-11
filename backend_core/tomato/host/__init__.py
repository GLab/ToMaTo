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

import base64
import sys
import threading
import time
import zlib

from .. import starttime, scheduler
from ..accounting.quota import UsageStatistics
from ..db import *
from ..generic import *
from ..lib import anyjson as json
from ..lib import rpc, util, logging, error
from ..lib.cache import cached
from ..lib.error import TransportError, InternalError, UserError, Error
from ..lib.service import get_backend_users_proxy
from ..lib.settings import settings, Config
from ..lib.userflags import Flags


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
				if not self._proxy or not rpc.isReusable(self._proxy):
					self._proxy = rpc.createProxy(self._url, *self._args, **self._kwargs)
				try:
					return getattr(self._proxy, name)(*args, **kwargs)
				except Error as err:
					if isinstance(err, TransportError):
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
	:type totalUsage: UsageStatistics
	:type site: tomato.host.site.Site
	:type templates: list of Template
	"""
	from ..resources.template import Template
	name = StringField(required=True, unique=True)
	address = StringField(required=True)
	rpcurl = StringField(required=True, unique=True)
	from .site import Site
	site = ReferenceField(Site, required=True, reverse_delete_rule=DENY)
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True, reverse_delete_rule=DENY)
	elementTypes = DictField(db_field='element_types')
	connectionTypes = DictField(db_field='connection_types')
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
	templates = ListField(ReferenceField(Template, reverse_delete_rule=PULL))
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

	ACTIONS = {}
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
		"element_types": Attribute(readOnly=True, get=lambda obj: obj.elementTypes.keys(), schema=schema.List(items=schema.Identifier())),
		"connection_types": Attribute(readOnly=True, get=lambda obj: obj.connectionTypes.keys(), schema=schema.List(items=schema.Identifier())),
		"host_info": Attribute(field=hostInfo, readOnly=True, schema=schema.StringMap(additional=True)),
		"host_info_timestamp": Attribute(field=hostInfoTimestamp, readOnly=True, schema=schema.Number()),
		"availability": Attribute(field=availability, readOnly=True, schema=schema.Number()),
		"networks": Attribute(field=hostNetworks, readOnly=True, schema=schema.List())
	}

	def init(self, attrs=None):
		self.attrs = {}
		self.totalUsage = UsageStatistics.objects.create()
		self.hostInfoTimestamp = 0
		self.accountingTimestamp = 0
		self.lastResourcesSync = 0
		if attrs:
			self.modify(attrs)
		self.update()

	def getProxy(self):
		if not _caching:
			return RemoteWrapper(self.rpcurl, self.name, sslcert=settings.get_ssl_cert_filename(), sslkey=settings.get_ssl_key_filename(), sslca=settings.get_ssl_ca_filename(), timeout=settings.get_rpc_timeout())
		if not self.rpcurl in _proxies:
			_proxies[self.rpcurl] = RemoteWrapper(self.rpcurl, self.name, sslcert=settings.get_ssl_cert_filename(), sslkey=settings.get_ssl_key_filename(), sslca=settings.get_ssl_ca_filename(), timeout=settings.get_rpc_timeout())
		return _proxies[self.rpcurl]

	def incrementErrors(self):
		# count all component errors {element|connection}_{create|action|modify}
		# this value is reset on every sync
		logging.logMessage("component error", category="host", host=self.name)
		self.componentErrors += 1
		self.save()

	def update(self):
		self.availability *= settings.get_host_connections_settings()[Config.HOST_AVAILABILITY_FACTOR]
		self.save()
		if not self.enabled:
			return
		before = time.time()
		self.hostInfo = self._info()
		after = time.time()
		self.hostInfoTimestamp = (before + after) / 2.0
		self.hostInfo["query_time"] = after - before
		self.hostInfo["time_diff"] = self.hostInfo["time"] - self.hostInfoTimestamp
		try:
			self.hostNetworks = self.getProxy().host_networks()
		except:
			self.hostNetworks = []
		caps = self._convertCapabilities(self.getProxy().host_capabilities())
		self.elementTypes = caps["elements"]
		self.connectionTypes = caps["connections"]
		self.componentErrors = max(0, self.componentErrors / 2)
		if not self.problems():
			self.availability += 1.0 - settings.get_host_connections_settings()[Config.HOST_AVAILABILITY_FACTOR]
		self.save()
		logging.logMessage("info", category="host", name=self.name, info=self.hostInfo)
		logging.logMessage("capabilities", category="host", name=self.name, capabilities=caps)

	def _convertCapabilities(self, caps):
		def convertActions(actions, next_state):
			res = {}
			for action, states in actions.items():
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
				res[attr] = StatefulAttribute(writableStates=desc.get('states'), label=desc.get('desc'), schema=sch, default=desc.get('default')).info()
			return res
		elems = {}
		for name, info in caps['elements'].items():
			elems[name] = {
				"actions": convertActions(info.get('actions'), info.get('next_state')),
				"attributes": convertAttributes(info.get('attrs')),
				"children": {n: {"allowed_states": states} for n, states in info.get('children').items()},
				"parent": info.get('parent'),
				"connectability": [{"concept": n, "allowed_states": None} for n in info.get('con_concepts')]
			}
		cons = {}
		for name, info in caps['connections'].items():
			cons[name] = {
				"actions": convertActions(info.get('actions'), info.get('next_state')),
				"attributes": convertAttributes(info.get('attrs')),
				"connectability": [{"concept_from": names[0], "concept_to": names[1]} for names in info.get('con_concepts')]
			}
		return {
			"elements": elems,
			"connections": cons,
			"resources": caps.get('resources')
		}

	def _info(self):
		return self.getProxy().host_info()

	def getElementCapabilities(self, type_):
		return self.elementTypes.get(type_)

	def getConnectionCapabilities(self, type_):
		return self.connectionTypes.get(type_)

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
		hel.usageStatistics = UsageStatistics.objects.create()
		hel.objectInfo = el
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
		hcon.usageStatistics = UsageStatistics.objects.create()
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

	def synchronizeResources(self):
		if time.time() - self.lastResourcesSync < settings.get_host_connections_settings()[Config.HOST_RESOURCE_SYNC_INTERVAL]:
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
			attrs = {"tech": tpl.tech, "name": tpl.name, "preference": tpl.preference, "torrent_data": base64.b64encode(tpl.torrentData), "kblang": tpl.kblang}
			if not (attrs["tech"], attrs["name"]) in tpls:
				# create resource
				self.getProxy().resource_create("template", attrs)
				logging.logMessage("template create", category="host", name=self.name, template=attrs)
			else:
				hTpl = tpls[(attrs["tech"], attrs["name"])]
				isAttrs = dict(hTpl["attrs"])
				if hTpl["attrs"]["torrent_data_hash"] != tpl.torrentDataHash:
					self.getProxy().resource_modify(hTpl["id"], attrs)
					logging.logMessage("template update", category="host", name=self.name, template=attrs)
				elif isAttrs["ready"]:
					avail.append(tpl)
		self.templates = avail
		logging.logMessage("resource_sync end", category="host", name=self.name)
		self.lastResourcesSync = time.time()
		self.save()

	def updateAccountingData(self):
		logging.logMessage("accounting_sync begin", category="host", name=self.name)
		data = self.getProxy().accounting_statistics(type="5minutes", after=self.accountingTimestamp - 900)
		for el in self.elements.all():
			if not el.usageStatistics:
				el.usageStatistics = UsageStatistics.objects.create()
				el.save()
			if not str(el.num) in data["elements"]:
				print >>sys.stderr, "Missing accounting data for element #%d on host %s" % (el.num, self.name)
				continue
			logging.logMessage("host_records", category="accounting", host=self.name,
							   records=data["elements"][str(el.num)], object=("element", el.idStr))
			el.usageStatistics.importRecords(data["elements"][str(el.num)])
		for con in self.connections.all():
			if not con.usageStatistics:
				con.usageStatistics = UsageStatistics.objects.create()
				con.save()
			if not str(con.num) in data["connections"]:
				print >>sys.stderr, "Missing accounting data for connection #%d on host %s" % (con.num, self.name)
				continue
			logging.logMessage("host_records", category="accounting", host=self.name,
							   records=data["connections"][str(con.num)], object=("connection", con.idStr))
			con.usageStatistics.importRecords(data["connections"][str(con.num)])
		self.accountingTimestamp = time.time()
		self.save()
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
		if self.id:
			self.delete()
		self.totalUsage.remove()

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
					ref=['host', self.name],
					subject_group="host failure"
				)
			self.problemAge = 0
		if problems and (self.problemAge < time.time() - settings.get_host_connections_settings()[Config.HOST_UPDATE_INTERVAL] * 5):
			if self.problemMailTime < self.problemAge:
				# problem exists and no mail has been sent so far
				self.problemMailTime = time.time()
				self.sendMessageToHostManagers(
					title="Host %s: Problems" % self,
					message="Host %s has the following problems:\n\n%s" % self,
					ref=['host', self.name],
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
						ref=['host', self.name],
						subject_group="host failure"
					)
		self.save()

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
	def create(cls, name, site, attrs=None):
		if not attrs: attrs = {}
		UserError.check('/' not in name, code=UserError.INVALID_VALUE, message="Host name may not include a '/'") #FIXME: find out if still used
		for attr in ["address", "rpcurl"]:
			UserError.check(attr in attrs.keys(), code=UserError.INVALID_CONFIGURATION, message="Missing attribute for host: %s" % attr)
		host = Host(name=name, site=site)
		try:
			attrs_ = attrs.copy()
			attrs_['name'] = name
			host.init(attrs_)
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
	:type usageStatistics: UsageStatistics
	"""
	host = ReferenceField(Host, required=True, reverse_delete_rule=CASCADE)
	num = IntField(unique_with='host', required=True)
	topologyElement = ReferenceField('Element', db_field='topology_element') #reverse_delete_rule=NULLIFY defined at bottom of element/__init__.py
	topologyConnection = ReferenceField('Connection', db_field='topology_connection')  #reverse_delete_rule=NULLIFY defined at bottom of connections.py
	usageStatistics = ReferenceField(UsageStatistics, db_field='usage_statistics', required=True, reverse_delete_rule=DENY)
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


def select(site=None, elementTypes=None, connectionTypes=None, networkKinds=None, hostPrefs=None, sitePrefs=None, best=True, template=None):
	# STEP 1: limit host choices to what is possible
	if not sitePrefs: sitePrefs = {}
	if not hostPrefs: hostPrefs = {}
	if not networkKinds: networkKinds = []
	if not connectionTypes: connectionTypes = []
	if not elementTypes: elementTypes = []
	all_ = Host.getAll(site=site) if site else Host.getAll()
	hosts = []
	for host in all_:
		if host.problems():
			continue
		if elementTypes and set(elementTypes) - set(host.elementTypes.keys()):
			continue
		if connectionTypes and set(connectionTypes) - set(host.connectionTypes.keys()):
			continue
		if networkKinds and set(networkKinds) - set(host.getNetworkKinds()):
			continue
		if template and template not in host.templates:
			continue
		if not best:
			return host
		hosts.append(host)
	UserError.check(hosts, code=UserError.INVALID_CONFIGURATION, message="No hosts found for requirements", data={
		'site': site, 'element_types': elementTypes, 'connection_types': connectionTypes, 'network_kinds': networkKinds
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


@cached(timeout=3600, autoupdate=True)
def getElementTypes():
	types = set()
	for h in Host.getAll():
		types += set(h.elementTypes.keys())
	return types


@cached(timeout=3600, autoupdate=True)
def getElementCapabilities(type_):
	# FIXME: merge capabilities
	caps = {}
	for h in Host.getAll():
		hcaps = h.getElementCapabilities(type_)
		if len(repr(hcaps)) > len(repr(caps)):
			caps = hcaps
	return caps


@cached(timeout=3600, autoupdate=True)
def getConnectionTypes():
	types = set()
	for h in Host.getAll():
		types += set(h.connectionTypes.keys())
	return types


@cached(timeout=3600, autoupdate=True)
def getConnectionCapabilities(type_):
	# FIXME: merge capabilities
	caps = {}
	for h in Host.getAll():
		hcaps = h.getConnectionCapabilities(type_)
		if len(repr(hcaps)) > len(repr(caps)):
			caps = hcaps
	return caps


checkingHostsLock = threading.RLock()
checkingHosts = set()


@util.wrap_task
def synchronizeHost(host):
	with checkingHostsLock:
		if host in checkingHosts:
			return
		checkingHosts.add(host)
	try:
		try:
			host.update()
			host.synchronizeResources()
			host.updateAccountingData()
		except:
			import traceback

			traceback.print_exc()
			logging.logException(host=host.name)
			print >>sys.stderr, "Error updating information from %s" % host
		host.checkProblems()
	finally:
		with checkingHostsLock:
			checkingHosts.remove(host)

@util.wrap_task
def synchronizeComponents():
	from .element import HostElement
	for hel in HostElement.objects.all():
		try:
			hel.synchronize()
		except Exception:
			handleError()
	from .connection import HostConnection
	for hcon in HostConnection.objects.all():
		try:
			hcon.synchronize()
		except Exception:
			handleError()


from .site import Site
from .. import handleError

scheduler.scheduleMaintenance(settings.get_host_connections_settings()[Config.HOST_UPDATE_INTERVAL],
                              Host.getAll, synchronizeHost)
scheduler.scheduleRepeated(3600, synchronizeComponents)  # @UndefinedVariable
