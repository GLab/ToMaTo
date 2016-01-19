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
from .generic import VMElement, VMInterface, ST_CREATED, ST_PREPARED
import time
from ..lib import util #@UnresolvedImport

class KVMQM(VMElement):
	TYPE = "kvmqm"
	DIRECT_ATTRS_EXCLUDE = ["ram", "cpus", "timeout", "template"]
	CAP_CHILDREN = {
		"kvmqm_interface": [ST_CREATED, ST_PREPARED],
	}
	PROFILE_ATTRS = ["ram", "cpus"]

	def init(self, *args, **kwargs):
		VMElement.init(self, *args, **kwargs)
		if self.template.kblang:
			self.modify({"kblang": self.template.kblang})

	def modify_template(self, tmplName):
		VMElement.modify_template(self, tmplName)
		if self.template.kblang:
			self.modify({"kblang": self.template.kblang})

class KVMQM_Interface(VMInterface):
	TYPE = "kvmqm_interface"
	CAP_PARENT = [KVMQM.TYPE]


@util.wrap_task
def syncRexTFV():
	for e in KVMQM.objects.filter(nextSync__gt=0.0, nextSync__lte=time.time()):
		with e:
			try:
				e.reload().updateInfo()
			except KVMQM.DoesNotExist:
				pass
		
scheduler.scheduleRepeated(1, syncRexTFV)
	
elements.TYPES[KVMQM.TYPE] = KVMQM
elements.TYPES[KVMQM_Interface.TYPE] = KVMQM_Interface