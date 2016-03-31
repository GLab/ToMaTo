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

import time
from ..lib.versioninfo import getVersionStr
from api_helpers import checkauth, getCurrentUserInfo, getCurrentUserName
from ..lib.service import get_backend_users_proxy
from ..lib.userflags import Flags
from ..lib.service import get_backend_core_proxy

def server_info():
	"""
	undocumented
	"""
	try:
		core_info = get_backend_core_proxy().server_info()
	except:
		core_info = {'public_key': None, "TEMPLATE_TRACKER_URL": None}
	topology_config = settings.get_topology_settings()
	return {
		"TEMPLATE_TRACKER_URL": core_info["TEMPLATE_TRACKER_URL"],
		'public_key': core_info['public_key'],
		'version': getVersionStr(),
		'api_version': [4, 0, 1],
		'topology_timeout': {
			'initial': topology_config[Config.TOPOLOGY_TIMEOUT_INITIAL],
			'maximum': topology_config[Config.TOPOLOGY_TIMEOUT_MAX],
			'options': topology_config[Config.TOPOLOGY_TIMEOUT_OPTIONS],
			'default': topology_config[Config.TOPOLOGY_TIMEOUT_DEFAULT],
			'warning': topology_config[Config.TOPOLOGY_TIMEOUT_WARNING]
		}
	}

def link_statistics(siteA, siteB):
	return get_backend_core_proxy().link_statistics(siteA, siteB)

def notifyAdmins(subject, text, global_contact = True, issue="admin"):
	user_orga = getCurrentUserInfo().get_organization_name()
	user_name = getCurrentUserName()
	get_backend_core_proxy().notifyAdmins(subject, text, global_contact, issue, user_orga, user_name)

def statistics():
	# fixme: broken
	return get_backend_core_proxy().statistics()

@checkauth
def task_list():
	#fixme: should this check more authorization?
	#fixme: this should query all possible backend services...
	return scheduler.info()["tasks"]

def task_execute(id):
	# fixme: this should get the argument on which service to be executed...
	getCurrentUserInfo().check_may_execute_tasks()
	return scheduler.executeTask(id, force=True)

from .. import scheduler
from ..lib.settings import settings, Config
from ..lib import get_public_ip_address
