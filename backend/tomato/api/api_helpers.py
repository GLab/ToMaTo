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

from .. import currentUser
from ..lib.error import UserError  #@UnresolvedImport
import types

def checkauth(fn):
	def call(*args, **kwargs):
		if not currentUser():
			raise UserError(UserError.NOT_LOGGED_IN, message="not logged in")
		return fn(*args, **kwargs)
	call.__name__ = fn.__name__
	call.__doc__ = fn.__doc__
	call.__dict__.update(fn.__dict__)
	return call

def makeApiSafe(value):
	if value is None or isinstance(value, (bool, int, long, float)+types.StringTypes):
		return value
	if isinstance(value, types.DictionaryType):
		return {str(k): makeApiSafe(v) for k, v in value.items()}
	if isinstance(value, (types.ListType, types.TupleType)):
		return [makeApiSafe(v) for v in value]
	raise TypeError("Unsupported type: %s" % type(value))

def apiSafe(fn):
	def call(*args, **kwargs):
		return makeApiSafe(fn(*args, **kwargs))
	call.__name__ = fn.__name__
	call.__module__ = fn.__module__
	call.__doc__ = fn.__doc__
	return call