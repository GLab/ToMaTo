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

from tomato import fault, hosts
from tomato.lib import ifaceutil, db

from django.db import models

class PhysicalLink(models.Model):
	src_group = models.CharField(max_length=10, validators=[db.nameValidator])
	dst_group = models.CharField(max_length=10, validators=[db.nameValidator])
	loss = models.FloatField()
	delay_avg = models.FloatField()
	delay_stddev = models.FloatField()
			
	sliding_factor = 0.25
		
	class Meta:
		db_table = "tomato_physicallink"	
		app_label = 'tomato'
		unique_together = (("src_group", "dst_group"),)		
			
	def adapt(self, loss, delay_avg, delay_stddev):
		self.loss = ( 1.0 - self.sliding_factor ) * self.loss + self.sliding_factor * loss
		self.delay_avg = ( 1.0 - self.sliding_factor ) * self.delay_avg + self.sliding_factor * delay_avg
		self.delay_stddev = ( 1.0 - self.sliding_factor ) * self.delay_stddev + self.sliding_factor * delay_stddev
		self.save()
	
	def adaptFail(self):
		self.loss = ( 1.0 - self.sliding_factor ) * self.loss + self.sliding_factor
	
	def toDict(self):
		"""
		Prepares a physical link object for serialization.
		
		@return: a dict containing information about the physical link
		@rtype: dict
		"""
		return {"src": self.src_group, "dst": self.dst_group, "loss": self.loss,
			"delay_avg": self.delay_avg, "delay_stddev": self.delay_stddev}

def get(srcg_name, dstg_name):
	return PhysicalLink.objects.get(src_group = srcg_name, dst_group = dstg_name) # pylint: disable-msg=E1101		
		
def getAll():
	return PhysicalLink.objects.all() # pylint: disable-msg=E1101		

def measureRun():
	for srcg in hosts.getGroups():
		for dstg in hosts.getGroups():
			if not srcg == dstg:
				src = hosts.getBest(srcg)
				dst = hosts.getBest(dstg)
				try:
					(loss, delay_avg, delay_stddev) = ifaceutil.ping(src, dst.name, 500, 300)
					try:
						link = get(srcg, dstg)
						link.adapt(loss, delay_avg, delay_stddev)
					except PhysicalLink.DoesNotExist: # pylint: disable-msg=E1101
						PhysicalLink.objects.create(src_group=srcg, dst_group=dstg, loss=loss, delay_avg=delay_avg, delay_stddev=delay_stddev) # pylint: disable-msg=E1101
				except:
					try:
						link = get(srcg, dstg)
						link.adaptFail()
					except PhysicalLink.DoesNotExist: # pylint: disable-msg=E1101
						pass #not creating a record if first contact is a fail
