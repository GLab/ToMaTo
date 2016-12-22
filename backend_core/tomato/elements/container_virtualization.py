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

from ..generic import Attribute
from .. import elements, scheduler
from .generic import ST_CREATED, ST_PREPARED, MultiTechVMElement, MultiTechVMInterface
import time
from ..lib import util #@UnresolvedImport
from ..lib.constants import TechName, TypeName, TypeTechTrans

class ContainerVirtualization(MultiTechVMElement):
	TYPE = TypeName.CONTAINER_VIRTUALIZATION
	TECHS = TypeTechTrans.CONTAINER_VIRTUALIZATION_TECHS
	DIRECT_ATTRS_EXCLUDE = ["ram", "diskspace", "cpus", "timeout", "template"]
	CAP_CHILDREN = {
		TypeName.CONTAINER_VIRTUALIZATION_INTERFACE: [ST_CREATED, ST_PREPARED],
	}
	PROFILE_ATTRS = ["ram", "diskspace", "cpus"]
	
	def init(self, *args, **kwargs):
		MultiTechVMElement.init(self, *args, **kwargs)
		self.modify_name(self.name)
	
	def modify_name(self, value):
		self.name = value
		self.modify(hostname=util.filterStr(value, substitute="x"))

	ATTRIBUTES = MultiTechVMElement.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"name": Attribute(field=MultiTechVMElement.name, set=modify_name, label="Name")
	})

class ContainerVirtualization_Interface(MultiTechVMInterface):
	TYPE = TypeName.CONTAINER_VIRTUALIZATION_INTERFACE
	TECHS = TypeTechTrans.CONTAINER_VIRTUALIZATION_INTERFACE_TECHS
	CAP_PARENT = [ContainerVirtualization.TYPE]
	#TODO: add /24, /64

@util.wrap_task
def syncRexTFV():
	for e in ContainerVirtualization.objects.filter(nextSync__gt=0.0, nextSync__lte=time.time()):
		with e:
			try:
				e.reload().updateInfo()
			except ContainerVirtualization.DoesNotExist:
				pass


scheduler.scheduleRepeated(1, syncRexTFV)

elements.TYPES[ContainerVirtualization.TYPE] = ContainerVirtualization
elements.TYPES[ContainerVirtualization_Interface.TYPE] = ContainerVirtualization_Interface
