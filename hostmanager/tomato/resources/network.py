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

from django.db import models
from .. import resources, firewall, currentUser
from ..user import User


class Network(resources.Resource):
	owner = models.ForeignKey(User, related_name='networks')
	kind = models.CharField(max_length=50)
	bridge = models.CharField(max_length=20)
	preference = models.IntegerField(default=0)
	
	TYPE = "network"

	class Meta:
		db_table = "tomato_network"
		app_label = 'tomato'
		unique_together = (("bridge", "owner"))
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		resources.Resource.init(self, *args, **kwargs)
		self.save()
		firewall.add_bridge(self.bridge)
		
	def remove(self):
		br = self.bridge
		resources.Resource.remove(self)
		firewall.remove_bridge(br)
				
	def upcast(self):
		return self
	
	def getBridge(self):
		return self.bridge
	
	def modify_kind(self, val):
		self.kind = val
	
	def modify_bridge(self, val):
		
		#check whether the firewall has to be modified.
		old_bridge = None
		if self.bridge:
			old_bridge = self.bridge
		
		#set the new value
		self.bridge = val
		
		#if the firewall check returned true, apply the changes
		if old_bridge:
			firewall.add_bridge(val) # if no old bridge was there, this will be done by init.
			firewall.remove_bridge(old_bridge)

	def modify_preference(self, val):
		self.preference = val

	def info(self):
		info = resources.Resource.info(self)
		info["attrs"]["kind"] = self.kind
		info["attrs"]["bridge"] = self.bridge
		info["attrs"]["preference"] = self.preference
		return info

def get(kind):
	return Network.objects.filter((models.Q(kind=kind)|models.Q(kind__startswith=kind+"/"))&models.Q(owner=currentUser())).order_by("-preference")[0]

def getAll():
	return Network.objects.all()

resources.TYPES[Network.TYPE] = Network