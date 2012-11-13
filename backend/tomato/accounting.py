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

from lib import db, attributes, util, logging #@UnresolvedImport
from lib.decorators import *
from datetime import datetime, timedelta
import time

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
    combined.cputime = _sum([(r.cputime, r.measurements) for r in records], measurements)
    combined.diskspace = _avg([(r.diskspace, r.measurements) for r in records], measurements)
    combined.memory = _avg([(r.memory, r.measurements) for r in records], measurements)
    combined.traffic = _sum([(r.traffic, r.measurements) for r in records], measurements)
    return (combined, measurements)

class Usage:
    def __init__(self):
        self.cputime = 0.0
        self.memory = 0.0
        self.diskspace = 0.0
        self.traffic = 0.0

class UsageStatistics(attributes.Mixin, models.Model):
    #records: [UsageRecord]
    attrs = db.JSONField()
    
    class Meta:
        pass

    def init(self, attrs={}):
        self.attrs = {}
        self.begin = time.time()
        self.save()
        
    def remove(self):
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
        record = UsageRecord()
        record.init(self, type_, begin, end, measurements, usage)
        record.save()
        self.records.add(record)
        return record
        
    def removeOld(self):
        for type_ in TYPES:
            for r in self.getRecords(type=type_).order_by("-begin")[KEEP_RECORDS[type_]:]:
                r.delete()
        
    def update(self, now):
        self.combine(now)
        self.removeOld()
        
    def combine(self, now):
        lastType = TYPES[0]
        for type_ in TYPES[1:]:
            begin, end = _lastRange(type_, now)
            if self.getRecords(type=type_, begin=begin, end=end).exists():
                break
            records = self.getRecords(type=lastType, begin__gte=begin, end__lte=end)
            usage, coverage = _combine(begin, end, records)
            self.createRecord(type_, begin, end, coverage, usage)
            lastType = type_
                
    def updateFrom(self, now, others):
        for ts in [now-900, now-600, now-300, now]:
            begin, end = _lastRange("5minutes", ts)
            if self.getRecords(type="5minutes", end=end).exists():
                continue
            usage = Usage()
            measurements = 0
            records = 0
            for o in others:
                for rec in o.getRecords(type="5minutes", end=end):
                    usage.cputime += rec.cputime
                    usage.traffic += rec.traffic
                    usage.memory += rec.memory * (rec.end - rec.begin) / (end-begin)
                    usage.diskspace += rec.diskspace * (rec.end - rec.begin) / (end-begin)
                    measurements += rec.measurements
                    records += 1
            self.createRecord("5minutes", begin, end, measurements, usage)
        self.combine(now)
        self.removeOld()
           
class UsageRecord(models.Model):
    statistics = models.ForeignKey(UsageStatistics, related_name="records")
    type = models.CharField(max_length=10, choices=[(t, t) for t in TYPES], db_index=True) #@ReservedAssignment
    begin = models.FloatField()
    end = models.FloatField(db_index=True)
    measurements = models.IntegerField()
    #using fields to save space
    memory = models.FloatField() #unit: bytes
    diskspace = models.FloatField() #unit: bytes
    traffic = models.FloatField() #unit: bytes
    cputime = models.FloatField() #unit: cpu seconds
    
    class Meta:
        unique_together=(("statistics", "type", "end"),)

    def init(self, statistics, type, begin, end, measurements, usage): #@ReservedAssignment
        self.statistics = statistics
        self.type = type
        self.begin = begin
        self.end = end
        self.measurements = measurements
        self.cputime = usage.cputime
        self.memory = usage.memory
        self.diskspace = usage.diskspace
        self.traffic = usage.traffic
        self.save()

    def info(self):
        return {
            "type": self.type,
            "begin": self.begin,
            "end": self.end,
            "measurements": self.measurements,
            "usage": {"cputime": self.cputime, "diskspace": self.diskspace, "memory": self.memory, "traffic": self.traffic},
        }
        
def synchronize():
    logging.logMessage("sync begin", category="accounting")        
    from . import host, elements, connections, topology
    now = time.time()
    for h in host.getAll():
        try:
            h.updateAccountingData(now)
        except:
            logging.logException(host=h.address)
            print "Error fetching accounting data from %s" % h
    for el in elements.getAll():
        el.updateUsage(now-900)
    for con in connections.getAll():
        con.updateUsage(now-900)
    for top in topology.getAll():
        top.updateUsage(now-900)
    logging.logMessage("sync end", category="accounting")        

task = util.RepeatedTimer(300, synchronize) #every 5 minutes