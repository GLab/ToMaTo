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
from . import config, currentUser, starttime, scheduler, accounting
from accounting import UsageStatistics
from lib import attributes, db, rpc, util, logging, error  # @UnresolvedImport
from lib.cache import cached  # @UnresolvedImport
from lib.error import TransportError, InternalError, UserError, Error
from .lib import anyjson as json
from auth import Flags
from dumpmanager import DumpSource
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
				except Error, err:
					if isinstance(err, TransportError):
						self._proxy = None
						if retries >= 0:
							print "Retrying after error on %s: %s, retries left: %d" % (self._host, err, retries)
							continue
						if not err.data:
							err.data = {}
						err.data["host"] = self._host
					raise err, None, sys.exc_info()[2]
				except Exception, exc:
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


class Organization(attributes.Mixin, models.Model):
	name = models.CharField(max_length=50, unique=True)
	totalUsage = models.OneToOneField(UsageStatistics, null=True, related_name='+', on_delete=models.SET_NULL)
	attrs = db.JSONField()
	description = attributes.attribute("description", unicode, "")
	homepage_url = attributes.attribute("homepage_url", unicode, "")
	image_url = attributes.attribute("image_url", unicode, "")
	description_text = attributes.attribute("description_text", unicode, "")
	# sites: [Site]
	# users: [User]

	class Meta:
		pass

	def init(self, attrs):
		self.totalUsage = UsageStatistics.objects.create()
		self.modify(attrs)

	def checkPermissions(self):
		user = currentUser()
		if user.hasFlag(Flags.GlobalAdmin):
			return True
		if user.hasFlag(Flags.OrgaAdmin) and user.organization == self:
			return True
		return False

	def modify(self, attrs):
		UserError.check(self.checkPermissions(), code=UserError.DENIED, message="Not enough permissions")
		logging.logMessage("modify", category="organization", name=self.name, attrs=attrs)
		for key, value in attrs.iteritems():
			if key == "description":
				self.description = value
			elif key == "homepage_url":
				self.homepage_url = value
			elif key == "image_url":
				self.image_url = value
			elif key == "description_text":
				self.description_text = value
			else:
				raise UserError(code=UserError.UNSUPPORTED_ATTRIBUTE, message="Unknown organization attribute",
					data={"attribute": key})
		self.save()

	def remove(self):
		UserError.check(self.checkPermissions(), code=UserError.DENIED, message="Not enough permissions")
		UserError.check(not self.sites.all(), code=UserError.NOT_EMPTY, message="Organization still has sites")
		UserError.check(not self.users.all(), code=UserError.NOT_EMPTY, message="Organization still has users")
		logging.logMessage("remove", category="organization", name=self.name)
		self.totalUsage.remove()
		self.delete()

	def updateUsage(self):
		self.totalUsage.updateFrom([user.totalUsage for user in self.users.all()])

	def info(self):
		return {
			"name": self.name,
			"description": self.description,
			"homepage_url": self.homepage_url,
			"image_url": self.image_url,
			"description_text": self.description_text
		}

	def __str__(self):
		return self.name

	def __repr__(self):
		return "Organization(%s)" % self.name


def getOrganization(name, **kwargs):
	try:
		return Organization.objects.get(name=name, **kwargs)
	except Organization.DoesNotExist:
		return None


def getAllOrganizations(**kwargs):
	return list(Organization.objects.filter(**kwargs))


def createOrganization(name, description="", attrs={}):
	UserError.check(currentUser().hasFlag(Flags.GlobalAdmin), code=UserError.DENIED, message="Not enough permissions")
	logging.logMessage("create", category="site", name=name, description=description)
	organization = Organization(name=name)
	organization.save()
	attrs.update({"description": description})
	organization.init(attrs)
	return organization


class Site(attributes.Mixin, models.Model):
	name = models.CharField(max_length=50, unique=True)
	organization = models.ForeignKey(Organization, null=False, related_name="sites")
	# hosts: [Host]
	attrs = db.JSONField()
	description = attributes.attribute("description", unicode, "")
	location = attributes.attribute("location", unicode, "")
	geolocation = attributes.attribute("geolocation", dict, {})
	description_text = attributes.attribute("description_text", unicode, "")

	class Meta:
		pass

	def init(self, attrs):
		self.modify(attrs)

	def checkPermissions(self):
		user = currentUser()
		if user.hasFlag(Flags.GlobalHostManager):
			return True
		if user.hasFlag(Flags.OrgaHostManager) and user.organization == self.organization:
			return True
		return False

	def modify(self, attrs):
		UserError.check(self.checkPermissions(), code=UserError.DENIED, message="Not enough permissions")
		logging.logMessage("modify", category="site", name=self.name, attrs=attrs)
		for key, value in attrs.iteritems():
			if key == "description":
				self.description = value
			elif key == "location":
				self.location = value
			elif key == "geolocation":
				self.geolocation = value
			elif key == "description_text":
				self.description_text = value
			elif key == "organization":
				orga = getOrganization(value)
				UserError.check(orga, code=UserError.ENTITY_DOES_NOT_EXIST, message="No organization with that name",
					data={"name": value})
				self.organization = orga
			else:
				raise UserError(code=UserError.UNSUPPORTED_ATTRIBUTE, message="Unknown site attribute",
					data={"attribute": key})
		self.save()

	def remove(self):
		UserError.check(self.checkPermissions(), code=UserError.DENIED, message="Not enough permissions")
		UserError.check(not self.hosts.all(), code=UserError.NOT_EMPTY, message="Site still has hosts")
		logging.logMessage("remove", category="site", name=self.name)
		self.delete()

	def info(self):
		return {
			"name": self.name,
			"description": self.description,
			"location": self.location,
			"geolocation": self.geolocation,
			"organization": self.organization.name,
			"description_text": self.description_text
		}

	def __str__(self):
		return self.name

	def __repr__(self):
		return "Site(%s)" % self.name


def getSite(name, **kwargs):
	try:
		return Site.objects.get(name=name, **kwargs)
	except Site.DoesNotExist:
		return None


def getAllSites(**kwargs):
	return list(Site.objects.filter(**kwargs))


def createSite(name, organization, description="", attrs={}):
	orga = getOrganization(organization)
	UserError.check(orga, code=UserError.ENTITY_DOES_NOT_EXIST, message="No organization with that name",
		data={"name": organization})

	user = currentUser()
	UserError.check(user.hasFlag(Flags.GlobalHostManager) or user.hasFlag(Flags.OrgaHostManager) and user.organization == orga,
		code=UserError.DENIED, message="Not enough permissions")
	logging.logMessage("create", category="site", name=name, description=description)
	site = Site(name=name, organization=orga)
	site.save()
	attrs.update({'description':description})
	site.init(attrs)
	return site


class Host(attributes.Mixin, DumpSource, models.Model):
	name = models.CharField(max_length=255, unique=True)
	address = models.CharField(max_length=255, unique=False)
	rpcurl = models.CharField(max_length=255, unique=True)
	site = models.ForeignKey(Site, null=False, related_name="hosts")
	totalUsage = models.OneToOneField(accounting.UsageStatistics, null=True, related_name='+',
									  on_delete=models.SET_NULL)
	attrs = db.JSONField()
	elementTypes = attributes.attribute("element_types", dict, {})
	connectionTypes = attributes.attribute("connection_types", dict, {})
	hostInfo = attributes.attribute("info", dict, {})
	hostInfoTimestamp = attributes.attribute("info_timestamp", float, 0.0)
	hostNetworks = attributes.attribute("networks", list, {})
	accountingTimestamp = attributes.attribute("accounting_timestamp", float, 0.0)
	lastResourcesSync = attributes.attribute("last_resources_sync", float, 0.0)
	enabled = attributes.attribute("enabled", bool, True)
	componentErrors = attributes.attribute("componentErrors", int, 0)
	problemAge = attributes.attribute("problem_age", float, 0)
	problemMailTime = attributes.attribute("problem_mail_time", float, 0)
	availability = attributes.attribute("availability", float, 1.0)
	description_text = attributes.attribute("description_text", unicode, "")
	dump_last_fetch = attributes.attribute("dump_last_fetch", float, 0)
	# connections: [HostConnection]
	# elements: [HostElement]
	# templates: [TemplateOnHost]

	class Meta:
		ordering = ['site', 'name']

	def init(self, attrs=None):
		self.attrs = {}
		self.totalUsage = UsageStatistics.objects.create()
		if attrs:
			self.modify(attrs)
		self.update()

	def _saveAttributes(self):
		pass  # disable automatic attribute saving

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
		hel = HostElement(host=self, num=el["id"], topology_element=ownerElement, topology_connection=ownerConnection)
		hel.usageStatistics = UsageStatistics.objects.create()
		hel.attrs = el
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
		hcon = HostConnection(host=self, num=con["id"], topology_element=ownerElement,
							  topology_connection=ownerConnection)
		hcon.usageStatistics = UsageStatistics.objects.create()
		hcon.attrs = con
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
		from models import TemplateOnHost

		logging.logMessage("resource_sync begin", category="host", name=self.name)
		# TODO: implement for other resources
		from . import resources

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

	def modify(self, attrs):
		UserError.check(self.checkPermissions(), code=UserError.DENIED, message="Not enough permissions")
		logging.logMessage("modify", category="host", name=self.name, attrs=attrs)
		for key, value in attrs.iteritems():
			if key == "site":
				self.site = getSite(value)
			elif key == "address":
				self.address = value
			elif key == "rpcurl":
				self.rpcurl = value
			elif key == "name":
				self.name = value
			elif key == "enabled":
				self.enabled = value
			elif key == "description_text":
				self.description_text = value
			else:
				raise UserError(code=UserError.UNSUPPORTED_ATTRIBUTE, message="Unknown host attribute",
					data={"attribute": key})
		self.save()

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

	def info(self):
		return {
			"name": self.name,
			"address": self.address,
			"rpcurl": self.rpcurl,
			"site": self.site.name,
			"organization": self.site.organization.name,
			"enabled": self.enabled,
			"problems": self.problems(),
			"component_errors": self.componentErrors,
			"load": self.getLoad(),
			"element_types": self.elementTypes.keys(),
			"connection_types": self.connectionTypes.keys(),
			"host_info": self.hostInfo.copy() if self.hostInfo else None,
			"host_info_timestamp": self.hostInfoTimestamp,
			"availability": self.availability,
			"description_text": self.description_text,
			"networks": [n for n in self.hostNetworks] if self.hostNetworks else None
		}

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


class HostElement(attributes.Mixin, models.Model):
	host = models.ForeignKey(Host, null=False, related_name="elements")
	num = models.IntegerField(null=False)  # not id, since this is reserved
	topology_element = models.ForeignKey("tomato.Element", null=True, related_name="host_elements")
	topology_connection = models.ForeignKey("tomato.Connection", null=True, related_name="host_elements")
	usageStatistics = models.OneToOneField(UsageStatistics, null=True, related_name='+', on_delete=models.SET_NULL)
	attrs = db.JSONField()
	connection = attributes.attribute("connection", int)
	state = attributes.attribute("state", str)
	type = attributes.attribute("type", str)  # @ReservedAssignment

	class Meta:
		unique_together = (("host", "num"),)

	def createChild(self, type_, attrs=None, ownerConnection=None, ownerElement=None):
		if not attrs: attrs = {}
		return self.host.createElement(type_, self, attrs, ownerConnection=ownerConnection, ownerElement=ownerElement)

	def connectWith(self, hel, type_=None, attrs=None, ownerConnection=None, ownerElement=None):
		if not attrs: attrs = {}
		return self.host.createConnection(self, hel, type_, attrs, ownerConnection=ownerConnection,
										  ownerElement=ownerElement)

	def modify(self, attrs):
		logging.logMessage("element_modify", category="host", host=self.host.name, id=self.num, attrs=attrs)
		try:
			self.attrs = self.host.getProxy().element_modify(self.num, attrs)
		except error.UserError, err:
			if err.code == error.UserError.ENTITY_DOES_NOT_EXIST:
				logging.logMessage("missing element", category="host", host=self.host.name, id=self.num)
				self.remove()
			if err.code == error.UserError.INVALID_STATE:
				self.updateInfo()
			raise
		except:
			self.host.incrementErrors()
			raise
		logging.logMessage("element_info", category="host", host=self.host.name, id=self.num, info=self.attrs)
		self.save()

	def action(self, action, params=None):
		if not params: params = {}
		logging.logMessage("element_action begin", category="host", host=self.host.name, id=self.num, action=action,
						   params=params)
		try:
			res = self.host.getProxy().element_action(self.num, action, params)
		except error.UserError, err:
			if err.code == error.UserError.ENTITY_DOES_NOT_EXIST:
				logging.logMessage("missing element", category="host", host=self.host.name, id=self.num)
				self.remove()
			if err.code == error.UserError.INVALID_STATE:
				self.updateInfo()
			raise
		except:
			self.host.incrementErrors()
			raise
		logging.logMessage("element_action end", category="host", host=self.host.name, id=self.num, action=action,
						   params=params, result=res)
		self.updateInfo()
		return res

	def remove(self):
		try:
			logging.logMessage("element_remove", category="host", host=self.host.name, id=self.num)
			self.host.getProxy().element_remove(self.num)
		except error.UserError, err:
			if err.code != error.UserError.ENTITY_DOES_NOT_EXIST:
				self.host.incrementErrors()
		except:
			self.host.incrementErrors()
		self.usageStatistics.delete()
		self.delete()

	def getConnection(self):
		return self.host.getConnection(self.connection) if self.connection else None

	def updateInfo(self):
		try:
			self.attrs = self.host.getProxy().element_info(self.num)
		except error.UserError, err:
			if err.code == error.UserError.ENTITY_DOES_NOT_EXIST:
				logging.logMessage("missing element", category="host", host=self.host.name, id=self.num)
				self.remove()
			raise
		except:
			self.host.incrementErrors()
			raise
		logging.logMessage("element_info", category="host", host=self.host.name, id=self.num, info=self.attrs)
		self.save()

	def info(self):
		return self.attrs

	def getAttrs(self):
		return self.attrs["attrs"]

	def getAllowedActions(self):
		try:
			caps = self.host.getElementCapabilities(self.type)["actions"]
			res = []
			for key, states in caps.iteritems():
				if self.state in states:
					res.append(key)
			return res
		except:
			self.host.incrementErrors()
			logging.logException(host=self.host.name)
			return []

	def getAllowedAttributes(self):
		caps = self.host.getElementCapabilities(self.type)["attrs"]
		ret = dict(filter(lambda attr: not "states" in attr[1] or self.state in attr[1]["states"], caps.iteritems()))
		return ret

	def updateAccountingData(self, data):
		self.usageStatistics.importRecords(data)
		self.usageStatistics.removeOld()

	def synchronize(self):
		try:
			if not self.topology_element and not self.topology_connection:
				self.remove()
				return
			self.modify({"timeout": time.time() + 14 * 24 * 60 * 60})
		except error.UserError, err:
			if err.code != error.UserError.UNSUPPORTED_ATTRIBUTE:
				raise
		except:
			logging.logException(host=self.host.address)


class HostConnection(attributes.Mixin, models.Model):
	host = models.ForeignKey(Host, null=False, related_name="connections")
	num = models.IntegerField(null=False)  # not id, since this is reserved
	topology_element = models.ForeignKey("tomato.Element", null=True, related_name="host_connections")
	topology_connection = models.ForeignKey("tomato.Connection", null=True, related_name="host_connections")
	usageStatistics = models.OneToOneField(UsageStatistics, null=True, related_name='+', on_delete=models.SET_NULL)
	attrs = db.JSONField()
	elements = attributes.attribute("elements", list)
	state = attributes.attribute("state", str)
	type = attributes.attribute("type", str)  # @ReservedAssignment

	class Meta:
		unique_together = (("host", "num"),)

	def modify(self, attrs):
		logging.logMessage("connection_modify", category="host", host=self.host.name, id=self.num, attrs=attrs)
		try:
			self.attrs = self.host.getProxy().connection_modify(self.num, attrs)
		except error.UserError, err:
			if err.code == error.UserError.ENTITY_DOES_NOT_EXIST:
				logging.logMessage("missing connection", category="host", host=self.host.name, id=self.num)
				self.remove()
			if err.code == error.UserError.INVALID_STATE:
				self.updateInfo()
			raise
		except:
			self.host.incrementErrors()
			raise
		logging.logMessage("connection_info", category="host", host=self.host.name, id=self.num, info=self.attrs)
		self.save()

	def action(self, action, params=None):
		if not params: params = {}
		logging.logMessage("connection_action begin", category="host", host=self.host.name, id=self.num, action=action,
						   params=params)
		try:
			res = self.host.getProxy().connection_action(self.num, action, params)
		except error.UserError, err:
			if err.code == error.UserError.ENTITY_DOES_NOT_EXIST:
				logging.logMessage("missing connection", category="host", host=self.host.name, id=self.num)
				self.remove()
			if err.code == error.UserError.INVALID_STATE:
				self.updateInfo()
			raise
		except:
			self.host.incrementErrors()
			raise
		logging.logMessage("connection_action begin", category="host", host=self.host.name, id=self.num, action=action,
						   params=params, result=res)
		self.updateInfo()
		return res

	def remove(self):
		try:
			logging.logMessage("connection_remove", category="host", host=self.host.name, id=self.num)
			self.host.getProxy().connection_remove(self.num)
		except error.UserError, err:
			if err.code != error.UserError.ENTITY_DOES_NOT_EXIST:
				self.host.incrementErrors()
		except:
			self.host.incrementErrors()
		self.usageStatistics.delete()
		self.delete()

	def getElements(self):
		return [self.host.getElement(el) for el in self.elements]

	def updateInfo(self):
		try:
			self.attrs = self.host.getProxy().connection_info(self.num)
			self.state = self.attrs["state"]
		except error.UserError, err:
			if err.code == error.UserError.ENTITY_DOES_NOT_EXIST:
				logging.logMessage("missing connection", category="host", host=self.host.name, id=self.num)
				self.remove()
			raise
		except:
			self.host.incrementErrors()
			raise
		logging.logMessage("connection_info", category="host", host=self.host.name, id=self.num, info=self.attrs)
		self.save()

	def info(self):
		return self.attrs

	def getAttrs(self):
		return self.attrs["attrs"]

	def getAllowedActions(self):
		caps = self.host.getConnectionCapabilities(self.type)["actions"]
		res = []
		for key, states in caps.iteritems():
			if self.state in states:
				res.append(key)
		return res

	def getAllowedAttributes(self):
		caps = self.host.getConnectionCapabilities(self.type)["attrs"]
		return dict(filter(lambda attr: not "states" in attr[1] or self.state in attr[1]["states"], caps.iteritems()))

	def updateAccountingData(self, data):
		self.usageStatistics.importRecords(data)
		self.usageStatistics.removeOld()

	def synchronize(self):
		try:
			if not self.topology_element and not self.topology_connection:
				self.remove()
				return
			self.updateInfo()
		except:
			logging.logException(host=self.host.name)


def get(**kwargs):
	try:
		return Host.objects.get(**kwargs)
	except Host.DoesNotExist:
		return None


def getAll(**kwargs):
	return list(Host.objects.filter(**kwargs))


def create(name, site, attrs=None):
	if not attrs: attrs = {}
	user = currentUser()
	UserError.check(user.hasFlag(Flags.GlobalHostManager) or user.hasFlag(Flags.OrgaHostManager) and user.organization == site.organization,
		code=UserError.DENIED, message="Not enough permissions")
	for attr in ["address", "rpcurl"]:
		UserError.check(attr in attrs.keys(), code=UserError.INVALID_CONFIGURATION, message="Missing attribute for host: %s" % attr)
	host = Host(name=name, site=site)
	host.init(attrs)
	host.save()
	logging.logMessage("create", category="host", info=host.info())
	return host


def select(site=None, elementTypes=None, connectionTypes=None, networkKinds=None, hostPrefs=None, sitePrefs=None):
	# STEP 1: limit host choices to what is possible
	if not sitePrefs: sitePrefs = {}
	if not hostPrefs: hostPrefs = {}
	if not networkKinds: networkKinds = []
	if not connectionTypes: connectionTypes = []
	if not elementTypes: elementTypes = []
	all_ = getAll(site=site) if site else getAll()
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
	for h in getAll():
		types += set(h.elementTypes.keys())
	return types


@cached(timeout=3600, autoupdate=True)
def getElementCapabilities(type_):
	# FIXME: merge capabilities
	caps = {}
	for h in getAll():
		hcaps = h.getElementCapabilities(type_)
		if len(repr(hcaps)) > len(repr(caps)):
			caps = hcaps
	return caps


@cached(timeout=3600, autoupdate=True)
def getConnectionTypes():
	types = set()
	for h in getAll():
		types += set(h.connectionTypes.keys())
	return types


@cached(timeout=3600, autoupdate=True)
def getConnectionCapabilities(type_):
	# FIXME: merge capabilities
	caps = {}
	for h in getAll():
		hcaps = h.getConnectionCapabilities(type_)
		if len(repr(hcaps)) > len(repr(caps)):
			caps = hcaps
	return caps


checkingHostsLock = threading.RLock()
checkingHosts = set()


@util.wrap_task
@db.commit_after
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
	for host in getAll():
		if host.enabled:
			scheduler.scheduleOnce(0, synchronizeHost, host)  # @UndefinedVariable


@util.wrap_task
def synchronizeComponents():
	for hel in HostElement.objects.all():
		hel.synchronize()
	for hcon in HostConnection.objects.all():
		hcon.synchronize()


scheduler.scheduleRepeated(config.HOST_UPDATE_INTERVAL, synchronize)  # @UndefinedVariable
scheduler.scheduleRepeated(3600, synchronizeComponents)  # @UndefinedVariable