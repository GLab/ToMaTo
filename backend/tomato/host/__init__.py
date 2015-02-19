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
from .. import config, currentUser, starttime, scheduler
from ..accounting import UsageStatistics
from ..lib import rpc, util, logging, error
from ..lib.cache import cached
from ..lib.error import TransportError, InternalError, UserError, Error
from ..lib import anyjson as json
from ..dumpmanager import DumpSource
import time, hashlib, threading, datetime, zlib, base64, sys

class RemoteWrapper:
	def __init__(self, url, host, *args, **kwargs):
		self._url = url
		self._host = host
		self._args = args
		self._kwargs = kwargs
		self._proxy = None

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
							print("Retrying after error on %s: %s, retries left: %d" % (self._host, err, retries))
							continue
						if not err.data:
							err.data = {}
						err.data["host"] = self._host
					raise err, None, sys.exc_info()[2]
				except Exception as exc:
					print "Warning: received unwrapped error:"
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

class Host(DumpSource, BaseDocument, Entity):
	"""
	:type totalUsage: UsageStatistics
	:type site: host.site.Site
	:type templates: list of Template
	"""
	from ..resources.template import Template
	name = StringField(required=True, unique=True)
	address = StringField(required=True)
	rpcurl = StringField(required=True, unique=True)
	from .site import Site
	site = ReferenceField(Site, required=True)
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True)
	elementTypes = DictField(db_field='element_types', required=True)
	connectionTypes = DictField(db_field='connection_types', required=True)
	hostInfo = DictField(db_field='host_info', required=True)
	hostInfoTimestamp = FloatField(db_field='host_info_timestamp', required=True)
	accountingTimestamp = FloatField(db_field='accounting_timestamp', required=True)
	lastResourcesSync = FloatField(db_field='last_resource_sync', required=True)
	enabled = BooleanField(default=True)
	componentErrors = IntField(default=0, db_field='component_errors')
	problemAge = FloatField(db_field='problem_age')
	problemMailTime = FloatField(db_field='problem_mail_time')
	availability = FloatField(default=1.0)
	description = StringField()
	dumpLastFetch = FloatField(db_field='dump_last_fetch')
	templates = ListField(ReferenceField(Template))
	hostNetworks = DictField(db_field='host_networks')
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
		"name": Attribute(field="name", schema=schema.Identifier()),
		"address": Attribute(field="address", schema=schema.String(regex="\d+\.\d+.\d+.\d+")),
		"rpcurl": Attribute(field="rpcurl", schema=schema.String(regex="\w+://\w+:\d+")),
		"site": Attribute(
			check=lambda obj, val: Site.get(val),
			set=lambda obj, val: setattr(obj, "site", Site.get(val)),
			get=lambda obj: obj.site.name,
			schema=schema.Identifier()
		),
		"enabled": Attribute(field="enabled", schema=schema.Bool()),
		"description": Attribute(field="description", schema=schema.String()),
		"organization": Attribute(readOnly=True, get=lambda obj: obj.site.organization.name, schema=schema.Identifier()),
		"problems": Attribute(readOnly=True, get=lambda obj: obj.problems(), schema=schema.List(items=schema.String())),
		"component_errors": Attribute(field="componentErrors", readOnly=True, schema=schema.Int()),
		"load": Attribute(readOnly=True, get=lambda obj: obj.getLoad(), schema=schema.List(items=schema.Number())),
		"element_types": Attribute(readOnly=True, get=lambda obj: obj.elementTypes.keys(), schema=schema.List(items=schema.Identifier())),
		"connection_types": Attribute(readOnly=True, get=lambda obj: obj.connectionTypes.keys(), schema=schema.List(items=schema.Identifier())),
		"host_info": Attribute(field="hostInfo", readOnly=True, schema=schema.StringMap(additional=True)),
		"host_info_timestamp": Attribute(field="hostInfoTimestamp", readOnly=True, schema=schema.Number()),
		"availability": Attribute(field="availability", readOnly=True, schema=schema.Number()),
		"networks": Attribute(field="hostNetworks", readOnly=True, schema=schema.List())
	}

	def init(self, attrs=None):
		self.attrs = {}
		self.totalUsage = UsageStatistics.objects.create()
		if attrs:
			self.modify(attrs)
		self.update()

	def getProxy(self):
		if not _caching:
			return RemoteWrapper(self.rpcurl, self.name, sslcert=config.CERTIFICATE, timeout=config.RPC_TIMEOUT)
		if not self.rpcurl in _proxies:
			_proxies[self.rpcurl] = RemoteWrapper(self.rpcurl, self.name, sslcert=config.CERTIFICATE,
												  timeout=config.RPC_TIMEOUT)
		return _proxies[self.rpcurl]

	def incrementErrors(self):
		# count all component errors {element|connection}_{create|action|modify}
		# this value is reset on every sync
		logging.logMessage("component error", category="host", host=self.name)
		self.componentErrors += 1
		self.save()

	def update(self):
		self.availability *= config.HOST_AVAILABILITY_FACTOR
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
			self.hostNetworks = None
		caps = self._capabilities()
		self.elementTypes = caps["elements"]
		self.connectionTypes = caps["connections"]
		self.componentErrors = max(0, self.componentErrors / 2)
		if not self.problems():
			self.availability += 1.0 - config.HOST_AVAILABILITY_FACTOR
		self.save()
		logging.logMessage("info", category="host", name=self.name, info=self.hostInfo)
		logging.logMessage("capabilities", category="host", name=self.name, capabilities=caps)

	def _capabilities(self):
		return self.getProxy().host_capabilities()

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
		hel = HostElement(host=self, num=el["id"], topology_element=ownerElement, topology_connection=ownerConnection)
		hel.usageStatistics = UsageStatistics.objects.create()
		hel.objectInfo = el
		hel.save()
		logging.logMessage("element_create", category="host", host=self.name, element=el,
						   ownerElement=(
							   ownerElement.__class__.__name__.lower(), ownerElement.id) if ownerElement else None,
						   ownerConnection=(
							   ownerConnection.__class__.__name__.lower(),
							   ownerConnection.id) if ownerConnection else None)
		return hel

	def getElement(self, num):
		return self.elements.get(num=num)

	def createConnection(self, hel1, hel2, type_=None, attrs=None, ownerElement=None, ownerConnection=None):
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
		hcon = HostConnection(host=self, num=con["id"], topology_element=ownerElement,
							  topology_connection=ownerConnection)
		hcon.usageStatistics = UsageStatistics.objects.create()
		hcon.objectInfo = con
		hcon.save()
		logging.logMessage("connection_create", category="host", host=self.name, element=con,
						   ownerElement=(
							   ownerElement.__class__.__name__.lower(), ownerElement.id) if ownerElement else None,
						   ownerConnection=(
							   ownerConnection.__class__.__name__.lower(),
							   ownerConnection.id) if ownerConnection else None)
		return hcon

	def getConnection(self, num):
		return self.connections.get(num=num)

	def grantUrl(self, grant, action):
		return "http://%s:%d/%s/%s" % (self.address, self.hostInfo["fileserver_port"], grant, action)

	def synchronizeResources(self):
		if time.time() - self.lastResourcesSync < config.RESOURCES_SYNC_INTERVAL:
			return
		if not self.enabled:
			return

		logging.logMessage("resource_sync begin", category="host", name=self.name)
		# TODO: implement for other resources
		from .. import resources

		hostNets = {}
		for net in self.getProxy().resource_list("network"):
			hostNets[net["attrs"]["bridge"]] = net
		for net in self.networks.all():
			key = net.bridge
			attrs = net.attrs.copy()
			attrs["bridge"] = net.bridge
			attrs["kind"] = net.getKind()
			attrs["preference"] = net.network.preference
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
			tpls[tpl["attrs"]["tech"]] = tpls.get(tpl["attrs"]["tech"], {})
			tpls[tpl["attrs"]["tech"]][tpl["attrs"]["name"]] = tpl
		for tpl in resources.getAll(type="template"):
			attrs = tpl.attrs.copy()
			attrs["name"] = tpl.name
			attrs["tech"] = tpl.tech
			try:
				toh = self.templates.get(template=tpl)
			except TemplateOnHost.DoesNotExist:
				toh = TemplateOnHost.objects.create(host=self, template=tpl, ready=False, date=time.time())
			if not attrs["tech"] in tpls or not attrs["name"] in tpls[attrs["tech"]]:
				# create resource
				self.getProxy().resource_create("template", attrs)
				logging.logMessage("template create", category="host", name=self.name, template=attrs)
				toh.ready = False
				toh.date = time.time()
				toh.save()
			else:
				hTpl = tpls[attrs["tech"]][attrs["name"]]
				isAttrs = dict(hTpl["attrs"])
				if isAttrs["ready"] != toh.ready:
					toh.ready = isAttrs["ready"]
					toh.date = time.time()
					toh.save()
				del isAttrs["ready"]
				del isAttrs["preference"]  # we have our own
				shouldAttrs = dict(attrs)
				shouldAttrs["torrent_data_hash"] = hashlib.md5(
					attrs["torrent_data"]).hexdigest() if "torrent_data" in attrs else None
				del shouldAttrs["torrent_data"]
				if isAttrs != shouldAttrs:
					# update resource
					if isAttrs["torrent_data_hash"] == shouldAttrs["torrent_data_hash"]:
						# only send torrent data when needed
						del attrs["torrent_data"]
					else:
						toh.ready = False
						toh.date = time.time()
						toh.save()
					self.getProxy().resource_modify(hTpl["id"], attrs)
					logging.logMessage("template update", category="host", name=self.name, template=attrs)
		logging.logMessage("resource_sync end", category="host", name=self.name)
		self.lastResourcesSync = time.time()
		self.save()

	def hasTemplate(self, tpl):
		return len(self.templates.filter(template=tpl, ready=True))

	def updateUsage(self):
		self.totalUsage.updateFrom(
			[hel.usageStatistics for hel in self.elements.all()] + [hcon.usageStatistics for hcon in
																	self.connections.all()])

	def updateAccountingData(self):
		logging.logMessage("accounting_sync begin", category="host", name=self.name)
		data = self.getProxy().accounting_statistics(type="5minutes", after=self.accountingTimestamp - 900)
		for el in self.elements.all():
			if not el.usageStatistics:
				el.usageStatistics = UsageStatistics.objects.create()
				el.save()
			if not str(el.num) in data["elements"]:
				print "Missing accounting data for element #%d on host %s" % (el.num, self.name)
				continue
			logging.logMessage("host_records", category="accounting", host=self.name,
							   records=data["elements"][str(el.num)], object=("element", el.id))
			el.updateAccountingData(data["elements"][str(el.num)])
		for con in self.connections.all():
			if not con.usageStatistics:
				con.usageStatistics = UsageStatistics.objects.create()
				con.save()
			if not str(con.num) in data["connections"]:
				print "Missing accounting data for connection #%d on host %s" % (con.num, self.name)
				continue
			logging.logMessage("host_records", category="accounting", host=self.name,
							   records=data["connections"][str(con.num)], object=("connection", con.id))
			con.updateAccountingData(data["connections"][str(con.num)])
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
		UserError.check(self.checkPermissions(), code=UserError.DENIED, message="Not enough permissions")
		res = []
		for type_, obj in [("element", el) for el in self.elements.all()] + [("connection", con) for con in
																			 self.connections.all()]:
			data = {"type": type_, "onhost_id": obj.num, "element_id": None, "connection_id": None, "topology_id": None,
					"state": obj.state}
			if obj.topology_element:
				tel = obj.topology_element
				data["element_id"] = tel.id
				data["topology_id"] = tel.topology_id
			if obj.topology_connection:
				tcon = obj.topology_connection
				data["connection_id"] = tcon.id
				data["topology_id"] = tcon.topology_id
			res.append(data)
		return res

	def checkPermissions(self):
		return self.site.checkPermissions()

	def remove(self):
		UserError.check(self.checkPermissions(), code=UserError.DENIED, message="Not enough permissions")
		UserError.check(not self.elements.all(), code=UserError.NOT_EMPTY, message="Host still has active elements")
		UserError.check(not self.connections.all(), code=UserError.NOT_EMPTY, message="Host still has active connections")
		logging.logMessage("remove", category="host", name=self.name)
		try:
			for res in self.getProxy().resource_list():
				self.getProxy().resource_remove(res["id"])
		except:
			pass
		self.totalUsage.remove()
		self.delete()

	def problems(self):
		problems = []
		if not self.enabled:
			problems.append("Manually disabled")
		hi = self.hostInfo
		if time.time() - max(self.hostInfoTimestamp, starttime) > 2 * config.HOST_UPDATE_INTERVAL + 300:
			problems.append("Host unreachable")
		if problems:
			return problems
		if time.time() - max(self.lastResourcesSync, starttime) > 2 * config.RESOURCES_SYNC_INTERVAL + 300:
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

	def checkProblems(self):
		from auth import mailFilteredUsers

		problems = self.problems()
		if problems and not self.problemAge:
			# a brand new problem, wait until it is stable
			self.problemAge = time.time()
		if self.problemAge and not problems:
			if self.problemMailTime >= self.problemAge:
				# problem is resolved and mail has been sent for this problem
				mailFilteredUsers(lambda user: user.hasFlag(Flags.GlobalHostContact)
											   or user.hasFlag(
					Flags.OrgaHostContact) and user.organization == self.site.organization,
								  "Host %s: Problems resolved" % self, "Problems on host %s have been resolved." % self)
			self.problemAge = 0
		if problems and (self.problemAge < time.time() - 300):
			if self.problemMailTime < self.problemAge:
				# problem exists and no mail has been sent so far
				self.problemMailTime = time.time()
				mailFilteredUsers(lambda user: user.hasFlag(Flags.GlobalHostContact)
											   or user.hasFlag(
					Flags.OrgaHostContact) and user.organization == self.site.organization,
								  "Host %s: Problems" % self,
								  "Host %s has the following problems:\n\n%s" % (self, ", ".join(problems)))
			if self.problemAge < time.time() - 6 * 60 * 60:
				# persistent problem older than 6h
				if 2 * (time.time() - self.problemMailTime) >= time.time() - self.problemAge:
					self.problemMailTime = time.time()
					from django.template.defaultfilters import timesince

					duration = timesince(datetime.datetime.fromtimestamp(self.problemAge))
					mailFilteredUsers(lambda user: user.hasFlag(Flags.GlobalHostContact)
												   or user.hasFlag(
						Flags.OrgaHostContact) and user.organization == self.site.organization,
									  "Host %s: Problems persist" % self,
									  "Host %s has the following problems since %s:\n\n%s" % (
										  self, duration, ", ".join(problems)))

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

	def dump_fetch_list(self, after):  # TODO: return None if unreachable
		return self.getProxy().dump_list(after=after, list_only=False, include_data=False, compress_data=True)

	def dump_fetch_with_data(self, dump_id, keep_compressed=True):
		# TODO: return None if unreachable, return dummy if it does not exist
		dump = self.getProxy().dump_info(dump_id, include_data=True, compress_data=True)
		if not keep_compressed:
			dump['data'] = json.loads(zlib.decompress(base64.b64decode(dump['data'])))
		return dump

	def dump_clock_offset(self):
		return max(0, -self.hostInfo['time_diff'])

	def dump_source_name(self):
		return "host:%s" % self.info()['name']

	def dump_matches_host(self, host_obj):
		return host_obj.dump_source_name() == self.dump_source_name()

	def dump_set_last_fetch(self, last_fetch):
		self.dump_last_fetch = last_fetch
		self.save()

	def dump_get_last_fetch(self):
		return self.dump_last_fetch

	@classmethod
	def get(cls, **kwargs):
		try:
			return Host.objects.get(**kwargs)
		except Host.DoesNotExist:
			return None

	@classmethod
	def getAll(cls, **kwargs):
		return list(Host.objects.filter(**kwargs))

	@classmethod
	def create(cls, name, site, attrs=None):
		if not attrs: attrs = {}
		user = currentUser()
		UserError.check(user.hasFlag(Flags.GlobalHostManager) or user.hasFlag(Flags.OrgaHostManager) and user.organization == site.organization,
			code=UserError.DENIED, message="Not enough permissions")
		host = Host(name=name, site=site)
		host.init(attrs)
		host.save()
		logging.logMessage("create", category="host", info=host.info())
		return host


class HostObject(BaseDocument):
	"""
	:type host: Host
	:type topologyElement: element.Element
	:type topologyConnection: connection.Connection
	:type usageStatistics: UsageStatistics
	"""
	host = ReferenceField(Host, required=True)
	num = IntField(unique_with='host', required=True)
	topologyElement = ReferenceField('Element', db_field='topology_element')
	topologyConnection = ReferenceField('Connection', db_field='topology_connection')
	usageStatistics = ReferenceField(UsageStatistics, db_field='usage_statistics', required=True)
	state = StringField(required=True)
	type = StringField(required=True)
	objectInfo = DictField(db_field='object_info')
	meta = {
		"abstract": True
	}

def select(site=None, elementTypes=None, connectionTypes=None, networkKinds=None, hostPrefs=None, sitePrefs=None):
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
		if set(elementTypes) - set(host.elementTypes.keys()):
			continue
		if set(connectionTypes) - set(host.connectionTypes.keys()):
			continue
		if set(networkKinds) - set(host.getNetworkKinds()):
			continue
		hosts.append(host)
	UserError.check(hosts, code=UserError.INVALID_CONFIGURATION, message="No hosts found for requirements")
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
			print "Error updating information from %s" % host
		host.checkProblems()
	finally:
		with checkingHostsLock:
			checkingHosts.remove(host)


@util.wrap_task
def synchronize():
	for host in Host.getAll():
		if host.enabled:
			scheduler.scheduleOnce(0, synchronizeHost, host)  # @UndefinedVariable


@util.wrap_task
def synchronizeComponents():
	from .element import HostElement
	for hel in HostElement.objects.all():
		hel.synchronize()
	from .connection import HostConnection
	for hcon in HostConnection.objects.all():
		hcon.synchronize()


from ..auth import Flags
from .site import Site

scheduler.scheduleRepeated(config.HOST_UPDATE_INTERVAL, synchronize)  # @UndefinedVariable
scheduler.scheduleRepeated(3600, synchronizeComponents)  # @UndefinedVariable