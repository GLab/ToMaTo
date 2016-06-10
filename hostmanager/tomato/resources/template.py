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
from .. import resources, config
from ..user import User
from ..lib import attributes #@UnresolvedImport
from ..lib.cmd import path #@UnresolvedImport
from ..lib.newcmd import aria2
from ..lib.newcmd.util import fs
from ..lib.error import UserError, InternalError #@UnresolvedImport
import os, threading

PATTERNS = {
	"kvmqm": "%s.qcow2",
	"openvz": "%s.tar.gz",
	"repy": "%s.repy",
}

class Template(resources.Resource):
	owner = models.ForeignKey(User, related_name='templates')
	tech = models.CharField(max_length=20)
	name = models.CharField(max_length=50)
	preference = models.IntegerField(default=0)
	urls = attributes.attribute("urls", list)
	checksum = attributes.attribute("checksum", str)
	size = attributes.attribute("size", long)
	popularity = attributes.attribute("popularity", float)
	ready = attributes.attribute("ready", bool)
	kblang = attributes.attribute("kblang",str,null=False,default="en-us")

	TYPE = "template"

	class Meta:
		db_table = "tomato_template"
		app_label = 'tomato'
		unique_together = (("tech", "name", "owner"))
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		attrs = args[0]
		for attr in ["name", "tech", "torrent_data"]:
			UserError.check(attr in attrs, UserError.INVALID_CONFIGURATION, "Attribute missing", data={"attribute": attr})
		self.modify_tech(attrs["tech"])
		self.modify_name(attrs["name"])
		self.ready = False
		resources.Resource.init(self, *args, **kwargs)

	def fetch(self, detached=False):
		if self.ready:
			return
		if detached:
			return threading.Thread(target=self.fetch).start()
		path = self.getPath()
		aria2.download(self.urls, path)
		self.size = fs.file_size(path)
		self.checksum = "sha1:%s" % fs.checksum(path, "sha1")
		self.save()

	def upcast(self):
		return self
	
	def getPath(self):
		hash = self.checksum.split(":")[1]
		return os.path.join(config.TEMPLATE_DIR, PATTERNS[self.tech] % hash)

	def modify_popularity(self, val):
		self.popularity = val

	def modify_checksum(self, val):
		if self.checksum != val:
			self.ready = False
		self.checksum = val

	def modify_urls(self, val):
		self.urls = val

	def modify_size(self, val):
		if self.size != val:
			self.ready = False
		self.size = val

	def modify_tech(self, val):
		UserError.check(val in PATTERNS.keys(), UserError.UNSUPPORTED_TYPE, "Unsupported template tech", data={"tech": val})
		self.tech = val
	
	def modify_name(self, val):
		self.name = val

	def modify_preference(self, val):
		self.preference = val
		
	def modify_kblang(self, val):
		from ..elements.kvmqm import kblang_options
		UserError.check(val in kblang_options, UserError.UNSUPPORTED_TYPE, "Unsupported value for kblang: %s" % val, data={"kblang":val})
		self.kblang = val

	def modify(self, attrs):
		res = resources.Resource.modify(self, attrs)
		self.fetch(detached=True)
		return res

	def remove(self):
		if os.path.exists(self.getPath()):
			path.remove(self.getPath(), recursive=True)
		resources.Resource.remove(self)

	def isReady(self):
		return os.path.exists(self.getPath())

	def info(self):
		info = resources.Resource.info(self)
		info["attrs"]["name"] = self.name
		info["attrs"]["tech"] = self.tech
		info["attrs"]["preference"] = self.preference
		info["attrs"]["kblang"] = self.kblang
		return info

def get(tech, name):
	try:
		return Template.objects.get(tech=tech, name=name, owner=currentUser())
	except:
		return None
	
def getPreferred(tech):
	tmpls = Template.objects.filter(tech=tech, owner=currentUser()).order_by("-preference")
	InternalError.check(tmpls, InternalError.CONFIGURATION_ERROR, "No template registered", data={"tech": tech})
	return tmpls[0]

resources.TYPES[Template.TYPE] = Template

from .. import currentUser