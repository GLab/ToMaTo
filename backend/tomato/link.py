# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2013 Dennis Schwerdel, University of Kaiserslautern
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
from . import host
from lib import util, logging #@UnresolvedImport

from datetime import datetime, timedelta
import time, random

TYPES = ["single", "5minutes", "hour", "day", "month", "year"]
KEEP_RECORDS = {
	"single": 10,
	"5minutes": 12,
	"hour": 24,
	"day": 30,
	"month": 12,
	"year": 5,
}

def _lastRange(type_, now=None):
	if not now:
		now = time.time()
	now = datetime.utcfromtimestamp(now)
	if type_ == "5minutes":
		end = now.replace(second=0, microsecond=0)
		end = end.replace(minute=(end.minute / 5)*5)
		begin = end - timedelta(minutes=5)
	elif type_ == "hour":
		end = now.replace(second=0, microsecond=0, minute=0)
		begin = end - timedelta(hours=1)
	elif type_ == "day":
		end = now.replace(second=0, microsecond=0, minute=0, hour=0)
		begin = end - timedelta(days=1)
	elif type_ == "month":
		end = now.replace(second=0, microsecond=0, minute=0, hour=0, day=1)
		begin = datetime(end.year if end.month > 1 else end.year -1, end.month -1 if end.month > 1 else 12, 1)
	elif type_ == "year":
		end = now.replace(second=0, microsecond=0, minute=0, hour=0, day=1, month=1)
		begin = datetime(end.year - 1, 1, 1)
	return (util.utcDatetimeToTimestamp(begin), util.utcDatetimeToTimestamp(end)) 

def _avg(data, weightSum):
	return sum([k * v for (k, v) in data]) / weightSum
		
def _sum(data, weightSum):
	return sum(v for (v, _) in  data)

class LinkMeasurement(models.Model):
	siteA = models.ForeignKey(host.Site, null=False, related_name="+")
	siteB = models.ForeignKey(host.Site, null=False, related_name="+")
	type = models.CharField(max_length=10, choices=[(t, t) for t in TYPES], db_index=True) #@ReservedAssignment
	begin = models.FloatField()
	end = models.FloatField(db_index=True)
	measurements = models.IntegerField()
	loss = models.FloatField()
	delayAvg = models.FloatField()
	delayStddev = models.FloatField()
	
	class Meta:
		unique_together=(("siteA", "siteB", "type", "end"),)

	def info(self):
		return {"siteA": self.siteA.name, "siteB": self.siteB.name, "type": self.type, "begin": self.begin, "end": self.end, "measurements": self.measurements, "loss": self.loss, "delay_avg": self.delayAvg, "delay_stddev": self.delayStddev}

def _combine():
	for siteA in host.getAllSites():
		for siteB in host.getAllSites():
			if siteA.id > siteB.id:
				continue
			link = LinkMeasurement.objects.filter(siteA=siteA, siteB=siteB)
			lastType = TYPES[0]
			for type_ in TYPES[1:]:
				begin, end = _lastRange(type_)
				if link.filter(type=type_, begin=begin, end=end).exists():
					break
				records = link.filter(type=lastType, begin__gte=begin, end__lte=end)
				if not records.exists():
					continue
				measurements = sum([r.measurements for r in records])
				loss = _avg([(r.loss, r.measurements) for r in records], measurements)
				lossMeasurements = sum([r.measurements * (1.0-r.loss) for r in records]) or 1.0 
				delayAvg = _avg([(r.delayAvg, r.measurements * (1.0 - r.loss)) for r in records], lossMeasurements)
				delayStddev = _avg([(r.delayStddev, r.measurements * (1.0 - r.loss)) for r in records], lossMeasurements)
				LinkMeasurement.objects.create(siteA=siteA, siteB=siteB, begin=begin, end=end, type=type_, loss=loss, delayAvg=delayAvg, delayStddev=delayStddev, measurements=measurements)
				lastType = type_
				
def _measure():
	for siteA in host.getAllSites():
		if not siteA.hosts.exists():
			continue
		for siteB in host.getAllSites():
			if siteA.id > siteB.id:
				continue
			choices = list(siteA.hosts.all())
			hostA = None
			while choices and not hostA:
				hostA = random.choice(choices)
				if hostA.problems():
					choices.remove(hostA)
					hostA = None
			if not hostA:
				continue
			choices = list(siteB.hosts.all())
			if hostA in choices:
				choices.remove(hostA)
			hostB = None
			while choices and not hostB:
				hostB = random.choice(choices)
				if hostB.problems():
					choices.remove(hostB)
					hostB = None
			if not hostB:
				continue
			begin = time.time()
			res = hostA.getProxy().host_ping(hostB.address)
			end = time.time()
			logging.logMessage("link measurement", category="link", siteA=siteA.name, siteB=siteB.name, hostA=hostA.address, hostB=hostB.address, result=res)
			LinkMeasurement.objects.create(siteA=siteA, siteB=siteB, begin=begin, end=end, type=TYPES[0], loss=res["loss"], delayAvg=res.get("rtt_avg", 0.0)/2.0, delayStddev=res.get("rtt_mdev", 0.0)/2.0, measurements=res["transmitted"])
	
def _removeOld():
	for siteA in host.getAllSites():
		for siteB in host.getAllSites():
			if siteA.id > siteB.id:
				continue
			link = LinkMeasurement.objects.filter(siteA=siteA, siteB=siteB)
			for type_ in TYPES:
				for r in link.filter(type=type_).order_by("-begin")[KEEP_RECORDS[type_]:]:
					r.delete()
		
def taskRun():
	_combine()
	_measure()
	_removeOld()
	
def getStatistics(siteA, siteB, type=None, after=None, before=None): #@ReservedAssignment
	siteA = host.getSite(siteA)
	siteB = host.getSite(siteB)
	all_ = LinkMeasurement.objects.all()
	if siteA.id > siteB.id:
		siteA, siteB = siteB, siteA
	all_ = all_.filter(siteA=siteA, siteB=siteB)
	if after:
		all_ = all_.filter(end__gte=after)
	if before:
		all_ = all_.filter(begin__lte=before)
	if type:
		return [m.info() for m in all_.filter(type=type)]
	else:
		return dict([(t, [m.info() for m in all_.filter(type=t)]) for t in TYPES])
	
task = util.RepeatedTimer(60, taskRun) #every minute