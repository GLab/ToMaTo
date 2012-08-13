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
from tomato import resources

class Template(resources.Resource):
	tech = models.CharField(max_length=20)
	name = models.CharField(max_length=50)
	preference = models.IntegerField(default=0)
	
	TYPE = "template"

	class Meta:
		db_table = "tomato_template"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		resources.Resource.init(self, *args, **kwargs)
				
	def upcast(self):
		return self
	
	def getPath(self):
		#FIXME: path
		return None
	
	def info(self):
		info = resources.Resource.info(self)
		info["attrs"]["name"] = self.name
		info["attrs"]["tech"] = self.tech
		return info

def get(tech, name):
	try:
		return Template.objects.get(tech=tech, name=name)
	except:
		return None
	
def getPreferred(tech):
	return Template.objects.filter(tech=tech).order_by("preference")[0]