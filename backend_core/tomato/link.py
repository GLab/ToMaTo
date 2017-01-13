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
from datetime import timedelta
from .host.site import Site
from lib import util, logging #@UnresolvedImport
from lib.error import UserError
import time, random, threading

TYPES = ["single", "5minutes", "hour", "day", "month", "year"]
KEEP_RECORDS = {
	"single": 10,
	"5minutes": 12,
	"hour": 24,
	"day": 30,
	"month": 12,
	"year": 5,
}
MAX_AGE = {
	"single": timedelta(minutes=2*KEEP_RECORDS["single"]),
	"5minutes": timedelta(minutes=2*5*KEEP_RECORDS["5minutes"]),
	"hour": timedelta(hours=2*KEEP_RECORDS["hour"]),
	"day": timedelta(days=2*KEEP_RECORDS["day"]),
	"month": timedelta(days=2*30*KEEP_RECORDS["month"]),
	"year": timedelta(days=2*365*KEEP_RECORDS["year"])
}

class LinkMeasurement(ExtDocument, EmbeddedDocument):
	begin = FloatField(required=True, db_field="b")
	end = FloatField(required=True, db_field="e")
	measurements = IntField(required=True, db_field="m")
	loss = FloatField(required=True, db_field="l")
	delayAvg = FloatField(db_field='da', required=True)
	delayStddev = FloatField(db_field='ds', required=True)

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

	def quickInfo(self):
		if self.by5minutes:
			fminutes = max(self.by5minutes, key=lambda r: r.end)
		else:
			fminutes = None
		if self.byHour:
			hour = max(self.byHour, key=lambda r: r.end)
		else:
			hour = None
		if self.byDay:
			day = max(self.byDay, key=lambda r: r.end)
		else:
			day = None
		if self.byMonth:
			month = max(self.byMonth, key=lambda r: r.end)
		else:
			month = None
		if self.byYear:
			year = max(self.byYear, key=lambda r: r.end)
		else:
			year = None

		return {
			"5minutes": fminutes,
			"hour": hour,
			"day": day,
			"month": month,
			"year": year
		}

pingingLock = threading.RLock()
pinging = set()

@util.wrap_task
def ping(siteA, siteB, ignore_missing_site=False):

	if isinstance(siteA, str):
		siteA = Site.get(siteA)
	if isinstance(siteB, str):
		siteB = Site.get(siteB)
	if (siteA is None or siteB is None) and ignore_missing_site:
		return
	if siteA is None:
		raise UserError(UserError.ENTITY_DOES_NOT_EXIST, "site does not exist", data={"site": siteA})
	if siteB is None:
		raise UserError(UserError.ENTITY_DOES_NOT_EXIST, "site does not exist", data={"site": siteB})

	key = (siteA, siteB)
	with pingingLock:
		if key in pinging:
			return
		pinging.add(key)
	try:
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
			return
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
			return
		begin = time.time()
		res = hostA.getProxy().host_ping(hostB.address)
		end = time.time()
		logging.logMessage("link measurement", category="link", siteA=siteA.name, siteB=siteB.name, hostA=hostA.name, hostB=hostB.name, result=res)
		stats.add(LinkMeasurement(begin=begin, end=end, loss=res['loss'], delayAvg=res.get("rtt_avg", 0.0)/2.0, delayStddev=res.get("rtt_mdev", 0.0)/2.0, measurements=res["transmitted"]))
	finally:
		with pingingLock:
			pinging.remove(key)

def get_site_pairs():
	pairs = set()
	for siteA in Site.objects.all():
		if not siteA.hosts.count():
			continue
		for siteB in Site.objects.all():
			if siteA.id >= siteB.id:
				continue
			if not siteB.hosts.count():
				continue
			pairs.add((siteA, siteB))
		pairs.add((siteA, siteA))
	return pairs


@util.wrap_task
def housekeep():
	exec_js(js_code("link_housekeep"), now=time.time(), types=TYPES, keep_records=KEEP_RECORDS, max_age={k: v.total_seconds() for k, v in MAX_AGE.items()})

def getStatistics(siteA, siteB):
	_siteA = Site.get(siteA)
	_siteB = Site.get(siteB)
	UserError.check(_siteA is not None, UserError.ENTITY_DOES_NOT_EXIST, "site does not exist", data={"site": siteA})
	UserError.check(_siteB is not None, UserError.ENTITY_DOES_NOT_EXIST, "site does not exist", data={"site": siteB})
	if _siteA.id > _siteB.id:
		_siteA, _siteB = _siteB, _siteA
	try:
		return LinkStatistics.objects.get(siteA=_siteA, siteB=_siteB)
	except LinkStatistics.DoesNotExist:
		ping(_siteA, _siteB)
		return LinkStatistics.objects.get(siteA=_siteA, siteB=_siteB)

def getStatisticsInfo(siteA, siteB): #@ReservedAssignment
	return getStatistics(siteA, siteB).info()


scheduler.scheduleMaintenance(60, get_site_pairs, lambda pair: ping(pair[0], pair[1], ignore_missing_site=True))  # every minute
scheduler.scheduleRepeated(60, housekeep)  # every minute