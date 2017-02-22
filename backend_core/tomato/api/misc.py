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
from ..lib.constants import StateName
from ..lib import get_public_ip_address
from ..lib.cache import cached
from ..lib.service import get_backend_users_proxy
from ..lib.settings import settings
from ..lib.userflags import Flags

def link_statistics(siteA, siteB):
	return link.getStatisticsInfo(siteA, siteB)

def notifyAdmins(subject, text, global_contact, issue, user_orga, user_name):
	api = get_backend_users_proxy()
	if issue == "admin":
		if global_contact:
			target_flag = Flags.GlobalAdminContact
			target_organization = None
		else:
			target_flag = Flags.OrgaAdminContact
			target_organization = user_orga
	else:
		if global_contact:
			target_flag = Flags.GlobalHostContact
			target_organization = None
		else:
			target_flag = Flags.OrgaHostContact
			target_organization = user_orga
	api.broadcast_message(subject, text, fromUser=user_name,
											  organization_filter=target_organization, flag_filter=target_flag)

@cached(timeout=3600)
def statistics():
	stats = {}
	resources = {}
	stats['resources'] = resources
	resources['hosts'] = 0
	resources['cpus'] = 0
	resources['memory'] = 0
	resources['diskspace'] = 0
	resources['load'] = 0
	resources['availability'] = 0
	for h in Host.getAll():
		resources['hosts'] += 1
		try:
			r = h.hostInfo['resources']
			resources['cpus'] += r['cpus_present']['count']
			resources['memory'] += int(r['memory']['total'])
			for v in r['diskspace'].values():
				resources['diskspace'] += int(v['total'])
		except:
			pass
		resources['load'] += h.getLoad()
		resources['availability'] += h.availability
	for k in ['load', 'availability']:
		resources[k] /= resources['hosts'] if resources['hosts'] else 1.0
	for k in ['memory', 'diskspace']:
		resources[k] = str(resources[k])
	usage = {}
	stats['usage'] = usage
	usage['topologies'] = 0
	
	usage['topologies_active'] = 0
	for top in list(topology.Topology.objects.all()):
		usage['topologies'] += 1
		if top.maxState != StateName.CREATED:
			usage['topologies_active'] += 1
	
	usage['elements'] = elements.Element.objects.count()
	usage['connections'] = connections.Connection.objects.count()
	usage['element_types'] = {key: cls.objects.count() for (key, cls) in elements.TYPES.items()}
	return stats

from .. import link, topology, elements, connections
from ..host import Host
