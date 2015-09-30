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

from .db import *

from lib.decorators import *
from datetime import datetime, timedelta
import time
from . import scheduler

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

def _toPoint(time_=None):
	if not time_:
		time_ = time.time()
	return datetime.utcfromtimestamp(time_)

def _lastPoint(type_, point):
	if type_ == "5minutes":
		return point.replace(second=0, microsecond=0, minute=(point.minute / 5)*5)
	elif type_ == "hour":
		return point.replace(second=0, microsecond=0, minute=0)
	elif type_ == "day":
		return point.replace(second=0, microsecond=0, minute=0, hour=0)
	elif type_ == "month":
		return point.replace(second=0, microsecond=0, minute=0, hour=0, day=1)
	elif type_ == "year":
		return point.replace(second=0, microsecond=0, minute=0, hour=0, day=1, month=1)

def _nextPoint(point, type_):
	if type_ == "5minutes":
		return point + timedelta(minutes=5)
	elif type_ == "hour":
		return point + timedelta(hours=1)
	elif type_ == "day":
		return point + timedelta(days=1)
	elif type_ == "month":
		return datetime(point.year if point.month < 12 else point.year +1, point.month +1 if point.month < 12 else 1, 1)
	elif type_ == "year":
		return datetime(point.year +1, 1, 1)

def _prevPoint(point, type_):
	if type_ == "5minutes":
		return point - timedelta(minutes=5)
	elif type_ == "hour":
		return point - timedelta(hours=1)
	elif type_ == "day":
		return point - timedelta(days=1)
	elif type_ == "month":
		return datetime(point.year if point.month > 1 else point.year -1, point.month -1 if point.month > 1 else 12, 1)
	elif type_ == "year":
		return datetime(point.year -1, 1, 1)

def _toTime(point):
	return util.utcDatetimeToTimestamp(point)

def _combine(records):
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

class Usage(EmbeddedDocument):
	memory = FloatField(default=0.0) #unit: bytes
	diskspace = FloatField(default=0.0) #unit: bytes
	traffic = FloatField(default=0.0) #unit: bytes
	cputime = FloatField(default=0.0) #unit: cpu seconds

	def init(self, cputime, diskspace, memory, traffic):
		self.cputime = cputime
		self.diskspace = diskspace
		self.memory = memory
		self.traffic = traffic

	def info(self):
		return {
			"cputime": self.cputime,
			"diskspace": self.diskspace,
			"memory": self.memory,
			"traffic": self.traffic
		}

class UsageRecord(EmbeddedDocument):
	begin = FloatField(required=True)
	end = FloatField(required=True)
	measurements = IntField(default=0)
	usage = EmbeddedDocumentField(Usage, required=True)
	meta = {
		'collection': 'usage_record',
		'ordering': ['type', 'end'],
		'indexes': [
			('type', 'end')
		]
	}

	def init(self, begin, end, measurements, usage): #@ReservedAssignment
		self.begin = begin
		self.end = end
		self.measurements = measurements
		self.usage = usage

	def info(self):
		return {
			"begin": self.begin,
			"end": self.end,
			"measurements": self.measurements,
			"usage": self.usage.info()
		}


class UsageStatistics(BaseDocument):
	"""
	:type by5minutes: list of UsageRecord
	:type byHour: list of UsageRecord
	:type byDay: list of UsageRecord
	:type byMonth: list of UsageRecord
	:type byYear: list of UsageRecord
	"""
	by5minutes = ListField(EmbeddedDocumentField(UsageRecord), db_field='5minutes')
	byHour = ListField(EmbeddedDocumentField(UsageRecord), db_field='hour')
	byDay = ListField(EmbeddedDocumentField(UsageRecord), db_field='day')
	byMonth = ListField(EmbeddedDocumentField(UsageRecord), db_field='month')
	byYear = ListField(EmbeddedDocumentField(UsageRecord), db_field='year')
	meta = {
		'collection': 'usage_statistics',
	}

	def init(self):
		self.save()

	def remove(self):
		self.delete()

	def info(self):
		return {
			"5minutes": [rec.info() for rec in self.by5minutes],
			"hour": [rec.info() for rec in self.byHour],
			"day": [rec.info() for rec in self.byDay],
			"month": [rec.info() for rec in self.byMonth],
			"year": [rec.info() for rec in self.byYear],
		}

	def _getList(self, type_):
		"""
		:rtype: list of UsageRecord
		"""
		if type_ == "5minutes":
			return self.by5minutes
		elif type_ == "hour":
			return self.byHour
		elif type_ == "day":
			return self.byDay
		elif type_ == "month":
			return self.byMonth
		elif type_ == "year":
			return self.byYear

	def importRecords(self, data):
		for rec in data:
			list_ = self._getList(rec["type"])
			if list_ and list_[-1].end >= rec["end"]:
				continue
			usage = Usage(cputime=rec["usage"]["cputime"], memory=rec["usage"]["memory"],
				diskspace=rec["usage"]["diskspace"], traffic=rec["usage"]["traffic"])
			record = UsageRecord(begin=rec["begin"], end=rec["end"], measurements=rec["measurements"], usage=usage)
			list_.append(record)
		self.save()

	def removeOld(self):
		for type_ in TYPES:
			list_ = self._getList(type_)
			list_[:] = list_[-KEEP_RECORDS[type_]:]
		self.save()

	def update(self):
		self.combine()
		self.removeOld()

	def combine(self):
		lastList = self._getList(TYPES[0])
		now = time.time()
		for type_ in TYPES[1:]:
			list_ = self._getList(type_)
			if list_:
				begin = list_[-1].end
			else:
				begin = _toTime(_prevPoint(_lastPoint(type_, _toPoint(now)), type_))
			end = _toTime(_nextPoint(_toPoint(begin), type_))
			while end <= now:
				records = filter(lambda rec: rec.begin >= begin and rec.end <= end, lastList)
				usage, measurements = _combine(records)
				list_.append(UsageRecord(begin=begin, end=end, usage=usage, measurements=measurements))
				begin = end
				end = _toTime(_nextPoint(_toPoint(end), type_))
			lastList = list_
		self.save()

	def updateFrom(self, sources):
		"""
		:type sources: list of UsageStatistics
		"""
		if not sources:
			return
		lists = [source.by5minutes for source in sources]
		minAll = _toTime(_lastPoint("5minutes", _toPoint(time.time() - 1800)))
		lastAll = max(minAll, min([l[-1].end if l else minAll for l in lists]))
		myList = self.by5minutes
		begin = myList[-1].begin if myList else minAll
		end = _toTime(_nextPoint(_toPoint(begin), "5minutes"))
		while end <= lastAll:
			usage = Usage()
			record = UsageRecord(usage=usage, begin=begin, end=end)
			for l in lists:
				for rec in l:
					if rec.end == end:
						record.measurements += rec.measurements
						record.usage.cputime += rec.usage.cputime
						record.usage.traffic += rec.usage.traffic
						record.usage.memory += rec.usage.memory * (rec.end - rec.begin) / (end-begin)
						record.usage.diskspace += rec.usage.diskspace * (rec.end - rec.begin) / (end-begin)
						break
			myList.append(record)
			begin = end
			end = _toTime(_nextPoint(_toPoint(end), "5minutes"))
		self.save()
		self.update()

	@property
	def latest(self):
		if not self.by5minutes:
			return
		return self.by5minutes[-1].usage.info()


class Quota(EmbeddedDocument):
	monthly = EmbeddedDocumentField(Usage, required=True)
	used = EmbeddedDocumentField(Usage, required=True)
	usedTime = FloatField(db_field='used_time', required=True)
	continousFactor = FloatField(db_field='continous_factor')

	def init(self, cputime, memory, diskspace, traffic, continous_factor):
		self.monthly = Usage(cputime=cputime, memory=memory, diskspace=diskspace, traffic=traffic)
		self.used = Usage()
		self.usedTime = time.time()
		self.continousFactor = continous_factor

	def getFactor(self):
		return max(self.used.cputime/self.monthly.cputime,
				self.used.memory/self.monthly.memory,
				self.used.diskspace/self.monthly.diskspace,
				self.used.traffic/self.monthly.traffic)

	def update(self, usageStats):
		"""
		:type usageStats: UsageStatistics
		"""
		start_of_month = util.startOfMonth(*util.getYearMonth(time.time()))
		if self.usedTime < start_of_month:
			self.used.cputime = 0.0
			self.used.memory = 0.0
			self.used.diskspace = 0.0
			self.used.traffic = 0.0
			self.usedTime = start_of_month
		recs = filter(lambda rec: rec.end > self.usedTime, usageStats.by5minutes)
		factor = 300.0 / util.secondsInMonth(*util.getYearMonth(time.time())) 
		end = self.usedTime
		for rec in recs:
			if rec.usage.cputime > self.monthly.cputime * factor * self.continousFactor:
				self.used.cputime += rec.usage.cputime - self.monthly.cputime * factor * self.continousFactor
			if rec.usage.memory > self.monthly.memory * self.continousFactor:
				self.used.memory += rec.usage.memory * factor - self.monthly.memory * self.continousFactor
			if rec.usage.diskspace > self.monthly.diskspace * self.continousFactor:
				self.used.diskspace += rec.usage.diskspace * factor - self.monthly.diskspace * self.continousFactor
			if rec.usage.traffic > self.monthly.traffic * factor * self.continousFactor:
				self.used.traffic += rec.usage.traffic - self.monthly.traffic * factor * self.continousFactor
			if rec.end > end:
				end = rec.end
		self.usedTime = end

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
		if "continous_factor" in value:
			self.continousFactor = value["continous_factor"]

	def info(self):
		return {
			"used": self.used.info(),
			"monthly": self.monthly.info(),
			"used_time": self.usedTime,
			"continous_factor": self.continousFactor
		}

@util.wrap_task
def aggregate():
	from . import host, elements, connections, topology, auth
	from .host import organization
	for el in elements.Element.objects():
		el.updateUsage()
	for con in connections.Connection.objects():
		con.updateUsage()
	for top in topology.Topology.objects():
		top.updateUsage()
	for user in auth.User.objects():
		user.updateUsage()
	for orga in organization.Organization.objects():
		orga.updateUsage()
	for h in host.Host.objects():
		if h.enabled:
			h.updateUsage()

@util.wrap_task
def updateQuota():
	from . import auth
	for user in auth.User.objects():
		user.updateQuota()
		user.enforceQuota()

scheduler.scheduleRepeated(60, aggregate) #every minute @UndefinedVariable
scheduler.scheduleRepeated(60, updateQuota) #every minute @UndefinedVariable