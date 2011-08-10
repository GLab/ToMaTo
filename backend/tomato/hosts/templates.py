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
from django.core import validators

import os

from tomato import attributes, config
from tomato.lib import db, fileutil, hostserver

hostServer = None
if config.TEMPLATE_HOSTSERVER:
	conf = config.TEMPLATE_HOSTSERVER
	hostServer = hostserver.HostServer(conf["HOST"], conf["PORT"], conf["BASEDIR"], conf["SECRET_KEY"])
	
class Template(attributes.Mixin, models.Model):
	name = models.CharField(max_length=100, validators=[db.templateValidator])
	type = models.CharField(max_length=12, validators=[db.nameValidator])
	default = models.BooleanField(default=False)
	attrs = db.JSONField(default={})
			
	def getDownloadUrl(self):
		if self.getAttribute("on_hostserver", False):
			return hostServer.downloadGrant(self.getFilename(), filename=self.getFilename()) 
		return self.getAttribute("external_url")
			
	def getUploadUrl(self):
		return hostServer.uploadGrant(self.getFilename()) 

	def setExternalUrl(self, url):
		self.setAttribute("external_url", url)			
		
	def isEnabled(self):
		return self.getAttribute("enabled", False)
			
	class Meta:
		db_table = "tomato_template"
		app_label = 'tomato'
		unique_together = (("name", "type"),)
		
	def init(self, name, ttype, external_url=None):
		import re
		fault.check(re.match("^[a-zA-Z0-9_.]+-[a-zA-Z0-9_.]+$", name), "Name must be in the format NAME-VERSION")
		fault.check(not name.endswith(".repy") and not name.endswith(".tar.gz") and not name.endswith(".qcow2"), "Name must not contain file extensions")
		self.name = name
		self.type = ttype
		if external_url:
			self.setExternalUrl(external_url)
		self.save()

	def setDefault(self):
		Template.objects.filter(type=self.type).update(default=False) # pylint: disable-msg=E1101
		self.default=True
		self.save()
		
	def getFileExt(self):
		return {"kvm": ".qcow2", "openvz": ".tar.gz", "prog": ".repy"}.get(self.type)
		
	def getFilename(self):
		return self.name + self.getFileExt()
	
	def getPath(self):
		dir = {"kvm": "qemu", "openvz": "cache", "prog": "repy"}.get(self.type)
		return "/var/lib/vz/template/%s/%s" % (dir, self.getFilename())
	
	def uploadTask(self):
		proc = tasks.Process("upload-template")
		for host in getAllHosts():
			proc.add(tasks.Task(host.name, fn=self.uploadToHost, args=(host,)))
		return proc.start()
	
	def uploadToHost(self, host):
		if not self.isEnabled():
			return
		if host.clusterState() == ClusterState.NODE:
			return
		dst = self.getPath()
		url = self.getDownloadUrl()
		if url:
			fileutil.mkdir(host, os.path.dirname(dst))
			host.execute("curl -o %(filename)s -sSR -z %(filename)s %(url)s" % {"url": url, "filename": dst})

	def configure(self, attributes):
		if "external_url" in attributes:
			self.setExternalUrl(attributes["external_url"])
		if "on_hostserver" in attributes:
			self.setAttribute("on_hostserver", attributes["on_hostserver"])
		if "enabled" in attributes:
			self.setAttribute("enabled", attributes["enabled"])
		if "notes" in attributes:
			self.setAttribute("notes", attributes["notes"])
		if self.isEnabled():
			return self.uploadTask()

	def __unicode__(self):
		return "Template(type=%s,name=%s,default=%s)" %(self.type, self.name, self.default)
			
	def toDict(self, auth=False):
		"""
		Prepares a template for serialization.
			
		@return: a dict containing information about the template
		@rtype: dict
		"""
		res = {"name": self.name, "type": self.type, "default": self.default,
			"external_url": self.getAttribute("external_url"),
			"on_hostserver": self.getAttribute("on_hostserver", False),
			"enabled": self.isEnabled(),
			"notes": self.getAttribute("notes", "")}
		if auth:
			res["download_url"] = self.getDownloadUrl()
			res["upload_url"] = self.getUploadUrl()
		return res

def getAll(ttype=None):
	tpls = Template.objects.all() # pylint: disable-msg=E1101
	if ttype:
		tpls = tpls.filter(type=ttype)
	return tpls

def findName(ttype, name):
	try:
		return Template.objects.get(type=ttype, name=name).name # pylint: disable-msg=E1101
	except: #pylint: disable-msg=W0702
		return getDefault(ttype)

def getMap(auth):
	map = {}
	for tpl in getAll():
		if not tpl.type in map:
			map[tpl.type] = []
		map[tpl.type].append(tpl.toDict(auth)) 
	return map

def get(ttype, name):
	return Template.objects.get(type=ttype, name=name) # pylint: disable-msg=E1101

def add(type, name, attributes):
	tpl = Template.objects.create(name=name, type=type) # pylint: disable-msg=E1101
	return tpl.configure(attributes)

def change(type, name, attributes):
	tpl = get(type, name)
	return tpl.configure(attributes)
	
def remove(type, name):
	#FIXME: actually delete hostserver file
	Template.objects.filter(type=type, name=name).delete() # pylint: disable-msg=E1101
	
def getDefault(ttype):
	tpls = Template.objects.filter(type=ttype, default=True) # pylint: disable-msg=E1101
	if tpls.count() >= 1:
		return tpls[0].name
	else:
		return None

# keep internal imports at the bottom to avoid dependency problems
from tomato.hosts import getAll as getAllHosts
from tomato import fault
from tomato.lib import tasks
from tomato.hosts import ClusterState