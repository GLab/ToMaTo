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
from ..lib.cmd import bittorrent, path #@UnresolvedImport
from ..lib.error import UserError, InternalError #@UnresolvedImport
import os, base64, hashlib

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
	torrent_data = attributes.attribute("torrent_data", str)  #encoded as base64
	kblang = attributes.attribute("kblang",str,null=False,default="en-us")

	@property
	def torrent_data_hash(self):
		return hashlib.md5(base64.b64decode(self.torrent_data)).hexdigest() if self.torrent_data else None

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
		resources.Resource.init(self, *args, **kwargs)
				
	def upcast(self):
		return self
	
	def getPath(self):
		hash = self.torrent_data_hash
		return os.path.join(config.TEMPLATE_DIR, PATTERNS[self.tech] % hash)
	
	def getTorrentPath(self):
		return self.getPath() + ".torrent"

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

	def modify_torrent_data(self, val):
		if val != self.torrent_data:
			if os.path.exists(self.getPath()):
				path.remove(self.getPath(), recursive=True)
			if os.path.exists(self.getTorrentPath()):
				path.remove(self.getTorrentPath())
		self.torrent_data = val
		if self.name and self.tech:
			with open(self.getTorrentPath(), "w") as fp:
				fp.write(base64.b64decode(val))

	def remove(self):
		if os.path.exists(self.getTorrentPath()):
			os.remove(self.getTorrentPath())
		if os.path.exists(self.getPath()):
			path.remove(self.getPath(), recursive=True)
		resources.Resource.remove(self)

	def isReady(self):
		try:
			if not os.path.exists(self.getTorrentPath()):
				self.torrent_data = ""
				self.save()
			path = self.getPath()
			size = os.path.getsize(path)
			bsize = bittorrent.fileSize(base64.b64decode(self.torrent_data))
			return size == bsize
		except:
			return False

	def info(self):
		info = resources.Resource.info(self)
		if self.torrent_data:
			del info["attrs"]["torrent_data"]
		info["attrs"]["ready"] = self.isReady()
		info["attrs"]["size"] = os.path.getsize(self.getPath()) if os.path.exists(self.getPath()) else 0
		info["attrs"]["name"] = self.name
		info["attrs"]["tech"] = self.tech
		info["attrs"]["preference"] = self.preference
		info["attrs"]["torrent_data_hash"] = self.torrent_data_hash
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