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

import xmlrpclib

class Fault(xmlrpclib.Fault):
	def __str__ (self):
		return "Error %s: %s" % (self.faultCode, self.faultString)

UNKNOWN_ERROR = -1
AUTHENTICATION_ERROR = 300

USER_ERROR = 400
INVALID_STATE = 401
UNKNOWN_OBJECT = 402
UNSUPPORTED_ATTRIBUTE = 403
UNSUPPORTED_ACTION = 403
OBJECT_BUSY = 404

INTERNAL_ERROR = 500

def new_user(text):
	raise new(text, code=USER_ERROR)

def raise_(text, code=UNKNOWN_ERROR):
	raise new(text, code)

def new(text, code=UNKNOWN_ERROR):
	return Fault(code, text)

def errors_add(error, trace):
	if isinstance(error, Fault) and UNKNOWN_ERROR < error.faultCode < INTERNAL_ERROR:
		return
	print trace

def wrap(exc):
	if isinstance(exc, Fault):
		return exc
	return new('%s:%s' % (exc.__class__.__name__, exc))

def check(condition, errorStr, formatOpt = None, code=USER_ERROR):
	if not condition:
		if formatOpt:
			errorStr = errorStr % formatOpt
		raise_(errorStr, code)