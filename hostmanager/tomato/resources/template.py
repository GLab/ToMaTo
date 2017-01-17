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

from .. import resources, config
from ..db import *
from ..generic import *
from ..user import User
from ..lib import attributes #@UnresolvedImport
from ..lib.cmd import path #@UnresolvedImport
from ..lib.newcmd import aria2
from ..lib.newcmd.util import fs
from ..lib.error import UserError, InternalError #@UnresolvedImport
import os, threading
from ..lib.constants import TypeName,TechName

PATTERNS = {
	TechName.KVMQM: "%s.qcow2",
	TechName.KVM: "%s.qcow2",
	TechName.OPENVZ: "%s.tar.gz",
	TypeName.REPY: "%s.repy",
}

class Template(resources.Resource):
	owner = ReferenceField(User)
	ownerId = ReferenceFieldId(owner)
	tech = StringField()
	name = StringField()
	preference = IntField()
	urls = ListField()
	checksum = StringField()
	size = IntField()
	popularity = IntField()
	ready = BooleanField(default=False)
	kblang = StringField(default="en-us")

	TYPE = "template"

	meta = {
		'ordering': ['tech', '+preference', 'name'],
		'indexes': [
			('tech', 'preference'), ('tech', 'name'), ('tech', 'name', 'owner')
		],
	}

	def init(self, *args, **kwargs):
		self.type = self.TYPE
		attrs = args[0]
		for attr in ["name", "tech", "urls"]:
			UserError.check(attr in attrs, UserError.INVALID_CONFIGURATION, "Attribute missing", data={"attribute": attr})
		self.modify_tech(attrs["tech"])
		self.modify_name(attrs["name"])
		self.ready = False
		self.save()
		self.modify(attrs)

	def fetch(self, detached=False):
		path = self.getPath()
		if self.ready and os.path.exists(path):
			return
		if detached:
			return threading.Thread(target=self.fetch).start()
		aria2.download(self.urls, path)
		self.ready = True
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
		#self.fetch(detached=True)
		return res

	def remove(self):
		if os.path.exists(self.getPath()):
			path.remove(self.getPath(), recursive=True)
		resources.Resource.remove(self)

	def info(self):
		info = resources.Resource.info(self)
		if "torrent_data" in info["attrs"]:
			del info["attrs"]["torrent_data"]
		info["attrs"]["name"] = self.name
		info["attrs"]["tech"] = self.tech
		info["attrs"]["preference"] = self.preference
		info["attrs"]["kblang"] = self.kblang
		return info

	ACTIONS = resources.Resource.ACTIONS.copy()
	ACTIONS.update({
		Entity.REMOVE_ACTION: Action(fn=remove)
	})

	ATTRIBUTES = resources.Resource.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"tech": Attribute(field=tech, schema=schema.String(options=PATTERNS.keys())),
		"name": Attribute(field=name, schema=schema.Identifier()),
		"owner": Attribute(field=ownerId, schema=schema.Identifier()),
		"popularity": Attribute(field=popularity, readOnly=True, schema=schema.Number(minValue=0)),
		"urls": Attribute(field=urls, schema=schema.List(items=schema.URL()),
						  set=lambda obj, value: obj.modify_urls(value)),
		"all_urls": Attribute(schema=schema.List(items=schema.URL()), readOnly=True, get=lambda obj: obj.all_urls),
		"preference": Attribute(field=preference, schema=schema.Number(minValue=0)),
		"kblang": Attribute(field=kblang, set=lambda obj, value: obj.modify_kblang(value),
							schema=schema.String()),
		"size": Attribute(get=lambda obj: float(obj.size) if obj.size else obj.size, readOnly=True,
						  schema=schema.Number()),
		"checksum": Attribute(readOnly=True, field=checksum, schema=schema.String()),
		"ready": Attribute(readOnly=True, schema=schema.Bool()),
	})

def get(tech, name):
	try:
		return Template.objects.get(tech=tech, name=name, owner=currentUser())
	except:
		return None
	
def getPreferred(tech):
	tmpls = Template.objects(tech=tech, owner=currentUser()).order_by("-preference")
	InternalError.check(tmpls, InternalError.CONFIGURATION_ERROR, "No template registered", data={"tech": tech})
	return tmpls[0]

resources.TYPES[Template.TYPE] = Template

from .. import currentUser