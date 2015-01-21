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

from ..lib.cache import cached #@UnresolvedImport
import time

@cached(timeout=3600, autoupdate=True)
def server_info():
	"""
	undocumented
	"""
	return {
		"TEMPLATE_TRACKER_URL": "http://%s:%d/announce" % (config.PUBLIC_ADDRESS, config.TRACKER_PORT),
		'external_urls': misc.getExternalURLs(),
		'public_key': misc.getPublicKey(),
		'version': misc.getVersion(),
		'topology_timeout': {
			'initial': config.TOPOLOGY_TIMEOUT_INITIAL,
			'maximum': config.TOPOLOGY_TIMEOUT_MAX,
			'options': config.TOPOLOGY_TIMEOUT_OPTIONS,
			'default': config.TOPOLOGY_TIMEOUT_DEFAULT,
			'warning': config.TOPOLOGY_TIMEOUT_WARNING
		}
	}

def link_statistics(siteA, siteB, type=None, after=None, before=None): #@ReservedAssignment
	return link.getStatistics(siteA, siteB, type, after, before)

def mailAdmins(subject, text, global_contact = True, issue="admin"):
	UserError.check(currentUser(), code=UserError.NOT_LOGGED_IN, message="Unauthorized")
	auth.mailAdmins(subject, text, global_contact, issue)
	
def mailUser(user, subject, text):
	UserError.check(currentUser(), code=UserError.NOT_LOGGED_IN, message="Unauthorized")
	auth.mailUser(user, subject, text)

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
	for h in host.getAll():
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
		topUsage = top.info()['usage']['usage']
		if topUsage['memory']>0 or topUsage['cputime']>0 or topUsage['traffic']>0:
			usage['topologies_active'] += 1
	
	usage['elements'] = elements.Element.objects.count()
	usage['connections'] = connections.Connection.objects.count()
	types = elements.Element.objects.values('type').order_by().annotate(models.Count('type'))
	usage['element_types'] = dict([(t['type'], t['type__count']) for t in types])
	
	usage['users'] = auth.User.objects.count()
	usage['users_active_30days'] = auth.User.objects.filter(last_login__gte = time.time() - 30*24*60*60).count()
	
	
	return stats

def task_list():
	UserError.check(currentUser(), code=UserError.NOT_LOGGED_IN, message="Unauthorized")
	return scheduler.info()

def task_execute(id):
	UserError.check(currentUser(), code=UserError.NOT_LOGGED_IN, message="Unauthorized")
	UserError.check(currentUser().hasFlag(auth.Flags.GlobalAdmin), code=UserError.DENIED, message="Not enough permissions")
	return scheduler.executeTask(id, force=True)

from django.db import models
from .. import misc, config, link, currentUser, host, topology, auth, elements, connections, scheduler
from ..lib.error import UserError
