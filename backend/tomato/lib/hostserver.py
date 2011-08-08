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

import hashlib, urllib, base64, time, uuid

DEFAULT_TIMEOUT = 3600

class HostServer:
	def __init__(self, server, port, basedir, secret):
		self.server = server
		self.port = port
		self.basedir = basedir
		self.secret = secret
		self._baseurl = "http://%s:%s" % (self.server, self.port)
	def _calcGrant(self, path, params):
		list = [k+"="+v for k, v in params.iteritems() if not k == "grant" and not k.startswith("_")]
		list.sort()
		return hashlib.sha1(path + "|" + ("&".join(list)) + "|" + self.secret).hexdigest()
	def _grant(self, path, params, timeout=None):
		if timeout:
			params["valid_until"] = str(time.time()+timeout)
		return self._calcGrant(path, params)
	def randomFilename(self, host):
		return "%s/%s" % (self.basedir, uuid.uuid1())
	def uploadGrant(self, path, redirect=None, timeout=DEFAULT_TIMEOUT):
		params={"path": base64.b64encode(path), "path_encoding": "base64"}
		if redirect:
			params["_redirect"] = base64.b64encode(redirect)
		params.update(grant=self._grant("/upload", params, timeout))
		return self._baseurl + "/upload?" + urllib.urlencode(params)	
	def downloadGrant(self, path, filename=None, mimetype=None, timeout=DEFAULT_TIMEOUT):
		params={"path": base64.b64encode(path), "path_encoding": "base64"}
		if filename:
			params["_name"] = base64.b64encode(filename)
		if mimetype:
			params["_mimetype"] = base64.b64encode(mimetype)			
		params.update(grant=self._grant("/download", params, timeout))
		return self._baseurl + "/download?" + urllib.urlencode(params)	
	def deleteGrant(self, path, redirect=None, timeout=DEFAULT_TIMEOUT):
		params={"path": base64.b64encode(path), "path_encoding": "base64"}
		if redirect:
			params["_redirect"] = base64.b64encode(redirect)
		params.update(grant=self._grant("/delete", params, timeout))
		return self._baseurl + "/delete?" + urllib.urlencode(params)	
