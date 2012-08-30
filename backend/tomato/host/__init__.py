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
from tomato import config
from tomato.lib import attributes, db, rpc, util #@UnresolvedImport
import xmlrpclib, base64

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
    return Site.objects.create(name=name, description=description)


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
    
    class Meta:
        pass

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
        self.hostInfo = self._info()
        caps = self._capabilities()
        self.elementTypes = caps["elements"]
        self.connectionTypes = caps["connections"]
        self.save()
        
    def _capabilities(self):
        return self.getProxy().host_capabilities()
        
    def _info(self):
        return self.getProxy().host_info()
        
    def getElementCapabilities(self, type_):
        return self.elementTypes.get(type_)
        
    def getConnectionCapabilities(self, type_):
        return self.connectionTypes.get(type_)

    def createElement(self, type_, parent=None, attrs={}):
        assert not parent or parent.host == self
        el = self.getProxy().element_create(type_, parent.num if parent else None, attrs)
        hel = HostElement(host=self, num=el["id"])
        hel.attrs = el
        hel.save()
        return hel

    def getElement(self, num):
        return self.elements.get(num=num)

    def createConnection(self, hel1, hel2, type_=None, attrs={}):
        assert hel1.host == self
        assert hel2.host == self
        con = self.getProxy().connection_create(hel1.num, hel2.num, type_, attrs)
        hcon = HostConnection(host=self, num=con["id"])
        hcon.attrs = con
        return hcon

    def getConnection(self, num):
        return self.connections.get(num=num)

    def grantUrl(self, grant, action):
        return "http://%s:%d/%s/%s" % (self.address, self.hostInfo["fileserver_port"], grant, action)
    
    def synchronizeResources(self):
        #TODO: implement for other resources
        from tomato import resources
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
            else:
                hTpl = hostTpls[key]
                #update resource
                self.getProxy().resource_modify(hTpl["id"], attrs)
    
    def info(self):
        return {
            "id": self.id,
            "address": self.address,
            "site": self.site.name,
            "element_types": self.elementTypes.keys(),
            "connection_types": self.connectionTypes.keys(),
            "host_info": self.hostInfo
        }


class HostElement(attributes.Mixin, models.Model):
    host = models.ForeignKey(Host, null=False, related_name="elements")
    num = models.IntegerField(null=False) #not id, since this is reserved
    attrs = db.JSONField()
    connection = attributes.attribute("connection", int)
    state = attributes.attribute("state", str)
    type = attributes.attribute("type", str) #@ReservedAssignment
        
    class Meta:
        unique_together = (("host", "num"),)

    def createChild(self, type_, attrs={}):
        return self.host.createElement(type_, self, attrs)

    def modify(self, attrs):
        self.attrs = self.host.getProxy().element_modify(self.num, attrs)
        self.save()
            
    def action(self, action, params={}):
        res = self.host.getProxy().element_action(self.num, action, params)
        self.updateInfo()
        return res
            
    def remove(self):
        try:
            self.host.getProxy().element_remove(self.num)
        except xmlrpclib.Fault, f:
            if f.faultCode != fault.UNKNOWN_OBJECT:
                raise
        self.delete()

    def getConnection(self):
        return self.host.getConnection(self.connection) if self.connection else None

    def updateInfo(self):
        self.attrs = self.host.getProxy().element_info(self.num)
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
        res = []
        for key, states in caps.iteritems():
            if self.state in states:
                res.append(key)
        return res
        
class HostConnection(attributes.Mixin, models.Model):
    host = models.ForeignKey(Host, null=False, related_name="connections")
    num = models.IntegerField(null=False) #not id, since this is reserved
    attrs = db.JSONField()
    elements = attributes.attribute("elements", list)
    state = attributes.attribute("state", str)
    type = attributes.attribute("type", str) #@ReservedAssignment
    
    class Meta:
        unique_together = (("host", "num"),)

    def modify(self, attrs):
        self.attrs = self.host.getProxy().connection_modify(self.num, attrs)
        self.save()
            
    def action(self, action, params={}):
        res = self.host.getProxy().connection_action(self.num, action, params)
        self.updateInfo()
        return res
            
    def remove(self):
        try:
            self.host.getProxy().connection_remove(self.num)
        except xmlrpclib.Fault, f:
            if f.faultCode != fault.UNKNOWN_OBJECT:
                raise
        self.delete()
        
    def getElements(self):
        return [self.host.getElement(el) for el in self.elements]

    def updateInfo(self):
        self.attrs = self.host.getProxy().connection_info(self.num)
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
        res = []
        for key, states in caps.iteritems():
            if self.state in states:
                res.append(key)
        return res
  
def get(id_, **kwargs):
    try:
        return Host.objects.get(id=id_, **kwargs)
    except Host.DoesNotExist:
        return None

def getAll(**kwargs):
    return list(Host.objects.filter(**kwargs))
    
def create(address, site, attrs={}):
    host = Host(address=address, site=site)
    host.init(attrs)
    host.save()
    return host

def select(site=None, elementTypes=[], connectionTypes=[]):
    all_ = getAll(site=site) if site else getAll()
    for host in all_:
        if set(elementTypes) - set(host.elementTypes.keys()):
            continue
        if set(connectionTypes) - set(host.connectionTypes.keys()):
            continue
        return host

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
            host.synchronizeResources()
        except:
            pass #needs admin permissions that might lack 

task = util.RepeatedTimer(1800, synchronize) #every 30 mins

from tomato import fault