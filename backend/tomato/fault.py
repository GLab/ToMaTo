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
import xmlrpclib

class Error(models.Model):
	date = models.DateTimeField(auto_now_add=True)
	title = models.CharField(max_length=255)
	message = models.TextField(blank=True)
	
	def to_dict(self):
		return {"id": self.id, "date": self.date, "title": self.title, "message": self.message} # pylint: disable-msg=E1101

def errors_all():
	return Error.objects.all() # pylint: disable-msg=E1101

def errors_add(title, message):
	Error.objects.create(title=title, message=message) # pylint: disable-msg=E1101

def errors_remove(id):
	Error.objects.get(id=id).delete() # pylint: disable-msg=E1101

class Fault(xmlrpclib.Fault):
	pass

def new(code, text):
	return Fault(code, text)

UNKNOWN = -1

# Topology related
NO_SUCH_TOPOLOGY = 100
ACCESS_TO_TOPOLOGY_DENIED = 101
NOT_A_REGULAR_USER = 102
INVALID_TOPOLOGY_STATE_TRANSITION = 103
IMPOSSIBLE_TOPOLOGY_CHANGE = 104
TOPOLOGY_HAS_PROBLEMS = 105
MALFORMED_XML = 106
MALFORMED_TOPOLOGY_DESCRIPTION = 107
INVALID_TOPOLOGY_STATE = 108
TOPOLOGY_BUSY = 109

# Device related
NO_SUCH_DEVICE = 200
UNKNOWN_DEVICE_TYPE = 204
UPLOAD_NOT_SUPPORTED = 201
DOWNLOAD_NOT_SUPPORTED = 202
DUPLICATE_DEVICE_ID = 203
INVALID_INTERFACE_NAME = 205
DUPLICATE_INTERFACE_NAME = 206
DUPLICATE_INTERFACE_CONNECTION = 207
NO_SUCH_TEMPLATE = 208

# Connector related
DUPLICATE_CONNECTOR_ID = 300
UNKNOWN_CONNECTOR_TYPE = 301
UNKNOWN_INTERFACE = 302

# Host related
NO_SUCH_HOST = 400
NO_SUCH_HOST_GROUP = 401
ACCESS_TO_HOST_DENIED = 402
HOST_EXISTS = 403
NO_HOSTS_AVAILABLE = 404
NO_RESOURCES = 405