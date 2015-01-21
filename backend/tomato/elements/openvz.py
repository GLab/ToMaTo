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

from .. import elements, scheduler
import generic, time
from ..lib import util,attributes #@UnresolvedImport
from . import getLock

class OpenVZ(generic.VMElement):
	TYPE = "openvz"
	DIRECT_ATTRS_EXCLUDE = ["ram", "diskspace", "cpus", "timeout", "template"]
	CAP_CHILDREN = {
		"openvz_interface": [generic.ST_CREATED, generic.ST_PREPARED],
	}
	PROFILE_ATTRS = ["ram", "diskspace", "cpus"]
	
	def init(self, *args, **kwargs):
		generic.VMElement.init(self, *args, **kwargs)
		self.modify_name(self.name)
	
	def modify_name(self, value):
		generic.VMElement.modify_name(self, value)
		self._modify({"hostname": util.filterStr(value, substitute="x")})
	
	class Meta:
		db_table = "tomato_openvz"
		app_label = 'tomato'

class OpenVZ_Interface(generic.VMInterface):
	TYPE = "openvz_interface"
	CAP_PARENT = [OpenVZ.TYPE]
	
	
	ip4address_attr = attributes.Attr("ip4address", desc="IPv4 address", type="str")
	ip4address = ip4address_attr.attribute()
	ip6address_attr = attributes.Attr("ip6address", desc="IPv6 address", type="str")
	ip6address = ip6address_attr.attribute()
	
	CUSTOM_ATTRS = {
				"ip4address":ip4address_attr,"ip6address":ip6address_attr
				}
	
	
	def modify_ip4address(self,val):
		if val and not '/' in val:
			val+='/24'		
		self.ip4address = val
		if self.element:
			self.element.modify({"ip4address": val})
	
	def modify_ip6address(self,val):
		if val and not '/' in val:
			val+='/64'		
		self.ip6address = val
		if self.element:
			self.element.modify({"ip6address": val})
			
			
	class Meta:
		db_table = "tomato_openvz_interface"
		app_label = 'tomato'
		
@util.wrap_task
def syncRexTFV():
	for e in OpenVZ.objects.filter(next_sync__gt=0.0, next_sync__lte=time.time()):
		with getLock(e):
			e.reload().updateInfo()

scheduler.scheduleRepeated(1, syncRexTFV)
	
elements.TYPES[OpenVZ.TYPE] = OpenVZ
elements.TYPES[OpenVZ_Interface.TYPE] = OpenVZ_Interface