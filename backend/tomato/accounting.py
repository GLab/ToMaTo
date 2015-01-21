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

from lib import db, attributes #@UnresolvedImport
from lib.decorators import *
from datetime import datetime, timedelta
import time
from . import scheduler, starttime

#TODO: aggregate per user
#TODO: fetch and save current records of to-be-deleted objects

TYPES = ["5minutes", "hour", "day", "month", "year"]
KEEP_RECORDS = {
	"5minutes": 12,
	"hour": 24,
	"day": 30,
	"month": 12,
	"year": 5,
}

def _avg(data, weightSum):
	return sum([k * v for (k, v) in data]) / weightSum
		
def _sum(data, weightSum):
	return sum(v for (v, _) in  data)

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

def _combine(begin, end, records):
	#calculate coverage
	measurements = sum([r.measurements for r in records])
	#combine attributes
	combined = Usage()
	if not measurements:
		return (combined, 0)
	combined.cputime = _sum([(r.usage.cputime, r.measurements) for r in records], measurements)
	combined.diskspace = _avg([(r.usage.diskspace, r.measurements) for r in records], measurements)
	combined.memory = _avg([(r.usage.memory, r.measurements) for r in records], measurements)
	combined.traffic = _sum([(r.usage.traffic, r.measurements) for r in records], measurements)
	return (combined, measurements)

class Usage(models.Model):
	memory = models.FloatField(default=0.0) #unit: bytes
	diskspace = models.FloatField(default=0.0) #unit: bytes
	traffic = models.FloatField(default=0.0) #unit: bytes
	cputime = models.FloatField(default=0.0) #unit: cpu seconds

	def init(self, cputime, diskspace, memory, traffic):
		self.cputime = cputime
		self.diskspace = diskspace
		self.memory = memory
		self.traffic = traffic

	class Meta:
		pass

	def remove(self):
		self.delete()

	def info(self):
		return {
			"cputime": self.cputime,
			"diskspace": self.diskspace,
			"memory": self.memory,
			"traffic": self.traffic
		}


class UsageStatistics(attributes.Mixin, models.Model):
	#records: [UsageRecord]
	attrs = db.JSONField()
	
	class Meta:
		pass

	def init(self):
		self.attrs = {}
		self.begin = time.time()
		self.save()
		
	def remove(self):
		for rec in self.records.all():
			rec.remove()
		self.delete()
	
	def info(self):
		return dict([(t, [r.info() for r in self.getRecords(type=t)]) for t in TYPES])

	def getRecords(self, **kwargs):
		return self.records.filter(**kwargs)

	def importRecords(self, data):
		for rec in data:
			if self.getRecords(type=rec["type"], begin=rec["begin"], end=rec["end"]).exists():
				continue
			usage = Usage()
			usage.cputime = rec["usage"]["cputime"]
			usage.memory = rec["usage"]["memory"]
			usage.diskspace = rec["usage"]["diskspace"]				
			usage.traffic = rec["usage"]["traffic"]
			self.createRecord(type_=rec["type"], begin=rec["begin"], end=rec["end"], measurements=rec["measurements"], usage=usage)

	def createRecord(self, type_, begin, end, measurements, usage):
		usage.save()
		record = UsageRecord()
		record.init(self, type_, begin, end, measurements, usage)
		record.save()
		self.records.add(record)
		return record
		
	def removeOld(self):
		for type_ in TYPES:
			records = self.getRecords(type=type_).order_by("-end")
			keep = records[:KEEP_RECORDS[type_]]
			for rec in records.exclude(pk__in=keep):
				rec.remove()
		
	def update(self):
		self.combine()
		self.removeOld()
		
	def combine(self):
		lastType = TYPES[0]
		for type_ in TYPES[1:]:
			begin, end = _lastRange(type_, time.time())
			if self.getRecords(type=type_, begin=begin, end=end).exists():
				break
			records = self.getRecords(type=lastType, begin__gte=begin, end__lte=end)
			if not records:
				continue
			usage, coverage = _combine(begin, end, records)
			self.createRecord(type_, begin, end, coverage, usage)
			lastType = type_
				
	def updateFrom(self, sources):
		ts = time.time() + 300
		for _ in xrange(KEEP_RECORDS["5minutes"]):
			ts -= 300
			begin, end = _lastRange("5minutes", ts)
			if self.getRecords(type="5minutes", end=end).exists():
				break # end loop here, older records exist all
			data = []
			for s in sources:
				data += s.getRecords(type="5minutes", end=end)
			if len(data) < len(sources):
				if ts > time.time() - 900:
					continue # not all sources ready, continue with older time frame
				elif time.time() - starttime < 900:
					break # we just started, give it some time to fetch all data
				elif not data:
					break # no sources available (any more), break
				else:
					pass # some sources missing but old time frame, continue with what we got
			usage = Usage()
			measurements = 0
			records = 0
			for d in data:
				usage.cputime += d.usage.cputime
				usage.traffic += d.usage.traffic
				usage.memory += d.usage.memory * (d.end - d.begin) / (end-begin)
				usage.diskspace += d.usage.diskspace * (d.end - d.begin) / (end-begin)
				measurements += d.measurements
				records += 1
			self.createRecord("5minutes", begin, end, measurements, usage)
		self.combine()
		self.removeOld()

class UsageRecord(models.Model):
	statistics = models.ForeignKey(UsageStatistics, related_name="records", on_delete=models.CASCADE)
	type = models.CharField(max_length=10, choices=[(t, t) for t in TYPES], db_index=True) #@ReservedAssignment
	begin = models.FloatField()
	end = models.FloatField(db_index=True)
	measurements = models.IntegerField()
	usage = models.ForeignKey(Usage, related_name="+", on_delete=models.PROTECT)
	
	class Meta:
		unique_together=(("statistics", "type", "end"),)

	def init(self, statistics, type, begin, end, measurements, usage): #@ReservedAssignment
		self.statistics = statistics
		self.type = type
		self.begin = begin
		self.end = end
		self.measurements = measurements
		usage.save()
		self.usage = usage
		self.save()

	def remove(self):
		usage = self.usage
		self.delete()
		usage.remove()

	def info(self):
		return {
			"type": self.type,
			"begin": self.begin,
			"end": self.end,
			"measurements": self.measurements,
			"usage": self.usage.info()
		}

class Quota(models.Model):
	monthly = models.ForeignKey(Usage, related_name="+", on_delete=models.PROTECT)
	used = models.ForeignKey(Usage, related_name="+", on_delete=models.PROTECT)
	used_time = models.FloatField()
	continous_factor = models.FloatField()
	
	def init(self, cputime, memory, diskspace, traffic, continous_factor):
		self.monthly = Usage.objects.create(cputime=cputime, memory=memory, diskspace=diskspace, traffic=traffic)
		self.used = Usage.objects.create()
		self.used_time = time.time()
		self.continous_factor = continous_factor
		self.save()
	
	def remove(self):
		monthly = self.monthly
		used = self.used
		self.delete()
		monthly.remove()
		used.remove()

	def getFactor(self):
		return max(self.used.cputime/self.monthly.cputime,
				self.used.memory/self.monthly.memory,
				self.used.diskspace/self.monthly.diskspace,
				self.used.traffic/self.monthly.traffic)

	def update(self, usageStats):
		start_of_month = util.startOfMonth(*util.getYearMonth(time.time()))
		if self.used_time < start_of_month:
			self.used.cputime = 0.0
			self.used.memory = 0.0
			self.used.diskspace = 0.0
			self.used.traffic = 0.0
			self.used.save()
			self.used_time = start_of_month
			self.save()
		recs = usageStats.getRecords(type="5minutes", end__gt=self.used_time)
		factor = 300.0 / util.secondsInMonth(*util.getYearMonth(time.time())) 
		end = self.used_time
		for rec in recs:
			if rec.usage.cputime > self.monthly.cputime * factor * self.continous_factor:
				self.used.cputime += rec.usage.cputime - self.monthly.cputime * factor * self.continous_factor
			if rec.usage.memory > self.monthly.memory * self.continous_factor:
				self.used.memory += rec.usage.memory * factor - self.monthly.memory * self.continous_factor
			if rec.usage.diskspace > self.monthly.diskspace * self.continous_factor:
				self.used.diskspace += rec.usage.diskspace * factor - self.monthly.diskspace * self.continous_factor
			if rec.usage.traffic > self.monthly.traffic * factor * self.continous_factor:
				self.used.traffic += rec.usage.traffic - self.monthly.traffic * factor * self.continous_factor
			if rec.end > end:
				end = rec.end
		self.used_time = end
		self.used.save()
		self.save()

	def modify(self, value):
		if "monthly" in value:
			m = value["monthly"]
			if "cputime" in m:
				self.monthly.cputime = m["cputime"]
			if "memory" in m:
				self.monthly.memory = m["memory"]
			if "diskspace" in m:
				self.monthly.diskspace = m["diskspace"]
			if "traffic" in m:
				self.monthly.traffic = m["traffic"]
			self.monthly.save()
		if "used" in value:
			u = value["used"]
			if "cputime" in u:
				self.used.cputime = u["cputime"]
			if "memory" in u:
				self.used.memory = u["memory"]
			if "diskspace" in u:
				self.used.diskspace = u["diskspace"]
			if "traffic" in u:
				self.used.traffic = u["traffic"]
			self.used.save()
		if "continous_factor" in value:
			self.continous_factor = value["continous_factor"]
			self.save()

	def info(self):
		return {
			"used": self.used.info(),
			"monthly": self.monthly.info(),
			"used_time": self.used_time,
			"continous_factor": self.continous_factor
		}

@util.wrap_task
@db.commit_after
def aggregate():
	from . import host, elements, connections, topology, auth
	for el in elements.getAll():
		el.updateUsage()
	for con in connections.getAll():
		con.updateUsage()
	for top in topology.getAll():
		top.updateUsage()
	for user in auth.getAllUsers():
		user.updateUsage()
	for orga in host.getAllOrganizations():
		orga.updateUsage()
	for h in host.getAll():
		if h.enabled:
			h.updateUsage()

@util.wrap_task
@db.commit_after
def updateQuota():
	from . import auth
	try:
		for user in auth.getAllUsers():
			user.updateQuota()
			user.enforceQuota()
	except:
		import traceback
		traceback.print_exc()

scheduler.scheduleRepeated(60, aggregate) #every minute @UndefinedVariable
scheduler.scheduleRepeated(60, updateQuota) #every minute @UndefinedVariable