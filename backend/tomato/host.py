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
from tomato import config, currentUser
from accounting import UsageStatistics
from tomato.lib import attributes, db, rpc, util, logging #@UnresolvedImport
from tomato.auth import Flags
import xmlrpclib, time

class Site(attributes.Mixin, models.Model):
    name = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=255)
    #hosts: [Host]
    
    class Meta:
        pass

    def info(self):
        return {
            "name": self.name,
            "description": self.description
        }

def getSite(name, **kwargs):
    try:
        return Site.objects.get(name=name, **kwargs)
    except Site.DoesNotExist:
        return None

def getAllSites(**kwargs):
    return list(Site.objects.filter(**kwargs))
    
def createSite(name, description=""):
    fault.check(currentUser().hasFlag(Flags.HostsManager), "Not enough permissions")
    logging.logMessage("create", category="site", name=name, description=description)        
    return Site.objects.create(name=name, description=description)

def removeSite(site):
    fault.check(currentUser().hasFlag(Flags.HostsManager), "Not enough permissions")
    fault.check(not site.hosts.all(), "Site still has hosts")
    logging.logMessage("remove", category="site", name=site.name)
    site.delete()

def _connect(address, port):
    transport = rpc.SafeTransportWithCerts(config.CERTIFICATE, config.CERTIFICATE)
    return rpc.ServerProxy('https://%s:%d' % (address, port), allow_none=True, transport=transport)


class Host(attributes.Mixin, models.Model):
    address = models.CharField(max_length=255, unique=True)
    site = models.ForeignKey(Site, null=False, related_name="hosts")
    attrs = db.JSONField()
    port = attributes.attribute("port", int, 8000)
    elementTypes = attributes.attribute("element_types", dict, {})
    connectionTypes = attributes.attribute("connection_types", dict, {})
    hostInfo = attributes.attribute("info", dict, {})
    hostInfoTimestamp = attributes.attribute("info_timestamp", float, 0.0)
    accountingTimestamp = attributes.attribute("accounting_timestamp", float, 0.0)
    
    class Meta:
        ordering = ['site', 'address']

    def init(self, attrs={}):
        self.attrs = attrs
        self.update()

    def _saveAttributes(self):
        pass #disable automatic attribute saving

    def getProxy(self):
        if not hasattr(self, "_proxy"):
            self._proxy = _connect(self.address, self.port)
        return self._proxy
        
    def update(self):
        before = time.time()
        self.hostInfo = self._info()
        after = time.time()
        self.hostInfoTimestamp = (before+after)/2.0
        self.hostInfo["query_time"] = after - before
        self.hostInfo["time_diff"] = self.hostInfo["time"] - self.hostInfoTimestamp
        caps = self._capabilities()
        self.elementTypes = caps["elements"]
        self.connectionTypes = caps["connections"]
        self.save()
        logging.logMessage("info", category="host", address=self.address, info=self.hostInfo)        
        logging.logMessage("capabilities", category="host", address=self.address, capabilities=caps)        
        
    def _capabilities(self):
        return self.getProxy().host_capabilities()
        
    def _info(self):
        return self.getProxy().host_info()
        
    def getElementCapabilities(self, type_):
        return self.elementTypes.get(type_)
        
    def getConnectionCapabilities(self, type_):
        return self.connectionTypes.get(type_)

    def createElement(self, type_, parent=None, attrs={}, owner=None):
        assert not parent or parent.host == self
        el = self.getProxy().element_create(type_, parent.num if parent else None, attrs)
        hel = HostElement(host=self, num=el["id"])
        hel.usageStatistics = UsageStatistics.objects.create()
        hel.attrs = el
        hel.save()
        logging.logMessage("element_create", category="host", host=self.address, element=el, owner=(owner.__class__.__name__.lower(), owner.id) if owner else None)        
        return hel

    def getElement(self, num):
        return self.elements.get(num=num)

    def createConnection(self, hel1, hel2, type_=None, attrs={}, owner=None):
        assert hel1.host == self
        assert hel2.host == self
        con = self.getProxy().connection_create(hel1.num, hel2.num, type_, attrs)
        hcon = HostConnection(host=self, num=con["id"])
        hcon.usageStatistics = UsageStatistics.objects.create()
        hcon.attrs = con
        hcon.save()
        logging.logMessage("connection_create", category="host", host=self.address, element=con, owner=(owner.__class__.__name__.lower(), owner.id) if owner else None)        
        return hcon

    def getConnection(self, num):
        return self.connections.get(num=num)

    def grantUrl(self, grant, action):
        return "http://%s:%d/%s/%s" % (self.address, self.hostInfo["fileserver_port"], grant, action)
    
    def synchronizeResources(self):
        logging.logMessage("resource_sync begin", category="host", address=self.address)        
        #TODO: implement for other resources
        from tomato import resources
        hostNets = {}
        for net in self.getProxy().resource_list("network"):
            hostNets[(net["attrs"]["kind"], net["attrs"]["bridge"])] = net
        for net in self.networks.all():
            key = (net.getKind(), net.bridge)
            attrs = net.attrs.copy()
            attrs["bridge"] = net.bridge
            attrs["kind"] = net.getKind()
            attrs["preference"] = net.network.preference
            if not key in hostNets:
                #create resource
                self.getProxy().resource_create("network", attrs)
                logging.logMessage("network create", category="host", address=self.address, network=attrs)        
            else:
                hNet = hostNets[key]
                if hNet["attrs"] != attrs:
                    #update resource
                    self.getProxy().resource_modify(hNet["id"], attrs)
                    logging.logMessage("network update", category="host", address=self.address, network=attrs)                
        hostTpls = {}
        for tpl in self.getProxy().resource_list("template"):
            hostTpls[(tpl["attrs"]["tech"], tpl["attrs"]["name"])] = tpl
        for tpl in resources.getAll(type="template"):
            key = (tpl.tech, tpl.name)
            attrs = tpl.attrs.copy()
            attrs["name"] = tpl.name
            attrs["tech"] = tpl.tech
            if not key in hostTpls:
                #create resource
                self.getProxy().resource_create("template", attrs)
                logging.logMessage("template create", category="host", address=self.address, template=attrs)        
            else:
                hTpl = hostTpls[key]
                if hTpl["attrs"] != tpl.info()["attrs"]:
                    #update resource
                    if hTpl["attrs"]["torrent_data_hash"] == tpl.info()["attrs"]["torrent_data_hash"]:
                        #only send torrent data when needed
                        del attrs["torrent_data"]
                    self.getProxy().resource_modify(hTpl["id"], attrs)
                    logging.logMessage("template update", category="host", address=self.address, template=attrs)        
        logging.logMessage("resource_sync end", category="host", address=self.address)        

    def updateAccountingData(self, now):
        logging.logMessage("accounting_sync begin", category="host", address=self.address)        
        data = self.getProxy().accounting_statistics(type="5minutes", after=self.accountingTimestamp-900)
        for el in self.elements.all():
            if not el.usageStatistics:
                el.usageStatistics = UsageStatistics.objects.create()
                el.save()
            if not str(el.num) in data["elements"]:
                print "Missing accounting data for element #%d on host %s" % (el.num, self.address)
                continue
            logging.logMessage("host_records", category="accounting", host=self.address, records=data["elements"][str(el.num)], object=("element", el.id))        
            el.updateAccountingData(data["elements"][str(el.num)])
        for con in self.connections.all():
            if not con.usageStatistics:
                con.usageStatistics = UsageStatistics.objects.create()
                con.save()
            if not str(con.num) in data["connections"]:
                print "Missing accounting data for connection #%d on host %s" % (con.num, self.address)
                continue
            logging.logMessage("host_records", category="accounting", host=self.address, records=data["connections"][str(con.num)], object=("connection", con.id))        
            con.updateAccountingData(data["connections"][str(con.num)])
        self.accountingTimestamp=now
        self.save()
        logging.logMessage("accounting_sync end", category="host", address=self.address)        
    
    def getNetworkKinds(self):
        return [net.getKind() for net in self.networks.all()]
    
    def info(self):
        return {
            "address": self.address,
            "site": self.site.name,
            "element_types": self.elementTypes.keys(),
            "connection_types": self.connectionTypes.keys(),
            "host_info": self.hostInfo.copy() if self.hostInfo else None,
            "host_info_timestamp": self.hostInfoTimestamp,
        }


class HostElement(attributes.Mixin, models.Model):
    host = models.ForeignKey(Host, null=False, related_name="elements")
    num = models.IntegerField(null=False) #not id, since this is reserved
    usageStatistics = models.OneToOneField(UsageStatistics, null=True, related_name='+')
    attrs = db.JSONField()
    connection = attributes.attribute("connection", int)
    state = attributes.attribute("state", str)
    type = attributes.attribute("type", str) #@ReservedAssignment
        
    class Meta:
        unique_together = (("host", "num"),)

    def createChild(self, type_, attrs={}, owner=None):
        return self.host.createElement(type_, self, attrs, owner=owner)

    def connectWith(self, hel, type_=None, attrs={}, owner=None):
        return self.host.createConnection(self, hel, type_, attrs, owner=owner)

    def modify(self, attrs):
        logging.logMessage("element_modify", category="host", host=self.host.address, id=self.num, attrs=attrs)        
        self.attrs = self.host.getProxy().element_modify(self.num, attrs)
        logging.logMessage("element_info", category="host", host=self.host.address, id=self.num, info=self.attrs)        
        self.save()
            
    def action(self, action, params={}):
        logging.logMessage("element_action begin", category="host", host=self.host.address, id=self.num, action=action, params=params)        
        res = self.host.getProxy().element_action(self.num, action, params)
        logging.logMessage("element_action end", category="host", host=self.host.address, id=self.num, action=action, params=params, result=res)        
        self.updateInfo()
        return res
            
    def remove(self):
        try:
            logging.logMessage("element_remove", category="host", host=self.host.address, id=self.num)        
            self.host.getProxy().element_remove(self.num)
        except xmlrpclib.Fault, f:
            if f.faultCode != fault.UNKNOWN_OBJECT:
                raise
        self.usageStatistics.delete()
        self.delete()

    def getConnection(self):
        return self.host.getConnection(self.connection) if self.connection else None

    def updateInfo(self):
        self.attrs = self.host.getProxy().element_info(self.num)
        logging.logMessage("element_info", category="host", host=self.host.address, id=self.num, info=self.attrs)        
        self.save()
        
    def info(self):
        return self.attrs

    def getAttrs(self):
        return self.attrs["attrs"]

    def getAllowedActions(self):
        caps = self.host.getElementCapabilities(self.type)["actions"]
        res = []
        for key, states in caps.iteritems():
            if self.state in states:
                res.append(key)
        return res

    def getAllowedAttributes(self):
        caps = self.host.getElementCapabilities(self.type)["attrs"]
        ret = dict(filter(lambda attr: not "states" in attr[1] or self.state in attr[1]["states"], caps.iteritems()))
        return ret
    
    def updateAccountingData(self, data):
        self.usageStatistics.importRecords(data)
        self.usageStatistics.removeOld()
        
    def getOwner(self):
        from tomato import elements, connections
        for el in elements.getAll():
            if self in el.getHostElements():
                return ("element", el.id)
        for con in connections.getAll():
            if self in el.getHostElements():
                return ("connection", con.id)
        return (None, None)

        
class HostConnection(attributes.Mixin, models.Model):
    host = models.ForeignKey(Host, null=False, related_name="connections")
    num = models.IntegerField(null=False) #not id, since this is reserved
    usageStatistics = models.OneToOneField(UsageStatistics, null=True, related_name='+')
    attrs = db.JSONField()
    elements = attributes.attribute("elements", list)
    state = attributes.attribute("state", str)
    type = attributes.attribute("type", str) #@ReservedAssignment
    
    class Meta:
        unique_together = (("host", "num"),)

    def modify(self, attrs):
        logging.logMessage("connection_modify", category="host", host=self.host.address, id=self.num, attrs=attrs)        
        self.attrs = self.host.getProxy().connection_modify(self.num, attrs)
        logging.logMessage("connection_info", category="host", host=self.host.address, id=self.num, info=self.attrs)        
        self.save()
            
    def action(self, action, params={}):
        logging.logMessage("connection_action begin", category="host", host=self.host.address, id=self.num, action=action, params=params)        
        res = self.host.getProxy().connection_action(self.num, action, params)
        logging.logMessage("connection_action begin", category="host", host=self.host.address, id=self.num, action=action, params=params, result=res)        
        self.updateInfo()
        return res
            
    def remove(self):
        try:
            logging.logMessage("connection_remove", category="host", host=self.host.address, id=self.num)        
            self.host.getProxy().connection_remove(self.num)
        except xmlrpclib.Fault, f:
            if f.faultCode != fault.UNKNOWN_OBJECT:
                raise
        self.usageStatistics.delete()
        self.delete()
        
    def getElements(self):
        return [self.host.getElement(el) for el in self.elements]

    def updateInfo(self):
        self.attrs = self.host.getProxy().connection_info(self.num)
        logging.logMessage("connection_info", category="host", host=self.host.address, id=self.num, info=self.attrs)        
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

    def getOwner(self):
        from tomato import elements, connections
        for el in elements.getAll():
            if self in el.getHostConnections():
                return ("element", el.id)
        for con in connections.getAll():
            if self in el.getHostConnections():
                return ("connection", con.id)
        return (None, None)


def get(**kwargs):
    try:
        return Host.objects.get(**kwargs)
    except Host.DoesNotExist:
        return None

def getAll(**kwargs):
    return list(Host.objects.filter(**kwargs))
    
def create(address, site, attrs={}):
    fault.check(currentUser().hasFlag(Flags.HostsManager), "Not enough permissions")
    host = Host(address=address, site=site)
    host.init(attrs)
    host.save()
    logging.logMessage("create", category="host", info=host.info())        
    return host

def select(site=None, elementTypes=[], connectionTypes=[], networkKinds=[]):
    all_ = getAll(site=site) if site else getAll()
    for host in all_:
        if set(elementTypes) - set(host.elementTypes.keys()):
            continue
        if set(connectionTypes) - set(host.connectionTypes.keys()):
            continue
        if set(networkKinds) - set(host.getNetworkKinds()):
            continue #FIXME: allow general networks
        logging.logMessage("select", category="host", result=host.address, site=site, element_types=elementTypes, connection_types=connectionTypes)
        return host
    logging.logMessage("select", category="host", result=None, site=site, element_types=elementTypes, connection_types=connectionTypes)

def getElementTypes():
    types = set()
    for h in getAll():
        types += set(h.elementTypes.keys())
    return types

def getElementCapabilities(type_):
    #FIXME: merge capabilities
    caps = {}
    for h in getAll():
        hcaps = h.getElementCapabilities(type_)
        if len(repr(hcaps)) > len(repr(caps)):
            caps = hcaps
    return caps
    
def getConnectionTypes():
    types = set()
    for h in getAll():
        types += set(h.connectionTypes.keys())
    return types

def getConnectionCapabilities(type_):
    #FIXME: merge capabilities
    caps = {}
    for h in getAll():
        hcaps = h.getConnectionCapabilities(type_)
        if len(repr(hcaps)) > len(repr(caps)):
            caps = hcaps
    return caps

def synchronize():
    #TODO: implement more than resource sync
    for host in getAll():
        try:
            host.update()
            host.synchronizeResources()
        except:
            import traceback
            traceback.print_exc()
            pass #needs admin permissions that might lack 

task = util.RepeatedTimer(600, synchronize) #every 10 mins

from tomato import fault