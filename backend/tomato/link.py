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

from .db import *
from . import scheduler
from .host.site import Site
from lib import util, logging #@UnresolvedImport
from .accounting import _lastPoint, _nextPoint, _prevPoint, _toPoint, _toTime, _avg
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

def _combine(records):
	combined = LinkMeasurement()
	combined.measurements = sum([r.measurements for r in records])
	if not combined.measurements:
		combined.loss = 0
		combined.delayAvg = 0
		combined.delayStddev = 0
		return combined
	combined.loss = _avg([(r.loss, r.measurements) for r in records], combined.measurements)
	combined.delayAvg = _avg([(r.delayAvg, r.measurements) for r in records], combined.measurements)
	combined.delayStddev = _avg([(r.delayStddev, r.measurements) for r in records], combined.measurements)
	return combined

class LinkMeasurement(ExtDocument, EmbeddedDocument):
	begin = FloatField(required=True)
	end = FloatField(required=True)
	measurements = IntField(required=True)
	loss = FloatField(required=True)
	delayAvg = FloatField(db_field='delay_avg', required=True)
	delayStddev = FloatField(db_field='delay_stddev', required=True)

	def info(self):
		return {
			"begin": self.begin,
			"end": self.end,
			"measurements": self.measurements,
			"loss": self.loss,
			"delay_avg": self.delayAvg,
			"delay_stddev": self.delayStddev
		}

class LinkStatistics(BaseDocument):
	"""
	:type siteA: host.site.Site
	:type siteB: host.site.Site
	:type single: list of LinkMeasurement
	:type by5minutes: list of LinkMeasurement
	:type byHour: list of LinkMeasurement
	:type byDay: list of LinkMeasurement
	:type byMonth: list of LinkMeasurement
	:type byYear: list of LinkMeasurement
	"""
	siteA = ReferenceField(Site, db_field='site_a', required=True, reverse_delete_rule=CASCADE)
	siteB = ReferenceField(Site, db_field='site_b', required=True, unique_with='siteA', reverse_delete_rule=CASCADE)
	single = ListField(EmbeddedDocumentField(LinkMeasurement), db_field='single')
	by5minutes = ListField(EmbeddedDocumentField(LinkMeasurement), db_field='5minutes')
	byHour = ListField(EmbeddedDocumentField(LinkMeasurement), db_field='hour')
	byDay = ListField(EmbeddedDocumentField(LinkMeasurement), db_field='day')
	byMonth = ListField(EmbeddedDocumentField(LinkMeasurement), db_field='month')
	byYear = ListField(EmbeddedDocumentField(LinkMeasurement), db_field='year')
	meta = {
		'collection': 'link_statistics',
		'ordering': ['siteA', 'siteB'],
		'indexes': [
			('siteA', 'siteB')
		]
	}

	def _getList(self, type_):
		"""
		:rtype: list of UsageRecord
		"""
		if type_ == "single":
			return self.single
		elif type_ == "5minutes":
			return self.by5minutes
		elif type_ == "hour":
			return self.byHour
		elif type_ == "day":
			return self.byDay
		elif type_ == "month":
			return self.byMonth
		elif type_ == "year":
			return self.byYear

	def info(self):
		return {
			"siteA": self.siteA.name,
			"siteB": self.siteB.name,
			"single": [lm.info() for lm in self.single],
			"5minutes": [lm.info() for lm in self.by5minutes],
			"hour": [lm.info() for lm in self.byHour],
			"day": [lm.info() for lm in self.byDay],
			"month": [lm.info() for lm in self.byMonth],
			"year": [lm.info() for lm in self.byYear],
		}

	def add(self, measurement):
		self.single.append(measurement)
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
				combined = _combine(records)
				combined.begin = begin
				combined.end = end
				list_.append(combined)
				begin = end
				end = _toTime(_nextPoint(_toPoint(end), type_))
			lastList = list_
		self.save()


def _measure():
	for siteA in Site.objects.all():
		if not siteA.hosts.count():
			continue
		for siteB in Site.objects.all():
			if siteA.id > siteB.id:
				continue
			try:
				stats = LinkStatistics.objects.get(siteA=siteA, siteB=siteB)
			except LinkStatistics.DoesNotExist:
				stats = LinkStatistics(siteA=siteA, siteB=siteB).save()
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
			logging.logMessage("link measurement", category="link", siteA=siteA.name, siteB=siteB.name, hostA=hostA.name, hostB=hostB.name, result=res)
			stats.add(LinkMeasurement(begin=begin, end=end, loss=res['loss'], delayAvg=res.get("rtt_avg", 0.0)/2.0, delayStddev=res.get("rtt_mdev", 0.0)/2.0, measurements=res["transmitted"]))
	
@util.wrap_task
def taskRun():
	_measure()
	for ls in LinkStatistics.objects:
		ls.update()

def getStatistics(siteA, siteB): #@ReservedAssignment
	siteA = Site.get(siteA)
	siteB = Site.get(siteB)
	if siteA.id > siteB.id:
		siteA, siteB = siteB, siteA
	stats = LinkStatistics.objects.get(siteA=siteA, siteB=siteB)
	return stats.info()

scheduler.scheduleRepeated(60, taskRun) #every minute