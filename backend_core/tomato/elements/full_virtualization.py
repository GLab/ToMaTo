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
from .generic import MultiTechVMElement, MultiTechVMInterface, ST_CREATED, ST_PREPARED
import time
from ..lib import util #@UnresolvedImport
from ..lib.constants import TypeName, TechName, TypeTechTrans

class FullVirtualization(MultiTechVMElement):
	TYPE = TypeName.FULL_VIRTUALIZATION
	TECHS = TypeTechTrans.FULL_VIRTUALTIZATION_TECHS
	DIRECT_ATTRS_EXCLUDE = ["ram", "cpus", "timeout", "template"]
	CAP_CHILDREN = {
		TypeName.FULL_VIRTUALIZATION_INTERFACE: [ST_CREATED, ST_PREPARED],
	}
	PROFILE_ATTRS = ["ram", "cpus"]

	def init(self, *args, **kwargs):
		MultiTechVMElement.init(self, *args, **kwargs)
		if self.template.kblang:
			self.modify(kblang=self.template.kblang)

	def modify_template(self, tmplName):
		FullVirtualization.modify_template(self, tmplName)
		if self.template.kblang:
			self.modify(kblang=self.template.kblang)

class FullVirtualization_Interface(MultiTechVMInterface):
	TYPE = TypeName.FULL_VIRTUALIZATION_INTERFACE
	CAP_PARENT = [FullVirtualization.TYPE]
	TECHS = TypeTechTrans.FULL_VIRTUALTIZATION_INTERFACE_TECHS


@util.wrap_task
def syncRexTFV():
	for e in FullVirtualization.objects.filter(nextSync__gt=0.0, nextSync__lte=time.time()):
		with e:
			try:
				e.reload().updateInfo()
			except FullVirtualization.DoesNotExist:
				pass
		
scheduler.scheduleRepeated(1, syncRexTFV)
	
elements.TYPES[FullVirtualization.TYPE] = FullVirtualization
elements.TYPES[FullVirtualization_Interface.TYPE] = FullVirtualization_Interface
