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
MAX_AGE = {
	"5minutes": timedelta(minutes=2*5*KEEP_RECORDS["5minutes"]),
	"hour": timedelta(hours=2*KEEP_RECORDS["hour"]),
	"day": timedelta(days=2*KEEP_RECORDS["day"]),
	"month": timedelta(days=2*30*KEEP_RECORDS["month"]),
	"year": timedelta(days=2*365*KEEP_RECORDS["year"])
}

class Usage(EmbeddedDocument):
	memory = FloatField(default=0.0, db_field="m") #unit: bytes
	diskspace = FloatField(default=0.0, db_field="d") #unit: bytes
	traffic = FloatField(default=0.0, db_field="t") #unit: bytes
	cputime = FloatField(default=0.0, db_field="c") #unit: cpu seconds

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
	begin = FloatField(required=True, db_field="b")
	end = FloatField(required=True, db_field="e")
	measurements = IntField(default=0, db_field="m")
	usage = EmbeddedDocumentField(Usage, required=True, db_field="u")
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
		if self.id:
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

	def updateUsage(self, usageStats):
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
def housekeep():
	try:
		exec_js(js_code("accounting_housekeep"), now=time.time(), types=TYPES, keep_records=KEEP_RECORDS, max_age={k: v.total_seconds() for k, v in MAX_AGE.items()})
	except:
		import traceback
		traceback.print_exc()


@util.wrap_task
def aggregate():
	try:
		exec_js(js_code("accounting_aggregate"), now=time.time(), types=TYPES, keep_records=KEEP_RECORDS, max_age={k: v.total_seconds() for k, v in MAX_AGE.items()})
	except:
		import traceback
		traceback.print_exc()


@util.wrap_task
def updateQuota():
	from . import auth
	for user in auth.User.objects():
		user.updateQuota()
		user.enforceQuota()

scheduler.scheduleRepeated(60, housekeep) #every minute @UndefinedVariable
scheduler.scheduleRepeated(60, aggregate) #every minute @UndefinedVariable
scheduler.scheduleRepeated(60, updateQuota) #every minute @UndefinedVariable