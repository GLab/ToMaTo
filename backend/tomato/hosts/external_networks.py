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

from tomato.hosts import Host
from tomato.lib import db

from django.db import models
from django.db.models import Sum

class ExternalNetwork(models.Model):
	type = models.CharField(max_length=50, validators=[db.nameValidator])
	group = models.CharField(max_length=50, validators=[db.nameValidator])
	max_devices = models.IntegerField(null=True)
	avoid_duplicates = models.BooleanField(default=False)

	class Meta:
		db_table = "tomato_externalnetwork"
		app_label = 'tomato'
		unique_together = (("group", "type"),)
		ordering=["type", "group"]

	def hasFreeSlots(self):
		return not (self.max_devices and self.usageCount() >= self.max_devices) 

	def usageCount(self):
		from tomato.connectors.external import ExternalNetworkConnector
		connectors = ExternalNetworkConnector.objects.filter(used_network=self)
		num = connectors.annotate(num_connections=models.Count('connection')).aggregate(Sum('num_connections'))["num_connections__sum"]
		return num if num else 0
		
	def toDict(self, bridges=False):
		"""
		Prepares an object for serialization.
		
		@return: a dict containing information about the object
		@rtype: dict
		"""
		data = {"type": self.type, "group": self.group, "max_devices": (self.max_devices if self.max_devices else False), "avoid_duplicates": self.avoid_duplicates}
		if bridges:
			data["bridges"] = [enb.toDict() for enb in self.externalnetworkbridge_set.all()]
		return data

	
class ExternalNetworkBridge(models.Model):
	host = models.ForeignKey(Host)
	network = models.ForeignKey(ExternalNetwork)
	bridge = models.CharField(max_length=10)

	class Meta:
		db_table = "tomato_externalnetworkbridge"
		app_label = 'tomato'
		unique_together=(("host", "bridge"),)
		ordering=["host", "bridge"]

	def toDict(self):
		"""
		Prepares an object for serialization.
		
		@return: a dict containing information about the object
		@rtype: dict
		"""
		return {"host": self.host.name, "type": self.network.type, "group": self.network.group, "bridge": self.bridge}

def getAll():
	return [en.toDict(True) for en in ExternalNetwork.objects.all()]