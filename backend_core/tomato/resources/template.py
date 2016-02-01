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

from ..db import *
from ..generic import *
from .. import config
from ..lib.cmd import bittorrent #@UnresolvedImport
from ..lib.error import UserError, InternalError #@UnresolvedImport
import os, os.path, base64, hashlib, shutil
from .. import currentUser
from ..auth import Flags


kblang_options = {
	"en-us": "English (US)",
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

class Template(Entity, BaseDocument):
	tech = StringField(required=True)
	name = StringField(required=True, unique_with='tech')
	preference = IntField(default=0)
	label = StringField()
	description = StringField()
	restricted = BooleanField(default=False)
	subtype = StringField()
	torrentData = BinaryField(db_field='torrent_data')
	kblang = StringField(default='en-us')
	nlXTPInstalled = BooleanField(db_field='nlxtp_installed')
	showAsCommon = BooleanField(db_field='show_as_common')
	creationDate = FloatField(db_field='creation_date', required=False)
	icon = StringField()
	meta = {
		'ordering': ['tech', '+preference', 'name'],
		'indexes': [
			('tech', 'preference'), ('tech', 'name')
		]
	}
	@property
	def hosts(self):
		from ..host import Host
		return Host.objects(templates=self)

	@property
	def torrentDataHash(self):
		return hashlib.md5(self.torrentData).hexdigest() if self.torrentData else None

	@property
	def size(self):
		try:
			return bittorrent.fileSize(self.torrentData)
		except:
			return -1

	def getReadyInfo(self):
		from ..host import Host
		return {
			"backend": self.isReady(),
			"hosts": {
				"ready": len(self.hosts),
				"total": Host.objects.count()
			}
		}

	def remove(self):
		if self.tech and os.path.exists(self.getTorrentPath()):
			os.remove(self.getTorrentPath())
		if self.tech and os.path.exists(self.getPath()):
			if os.path.isdir(self.getPath()):
				shutil.rmtree(self.getPath())
			else:
				os.remove(self.getPath())
		if self.id:
			self.delete()

	ACTIONS = {
		Entity.REMOVE_ACTION: Action(fn=remove)
	}
	ATTRIBUTES = {
		"id": IdAttribute(),
		"tech": Attribute(field=tech, schema=schema.String(options=PATTERNS.keys())),
		"name": Attribute(field=name, schema=schema.Identifier()),
		"preference": Attribute(field=preference, schema=schema.Number(minValue=0)),
		"label": Attribute(field=label, schema=schema.String()),
		"description": Attribute(field=description, schema=schema.String()),
		"restricted": Attribute(field=restricted, schema=schema.Bool()),
		"subtype": Attribute(field=subtype, schema=schema.String()),
		"torrent_data": Attribute(field=torrentData, set=lambda obj, value: obj.modify_torrent_data(value), get=lambda obj: base64.b64encode(obj.torrentData),
			schema=schema.String()),
		"kblang": Attribute(field=kblang, set=lambda obj, value: obj.modify_kblang(value),
			schema=schema.String(options=kblang_options.keys())),
		"torrent_data_hash": Attribute(readOnly=True, schema=schema.String(null=True), get=lambda obj: obj.torrentDataHash),
		"nlXTP_installed": Attribute(field=nlXTPInstalled),
		"show_as_common": Attribute(field=showAsCommon),
		"creation_date": Attribute(field=creationDate, schema=schema.Number(null=True)),
		"icon": Attribute(field=icon),
		"size": Attribute(readOnly=True, schema=schema.Int(null=False), get=lambda obj: obj.size),
		"ready": Attribute(readOnly=True, get=getReadyInfo, schema=schema.StringMap(items={
				'backend': schema.Bool(),
				'hosts': schema.StringMap(items={
					'ready': schema.Int(),
					'total': schema.Int()
				})
			})
		)
	}

	def init(self, attrs):
		for attr in ["name", "tech", "torrent_data"]:
			UserError.check(attr in attrs, code=UserError.INVALID_CONFIGURATION, message="Template needs attribute",
				data={"attribute": attr})
		if 'kblang' in attrs:
			kblang = attrs['kblang']
			del attrs['kblang']
		else:
			kblang=None
		Entity.init(self, attrs)
		if kblang:
			self.modify({'kblang':kblang})
		self.modify_torrent_data(base64.b64encode(self.torrentData)) #might have been set before name or tech
				
	def getPath(self):
		return os.path.join(config.TEMPLATE_PATH, PATTERNS[self.tech] % self.name)
	
	def getTorrentPath(self):
		return self.getPath() + ".torrent"

	def modify_kblang(self, val):
		UserError.check(self.tech == "kvmqm", UserError.UNSUPPORTED_ATTRIBUTE, "Unsupported attribute for %s template: kblang" % (self.tech), data={"tech":self.tech,"attr_name":"kblang","attr_val":val})
		self.kblang = val

	def modify_torrent_data(self, val):
		raw = base64.b64decode(val)
		try:
			info = bittorrent.torrentInfo(raw)
		except:
			raise UserError(code=UserError.INVALID_VALUE, message="Invalid torrent file")
		UserError.check(not "files" in info or len(info["files"]) == 1, code=UserError.INVALID_VALUE,
			message="Torrent must contain exactly one file")
		self.torrentData = raw
		if self.name and self.tech:
			shouldName = PATTERNS[self.tech] % self.name
			UserError.check(info["name"] == shouldName, code=UserError.INVALID_VALUE,
				message="Torrent content must be named like the template", data={"expected_name": shouldName})
			with open(self.getTorrentPath(), "w") as fp:
				fp.write(raw)

	def isReady(self):
		try:
			path = self.getPath()
			size = os.path.getsize(path)
			return size == self.size
		except:
			return False

	def info(self, include_torrent_data = False):
		info = Entity.info(self)
		if include_torrent_data:
			if self.restricted:
				UserError.check(currentUser().hasFlag(Flags.RestrictedTemplates), UserError.DENIED, "You need access to restricted templates in order to access this one.", data={'id':self.id})
		else:
			del info["torrent_data"]
		return info

	@classmethod
	def get(cls, tech, name):
		try:
			return Template.objects.get(tech=tech, name=name)
		except:
			return None

	@classmethod
	def getPreferred(cls, tech):
		tmpls = Template.objects.filter(tech=tech).order_by("-preference")
		InternalError.check(tmpls, code=InternalError.CONFIGURATION_ERROR, message="No template for this type registered", data={"tech": tech})
		return tmpls[0]

	@classmethod
	def create(cls, attrs):
		obj = cls()
		try:
			obj.init(attrs)
			obj.save()
			return obj
		except:
			obj.remove()
			raise