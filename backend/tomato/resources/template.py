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
from ..lib import attributes #@UnresolvedImport
from ..lib.cmd import bittorrent #@UnresolvedImport
from ..lib.error import UserError, InternalError #@UnresolvedImport
import os, os.path, base64, hashlib, shutil
from tomato import currentUser
from ..auth import Flags




kblang_options = {"en-us": "English (US)", 
					"en-gb": "English (GB)", 
					"de": "German", 
					"fr": "French", 
					"ja": "Japanese"
					}


PATTERNS = {
	"kvmqm": "%s.qcow2",
	"openvz": "%s.tar.gz",
	"repy": "%s.repy",
}

class Template(resources.Resource):
	tech = models.CharField(max_length=20)
	name = models.CharField(max_length=50)
	preference = models.IntegerField(default=0)
	label = attributes.attribute("label", str)
	subtype = attributes.attribute("subtype", str)
	torrent_data = attributes.attribute("torrent_data", str)
	restricted = attributes.attribute("restricted", bool)
	kblang = attributes.attribute("kblang",str,null=False,default="en-us")
	# hosts: [TemplateOnHost]
	
	TYPE = "template"

	class Meta:
		db_table = "tomato_template"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		attrs = args[0]
		for attr in ["name", "tech", "torrent_data"]:
			UserError.check(attr in attrs, code=UserError.INVALID_CONFIGURATION, message="Template needs attribute",
				data={"attribute": attr})
		if 'kblang' in attrs:
			kblang = attrs['kblang']
			del attrs['kblang']
		else:
			kblang=None
		resources.Resource.init(self, *args, **kwargs)
		if kblang:
			self.modify({'kblang':kblang})
		self.modify_torrent_data(self.torrent_data) #might have been set before name or tech 
				
	def upcast(self):
		return self
	
	def getPath(self):
		return os.path.join(config.TEMPLATE_PATH, PATTERNS[self.tech] % self.name)
	
	def getTorrentPath(self):
		return self.getPath() + ".torrent"

	def modify_name(self, val):
		self.name = val
		
	def modify_kblang(self, val):
		UserError.check(self.tech == "kvmqm", UserError.UNSUPPORTED_ATTRIBUTE, "Unsupported attribute for %s template: kblang" % (self.tech), data={"tech":self.tech,"attr_name":"kblang","attr_val":val})
		UserError.check(val in kblang_options, UserError.UNSUPPORTED_TYPE, "Unsupported value for kblang: %s" % val, data={"kblang":val})
		self.kblang = val

	def modify_tech(self, val):
		UserError.check(val in PATTERNS.keys(), code=UserError.INVALID_VALUE, message="Unsupported template tech", data={"value": val})
		self.tech = val
	
	def modify_preference(self, val):
		self.preference = val	
	
	def modify_torrent_data(self, val):
		raw = base64.b64decode(val)
		try:
			info = bittorrent.torrentInfo(raw)
		except:
			raise UserError(code=UserError.INVALID_VALUE, message="Invalid torrent file")
		UserError.check(not "files" in info or len(info["files"]) == 1, code=UserError.INVALID_VALUE,
			message="Torrent must contain exactly one file")
		self.torrent_data = val
		if self.name and self.tech:
			shouldName = PATTERNS[self.tech] % self.name
			UserError.check(info["name"] == shouldName, code=UserError.INVALID_VALUE,
				message="Torrent content must be named like the template", data={"expected_name": shouldName})
			with open(self.getTorrentPath(), "w") as fp:
				fp.write(raw)

	def remove(self):
		if self.tech and os.path.exists(self.getTorrentPath()):
			os.remove(self.getTorrentPath())
		if self.tech and os.path.exists(self.getPath()):
			if os.path.isdir(self.getPath()):
				shutil.rmtree(self.getPath())
			else:
				os.remove(self.getPath())
		resources.Resource.remove(self)

	def isReady(self):
		try:
			path = self.getPath()
			size = os.path.getsize(path)
			return size == bittorrent.fileSize(base64.b64decode(self.torrent_data))
		except:
			return False

	def info(self, include_torrent_data = False):
		info = resources.Resource.info(self)
		
		if include_torrent_data:
			if self.restricted:
				UserError.check(currentUser().hasFlag(Flags.RestrictedTemplates), UserError.DENIED, "You need access to restricted templates in order to access this one.", data={'id':self.id})
		else:
			if self.torrent_data:
				del info["attrs"]["torrent_data"]
		info["attrs"]["ready"] = {
			"backend": self.isReady(),
			"hosts": {
					"ready": len(self.hosts.filter(ready=True)),
					"total": len(self.hosts.all())
			}
		} 
		info["attrs"]["name"] = self.name
		info["attrs"]["tech"] = self.tech
		info["attrs"]["preference"] = self.preference
		info["attrs"]["torrent_data_hash"] = hashlib.md5(self.torrent_data).hexdigest() if self.torrent_data else None
		if self.tech == "kvmqm":
			info["attrs"]["kblang"] = self.kblang
		return info

def get(tech, name):
	try:
		return Template.objects.get(tech=tech, name=name)
	except:
		return None
	
def getPreferred(tech):
	tmpls = Template.objects.filter(tech=tech).order_by("-preference")
	InternalError.check(tmpls, code=InternalError.CONFIGURATION_ERROR, message="No template for this type registered", data={"tech": tech})
	return tmpls[0]

resources.TYPES[Template.TYPE] = Template