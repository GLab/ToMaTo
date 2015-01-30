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

import thread
from decorators import xmlRpcSafe

def start_thread(func, *args, **kwargs):
	return thread.start_new_thread(func, args, kwargs)

@xmlRpcSafe
def xml_rpc_sanitize(s):
	if s == None:
		return s
	if isinstance(s, str) or isinstance(s, float) or isinstance(s, unicode) or isinstance(s, bool):
		return s
	if isinstance(s, int) and abs(s) < (1<<31):
		return s
	if isinstance(s, int) and abs(s) >= (1<<31):
		return float(s)
	if isinstance(s, list):
		return [xml_rpc_sanitize(e) for e in s]
	if isinstance(s, dict):
		return dict([(str(k), xml_rpc_sanitize(v)) for k, v in s.iteritems()])
	return str(s)

def xml_rpc_safe(s):
	if s == None:
		return True
	if isinstance(s, str) or isinstance(s, float) or isinstance(s, unicode) or isinstance(s, bool):
		return True
	if isinstance(s, int) and abs(s) < (1<<31):
		return True
	if isinstance(s, list):
		for e in s:
			if not xml_rpc_safe(e):
				return False
		return True
	if isinstance(s, dict):
		for k, v in s.iteritems():
			if not xml_rpc_safe(k) or not xml_rpc_safe(v):
				return False
		return True
	print type(s)
	return False

