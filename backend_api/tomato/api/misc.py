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

from ..lib.service import get_backend_core_proxy, is_self, get_tomato_inner_proxy
from ..lib.util import joinDicts
from ..lib.versioninfo import getVersionStr
from ..lib.cache import cached
from ..misc import getCAPublicKey
from ..lib.settings import settings, Config

def server_info():
	"""
	Retrieve configuration information about the running instance of ToMaTo backend.

	Return value:
	  The return value of this method is a dict containing the following
	  information about the account:

	  ``public_key``
		public key that is used to authenticate on hostmanagers.

	  ``version``
		Version of backend_api.

	  ``api_version``
		Version of this API. If the API changes semantically or syntactically,
		the version will be different.

	  ``topology_timeout``
		Timeout configuration for topologies. Clients that provide an interface for
		setting timeouts should use this information to show options.
	"""
	return server_info_res

topology_config = settings.get_topology_settings()
server_info_res = {
	'public_key': getCAPublicKey(),
	'version': getVersionStr(),
	'api_version': [4, 1, 0],
	'topology_timeout': {
		'initial': topology_config[Config.TOPOLOGY_TIMEOUT_INITIAL],
		'maximum': topology_config[Config.TOPOLOGY_TIMEOUT_MAX],
		'options': topology_config[Config.TOPOLOGY_TIMEOUT_OPTIONS],
		'default': topology_config[Config.TOPOLOGY_TIMEOUT_DEFAULT],
		'warning': topology_config[Config.TOPOLOGY_TIMEOUT_WARNING]
	},
	'web_url': settings.get_web_url()
}

def link_statistics(siteA, siteB):
	"""
	get statistics about the link between two sites.
	the statistics between a site and itself are measurements inside the respective site.

	Parameter *siteA*
		name of first site

	Parameter *siteB*
		name of second site

	Return value:
		link statistics.
		A dict containing multiple measurements

		 ``siteA``
		 name of siteA

		 ``siteB``
		 name of siteB

		 ``single``
		 last measurement. Measurement is done every minute.

		 ``5minutes``
		 mean measurement of last five minutes

		 ``hour"``
		 mean measurement of last 60 minutes

		 ``day"``
		 mean measurement of last 24 hours

		 ``month``
		 mean measurement of last 30 days

		 ``year``
		 mean measurement of last 12 months



		 Every measurement is a dict containing the keys:

		 ``begin``
		 begin of period

		 ``end``
		 end of period

		 ``measurements``
		 number of measurements in period

		 ``loss``
		 mean loss rate of the measurements

		 ``delay_avg``
		 mean delay of the measurements

		 ``delay_stddev``
		 standard deviation of the delay measurements

	"""
	return get_backend_core_proxy().link_statistics(siteA, siteB)


def statistics():
	"""
	get statistics about this testbed.

	Return value:
	  The return value of this method is a dict containing the following
	  information about the account:

	  ``usage``
		information about the current number of users, active users, elements, topologies, etc.

	  ``resources``
		information about the testbed's resources (host load, host availability, available resources, ...)
	"""
	stats = {}
	for mod in Config.TOMATO_BACKEND_MODULES:
		if not is_self(mod):
			stat_update = get_tomato_inner_proxy(mod).statistics()
			stats = joinDicts(stats, stat_update)
	return stats
