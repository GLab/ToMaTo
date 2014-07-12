import datetime, time, json, zlib, threading
from django.db import models

import dump
import host
from lib import attributes, db
from auth import mailFlaggedUsers, Flags
from . import scheduler,config
    
    
#Zero-th part: database stuff
    
class ErrorGroup(models.Model):
    group_id = models.CharField(max_length=255, primary_key=True)
    description = models.CharField(max_length=255)
    #dumps: [ErrorDump]
    
    def update_description(self,description):
        self.description = description
        self.save()
        
    def info(self):
        return {
            'group_id':self.group_id,
            'description':self.description
        }
        
def create_group(group_id):
    gr = ErrorGroup.objects.create(
        group_id=group_id,
        description=group_id
      )
    gr.save()
    return gr


def get_group(group_id):
    try:
        return ErrorGroup.objects.get(group_id=group_id)
    except ErrorGroup.DoesNotExist:
        return None


class ErrorDump(attributes.Mixin, models.Model):
    source = models.CharField(max_length=255)
    dump_id = models.CharField(max_length=255)
    group = models.ForeignKey(ErrorGroup, related_name="dumps")
    description = db.JSONField()
    data = attributes.attribute("data", unicode, None)
    data_available = attributes.attribute("data_available", bool, False)
    type = attributes.attribute("origin", unicode, "")
    software_version = attributes.attribute("software_version", dict, "")
    timestamp = attributes.attribute("timestamp", float, 0)
    
    class Meta:
        unique_together=(("source","dump_id"))
        
    def getSource(self):
        return find_source_by_name(self.source)

    def modify_data(self,data,is_compressed=True):
        if data is None:
            self.data = None
            self.data_available = False
            self.save()
            return
        data_toinsert = None
        if is_compressed:
            data_toinsert = data
        else:
            data_toinsert = zlib.compress(json.dumps(data),9)
        self.data = data_toinsert
        self.data_available = True
        self.save()
        
    def fetch_data_from_source(self):
        d = self.getSource()._fetch_with_data(self.dump_id,True)
        self.modify_data(d, True)
        
    def info(self,include_data=False):
        dump = {
            'source':self.source,
            'dump_id':self.dump_id,
            'group_id':self.group.group_id,
            'group_description':self.group.description,
            'description':self.description,
            'type':self.type,
            'software_version':self.software_version,
            'timestamp':self.timestamp
            }
        if include_data:
            if not self.data_available:
                self.fetch_data_from_source()
            dump['data'] = json.loads(zlib.decompress(self.data))
        else:
            dump['data_available'] = self.data_available
        return dump
        
def create_dump(dump,source):
    d = ErrorDump.objects.create(
        source=source._source_name(),
        dump_id=dump['dump_id'],
        group_id=dump['group_id'],
        description=dump['description'],
        type=dump['type'],
        software_version=dump['software_version'],
        timestamp=dump['timestamp']
      )
    d.save()
    return d

def get_dump(source_name,dump_id):
    try:
        return ErrorDump.objects.get(source=source_name,dump_id=dump_id)
    except ErrorDump.DoesNotExist:
        return None






#First part: fetching dumps from all the sources.



#this class should not be instantiated. There are two subclasses available: one that can connect to a host, and one that connects to this backend.
class DumpSource:
    last_fetch = None #this time works more like a sequence number for the server.
    
    def __init__(self):
        self.last_fetch = datetime.datetime.utcfromtimestamp(0)
        
    #to be implemented in subclass
    #fetches all dumps from the source, which were thrown after after.
    #after is a datetime object and will be used unchanged.
    def _fetch_list(self,after):
        return None
    
    #to be implemented in subclass
    #fetches all data about the given dump.
    def _fetch_with_data(self,dump_id,keep_compressed=True):
        return None
    
    #to be implemented in a subclass
    #if the source has its clock before the backend, and an error is thrown in exactly this difference,
    #the dump would be skipped.
    #Thus, use the known clock offset to fetch dumps that might have occurred in this phase (i.e., right after the last fetch)
    #returns a datetime.timedelta. should be 0 if the source's clock is ahead, and >0 if the source's clock is behind
    def _clock_offset(self):
        return None
    
    #to be implemented in a subclass
    #returns a string to uniquely identify the source
    def _source_name(self):
        return None
    
    #override for HostDumpSource. Return true if the given host is this one
    def matches_host(self,host_obj):
        return False
    
    def getUpdates(self):
        this_fetch_time = datetime.datetime.now()
        last_fetch_better = self.last_fetch - self._clock_offset()
        fetch_results = self._fetch_list(last_fetch_better)
        if fetch_results is not None: # this might have happened due to source downtime. we still need the dumps we just tried to fetch.
            self.last_fetch = this_fetch_time
            return fetch_results
        else:
            return []
    
#fetches from a host (host is given in constructor)
class HostDumpSource(DumpSource):
    host_obj = None
    host_name = None
    def __init__(self,host_obj):
        super(HostDumpSource, self).__init__()
        self.host_obj = host_obj
        self.host_name = host_obj.info()['name']
        
    def _fetch_list(self,after): #TODO: return None if unreachable
        return self.host_obj.getProxy().dump_list(after=after,list_only=False,include_data=False,compress_data=True)
    
    def _fetch_with_data(self,dump_id,keep_compressed=True):
        dump = self.host_obj.getProxy().dump_info(dump_id,include_data=True,compress_data=True)
        if not keep_compressed:
            dump['data'] = json.loads(zlib.decompress(dump['data']))
        return dump
    
    def _clock_offset(self):
        diff = max(0,self.host_obj.hostInfo['time_diff']) #TODO: what does time_diff>0 mean? host ahead or backend ahead? iff >0 == host ahead, negate time_diff
        return datetime.timedelta(seconds=diff)
    
    def _source_name(self):
        return "host:%s" % self.host_name
    
    def matches_host(self, host_obj):
        return self.host_name == host_obj.info()['name']
    
#fetches from this backend
class BackendDumpSource(DumpSource):
    def __init__(self):
        super(BackendDumpSource, self).__init__()
        
    def _fetch_list(self,after):
        return dump.getAll(after=after,list_only=False,include_data=False,compress_data=True)
    
    def _fetch_with_data(self,dump_id,keep_compressed=True):
        dump = dump.get(dump_id,include_data=True,compress_data=True)
        if not keep_compressed:
            dump['data'] = json.loads(zlib.decompress(dump['data']))
        return dump
    
    def _clock_offset(self):
        return datetime.timedelta(seconds=0)
    
    def _source_name(self):
        return "backend"
        
        
#contains all dump sources
dumpsources=[]
lock_sources = threading.RLock()

#only one thread may write to the dump table at a time.
lock_db = threading.RLock()

def find_source_by_name(source_name):
    with lock_sources:
        global dumpsources
        for s in list(dumpsources):
            if s._source_name == source_name:
                return s
    return None

def insert_dump(dump,source): #TODO: add database table and actually do this
    with lock_db:
        source_name = source._source_name()
        must_fetch_data = False
        
        #check whether a dump from the source with given dump_id exists. if so, don't do anything
        if get_dump(source_name, dump['dump_id']) is not None:
            return
        
        # check whether the group ID already exists. If not, create it,
        # remember to fetch dump data in the end, and email developer users
        if get_group(dump['group_id']) is None:
            must_fetch_data = True
            create_group(dump['group_id'])
            mailFlaggedUsers(Flags.Debug, "[ToMaTo Devs] New Error Group", "A new group of error has been found, with ID %s. It has first been observed on %s." % (dump['group_id'],source._source_name()))
            #TODO: is this the right flag?
        
        #insert the dump.
        dump_db = create_dump(dump, source)
        
        #if needed, load data
        if must_fetch_data:
            dump_db.fetch_data_from_source()
        

def update_source(source):
    new_entries = source.getUpdates()
    for e in new_entries:
        insert_dump(e,source)
    
def update_all():
    global dumpsources
    def cycle_all():
        for s in list(dumpsources): #a removed host while iterating is caught by this, since dumpSource.getUpdates() will return [] in this case
            threading.thread.start_new(update_source,(s)) #host might need longer to respond. no reason not to parallelize this
            time.sleep(1) #do not connect to all hosts at the same time. There is no need to rush.
    threading.thread.start_new(cycle_all)

def remove_host(host_obj):
    global dumpsources
    with lock_sources:
        for s in list(dumpsources):
            if s.matches_host(host_obj):
                dumpsources.remove(s)
                break
            

def add_host(host_obj):
    global dumpsources
    s = HostDumpSource(host_obj)
    with lock_sources:
        dumpsources.append(s)
    threading.thread.start_new(update_source, (s)) #this update should not interfere with the actual host_add call.
        

def init():
    global dumpsources
    with lock_sources:
        dumpsources.append(BackendDumpSource())
        for h in host.getAll():
            dumpsources.append(HostDumpSource(h))
    scheduler.scheduleRepeated(config.DUMP_COLLECTION_INTERVAL, update_all, immediate=True)



# Second Part: Access to known dumps

#TODO: actually provide these methods