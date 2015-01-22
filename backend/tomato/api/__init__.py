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

from account import *
from topology import *
from host import *
from elements import *
from connections import *
from resources import *
from docs import *
from capabilities import *
from misc import *
from dumpmanager import *

def debug(method, args=None, kwargs=None, profile=None):
	UserError.check(currentUser().hasFlag(auth.Flags.Debug), code=UserError.DENIED, message="Not enough permissions")
	func = globals().get(method)
	from ..lib import debug
	result = debug.run(func, args, kwargs, profile)
	return result.marshal()
