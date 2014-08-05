# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2014, Integrated Communication Systems Lab, University of Kaiserslautern
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

from .. import dump

def dump_count():
	"""
	returns the total number of error dumps
	"""
	return dump.getCount()

def dump_list(after=None,list_only=False,include_data=False,compress_data=True):
	"""
	returns a list of dumps.
	
	Parameter *after*: 
      If set, only include dumps which have a timestamp after this time.
    
    Parameter *list_only*:
      If True, only include dump IDs.
      
    Parameter *include_data*:
      If True, include detailed data. This may be about 1M per dump.
      
    Parameter *compress_data*:
      If True and include_data, compress the detailed data before returning. It may still be around 20M per dump after compressing.
    """
	import datetime
	dumps = dump.getAll(after=after, list_only=list_only, include_data=include_data, compress_data=compress_data)
	for dump in dumps:
		dump['timestamp'] = datetime.datetime.strftime(datetime.datetime.fromtimestamp(dump['timestamp']), "%Y-%m-%dT%H:%M:%S.%f") #format must be the same as in backend.host.dump*
	return dumps	

def dump_info(dump_id,include_data=False,compress_data=True):
	"""
	returns info of a single dump
	
	Parameter *dump_id*:
	  The internal id of the dump
	  
	Parameter *include_data*:
      If True, include detailed data. This may be about 1M.
      
    Parameter *compress_data*:
      If True and include_data, compress the detailed data before returning. It may still be around 20M after compressing.
	"""
	import datetime
	dump = dump.get(dump_id, include_data=include_data, compress_data=compress_data)
	dump['timestamp'] = datetime.datetime.strftime(datetime.datetime.fromtimestamp(dump['timestamp']), "%Y-%m-%dT%H:%M:%S.%f") #format must be the same as in backend.host.dump*
	return dump
	
