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
from ..lib import util #@UnresolvedImport
from . import getLock

class KVMQM(generic.VMElement):
	TYPE = "kvmqm"
	DIRECT_ATTRS_EXCLUDE = ["ram", "cpus", "timeout", "template"]
	CAP_CHILDREN = {
		"kvmqm_interface": [generic.ST_CREATED, generic.ST_PREPARED],
	}
	PROFILE_ATTRS = ["ram", "cpus"]
	
	class Meta:
		db_table = "tomato_kvmqm"
		app_label = 'tomato'
	
class KVMQM_Interface(generic.VMInterface):
	TYPE = "kvmqm_interface"
	CAP_PARENT = [KVMQM.TYPE]
	
	class Meta:
		db_table = "tomato_kvmqm_interface"
		app_label = 'tomato'

@util.wrap_task
def syncRexTFV():
	for e in KVMQM.objects.filter(next_sync__gt=0.0, next_sync__lte=time.time()):
		with getLock(e):
			e.reload().updateInfo()
		
scheduler.scheduleRepeated(1, syncRexTFV)
	
elements.TYPES[KVMQM.TYPE] = KVMQM
elements.TYPES[KVMQM_Interface.TYPE] = KVMQM_Interface