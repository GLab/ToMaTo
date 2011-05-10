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

def _calcGrant(host, params):
	list = [k+"="+v for k, v in params.iteritems() if not k == "grant"]
	list.sort()
	return hashlib.sha1("&".join(list)+"|"+host.attributes["hostserver_secret_key"]).hexdigest()

def randomFilename(host):
	return "%s/%s" % (host.attributes["hostserver_basedir"], uuid.uuid1())

def uploadGrant(host, filename, redirect):
	params={"file": filename, "redirect": base64.b64encode(redirect), "valid_until": str(time.time()+3600)}
	params.update(grant=_calcGrant(params))
	qstr = urllib.urlencode(params)
	return "http://%s:%s/upload?%s" % (host.name, host.attributes["hostserver_port"], qstr)
	
def downloadGrant(host, file, name):
	params={"file": file, "valid_until": str(time.time()+3600), "name": name}
	params.update(grant=_calcGrant(params))
	qstr = urllib.urlencode(params)
	return "http://%s:%s/download?%s" % (host.name, host.attributes["hostserver_port"], qstr)
