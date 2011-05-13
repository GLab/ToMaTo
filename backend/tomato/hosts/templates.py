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

class Template(models.Model):
	name = models.CharField(max_length=100)
	type = models.CharField(max_length=12)
	default = models.BooleanField(default=False)
	download_url = models.CharField(max_length=255, default="")
		
	class Meta:
		db_table = "tomato_template"
		
	def init(self, name, ttype, download_url):
		import re
		if not re.match("^[a-zA-Z0-9_.]+-[a-zA-Z0-9_.]+$", name) or name.endswith(".tar.gz") or name.endswith(".qcow2"):
			raise fault.new(0, "Name must be in the format NAME-VERSION")
		self.name = name
		self.type = ttype
		self.download_url = download_url
		self.save()

	def setDefault(self):
		Template.objects.filter(type=self.type).update(default=False) # pylint: disable-msg=E1101
		self.default=True
		self.save()
		
	def getFilename(self):
		if self.type == "kvm":
			return "/var/lib/vz/template/qemu/%s.qcow2" % self.name
		if self.type == "openvz":
			return "/var/lib/vz/template/cache/%s.tar.gz" % self.name
	
	def uploadToHost(self, host):
		if host.clusterState() == ClusterState.NODE:
			return
		dst = self.getFilename()
		if self.download_url:
			host.execute("curl -o %(filename)s -sSR -z %(filename)s %(url)s" % {"url": self.download_url, "filename": dst})

	def __unicode__(self):
		return "Template(type=%s,name=%s,default=%s)" %(self.type, self.name, self.default)
			
	def toDict(self):
		"""
		Prepares a template for serialization.
			
		@return: a dict containing information about the template
		@rtype: dict
		"""
		return {"name": self.name, "type": self.type, "default": self.default, "url": self.download_url}

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

def get(ttype, name):
	return Template.objects.get(type=ttype, name=name) # pylint: disable-msg=E1101

def add(name, template_type, url):
	tpl = Template.objects.create(name=name, type=template_type, download_url=url) # pylint: disable-msg=E1101
	proc = tasks.Process("upload-template")
	for host in getAllHosts():
		proc.addTask(tasks.Task(host.name, fn=tpl.uploadToHost, args=(host,)))
	return proc.start()
	
def remove(template_type, name):
	Template.objects.filter(type=template_type, name=name).delete() # pylint: disable-msg=E1101
	
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