# Explicitly import all django models
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

from auth import User #@UnusedImport
from auth.permissions import Permissions, PermissionEntry #@UnusedImport
from topology import Topology #@UnusedImport
from elements import Element #@UnusedImport
from elements.openvz import OpenVZ, OpenVZ_Interface #@UnusedImport
from elements.kvmqm import KVMQM, KVMQM_Interface #@UnusedImport
from elements.repy import Repy, Repy_Interface #@UnusedImport
from elements.tinc import Tinc_VPN, Tinc_Endpoint #@UnusedImport
from elements.external_network import External_Network_Endpoint, External_Network #@UnusedImport
from elements.udp import UDP_Endpoint #@UnusedImport
from connections import Connection #@UnusedImport
from resources import Resource #@UnusedImport
from resources.template import Template #@UnusedImport
from resources.network import Network #@UnusedImport
from resources.profile import Profile #@UnusedImport
from accounting import Usage, UsageStatistics, UsageRecord, Quota #@UnusedImport
from link import LinkMeasurement #@UnusedImport
from host import Host
from lib.keyvaluestore import KeyValuePair #@UnusedImport

from django.db import models

class TemplateOnHost(models.Model):
	host = models.ForeignKey(Host, related_name="templates")
	template = models.ForeignKey(Template, related_name="hosts")
	ready = models.BooleanField()
	date = models.FloatField()

	class Meta:
		db_table = "tomato_templateonhost"
		app_label = 'tomato'
		unique_together=[('host', 'template')]