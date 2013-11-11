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
from .. import resources, fault, config
from ..lib import attributes #@UnresolvedImport
from ..lib.cmd import bittorrent, path #@UnresolvedImport
import os, base64, hashlib

PATTERNS = {
	"kvmqm": "%s.qcow2",
	"openvz": "%s.tar.gz",
	"repy": "%s.repy",
}

class Template(resources.Resource):
	tech = models.CharField(max_length=20)
	name = models.CharField(max_length=50)
	preference = models.IntegerField(default=0)
	torrent_data = attributes.attribute("torrent_data", str)
	
	TYPE = "template"

	class Meta:
		db_table = "tomato_template"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		attrs = args[0]
		for attr in ["name", "tech", "torrent_data"]:
			fault.check(attr in attrs, "Template needs attribute %s", attr) 
		resources.Resource.init(self, *args, **kwargs)
		self.modify_torrent_data(self.torrent_data) #might have been set before name or tech 
				
	def upcast(self):
		return self
	
	def getPath(self):
		return os.path.join(config.TEMPLATE_DIR, PATTERNS[self.tech] % self.name)
	
	def getTorrentPath(self):
		return self.getPath() + ".torrent"

	def modify_tech(self, val):
		fault.check(val in PATTERNS.keys(), "Unsupported template tech: %s", val)
		self.tech = val
	
	def modify_name(self, val):
		self.name = val

	def modify_preference(self, val):
		self.preference = val

	def modify_torrent_data(self, val):
		if val != self.torrent_data:
			if os.path.exists(self.getPath()):
				path.remove(self.getPath(), recursive=True)
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
		info["attrs"]["name"] = self.name
		info["attrs"]["tech"] = self.tech
		info["attrs"]["preference"] = self.preference
		info["attrs"]["torrent_data_hash"] = hashlib.md5(str(self.torrent_data)).hexdigest() if self.torrent_data else None
		return info

def get(tech, name):
	try:
		return Template.objects.get(tech=tech, name=name)
	except:
		return None
	
def getPreferred(tech):
	tmpls = Template.objects.filter(tech=tech).order_by("-preference")
	fault.check(tmpls, "No template of type %s registered", tech) 
	return tmpls[0]

resources.TYPES[Template.TYPE] = Template