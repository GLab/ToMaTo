import datetime, time, json, zlib, threading, thread
from django.db import models

import host
from .lib import attributes, db #@UnresolvedImport
from . import scheduler,config,currentUser,fault
    
    
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
    #
def getAll_group():
    return ErrorGroup.objects.all()


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
        d = self.getSource().dump_fetch_with_data(self.dump_id,True)
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

def getAll_dumps():
    return ErrorDump.objects.all()




#First part: fetching dumps from all the sources.



#this class should not be instantiated. There are two subclasses available: one that can connect to a host, and one that connects to this backend.
class DumpSource:
    #dump_last_fetch = None
        
    #to be implemented in subclass
    #fetches all dumps from the source, which were thrown after *after*.
    #after is a datetime object and will be used unchanged.
    #if this throws an exception, the fetching is assumed to have been unsuccessful.
    def dumps_fetch_list(self,after):
        return None
    
    #to be implemented in subclass
    #fetches all data about the given dump.
    #if this throws an exception, the fetching is assumed to have been unsuccessful.
    def dump_fetch_with_data(self,dump_id,keep_compressed=True):
        return None
    
    #to be implemented in a subclass
    #if the source has its clock before the backend, and an error is thrown in exactly this difference,
    #the dump would be skipped.
    #Thus, use the known clock offset to fetch dumps that might have occurred in this phase (i.e., right after the last fetch)
    #returns a datetime.timedelta. should be 0 if the source's clock is ahead, and >0 if the source's clock is behind
    def dump_clock_offset(self):
        return None
    
    #to be implemented in a subclass
    #returns a string to uniquely identify the source
    def dump_source_name(self):
        return None
    
    #override for HostDumpSource. Return true if the given host is this one
    def dump_matches_host(self,host_obj):
        return False
    
    def dump_getUpdates(self):
        this_fetch_time = datetime.datetime.now() - self._clock_offset()
        try:
            fetch_results = self._fetch_list(self.dump_last_fetch)
            self.dump_last_fetch = this_fetch_time
            return fetch_results
        except:
            return []
    
#fetches from this backend
class BackendDumpSource(DumpSource):
    dump_last_fetch = None
    def __init__(self):
        self.dump_last_fetch = datetime.datetime.utcfromtimestamp(0)
        
    def dump_fetch_list(self,after):
        import dump
        return dump.getAll(after=after,list_only=False,include_data=False,compress_data=True)
    
    def dump_fetch_with_data(self,dump_id,keep_compressed=True):
        import dump
        dump = dump.get(dump_id,include_data=True,compress_data=True)
        if not keep_compressed:
            dump['data'] = json.loads(zlib.decompress(dump['data']))
        return dump
    
    def dump_clock_offset(self):
        return datetime.timedelta(seconds=0)
    
    def dump_source_name(self):
        return "backend"
        
        
def getDumpSources():
    sources = [BackendDumpSource()]
    hosts = host.getAll()
    for host in hosts:
        sources.append(host)
    return sources

#only one thread may write to the dump table at a time.
lock_db = threading.RLock()

def find_source_by_name(source_name):
    for s in getDumpSources():
        if s.dump_source_name == source_name:
            return s
    return None

def insert_dump(dump,source):
    with lock_db:
        source_name = source.dump_source_name()
        must_fetch_data = False
        
        #check whether a dump from the source with given dump_id exists. if so, don't do anything
        if get_dump(source_name, dump['dump_id']) is not None:
            return
        
        # check whether the group ID already exists. If not, create it,
        # remember to fetch dump data in the end, and email developer users
        if get_group(dump['group_id']) is None:
            from auth import mailFlaggedUsers, Flags
            must_fetch_data = True
            create_group(dump['group_id'])
            mailFlaggedUsers(Flags.ErrorNotify, "[ToMaTo Devs] New Error Group", "A new group of error has been found, with ID %s. It has first been observed on %s." % (dump['group_id'],source._source_name()))
        
        #insert the dump.
        dump_db = create_dump(dump, source)
        
        #if needed, load data
        if must_fetch_data:
            dump_db.fetch_data_from_source()
        

def update_source(source):
    new_entries = source.dump_getUpdates()
    for e in new_entries:
        insert_dump(e,source)
    
def update_all():
    def cycle_all():
        for s in getDumpSources(): #a removed host while iterating is caught by this, since dumpSource.getUpdates() will return [] in this case
            thread.start_new_thread(update_source,(s,)) #host might need longer to respond. no reason not to parallelize this
            time.sleep(1) #do not connect to all hosts at the same time. There is no need to rush.
    thread.start_new_thread(cycle_all,())

def init():
    scheduler.scheduleRepeated(config.DUMP_COLLECTION_INTERVAL, update_all, immediate=True)



# Second Part: Access to known dumps for API

def checkPermissions():
        user = currentUser()
        if not user.hasFlag(Flags.Debug):
            fault.raise_("Not enough permissions")
            return False
        return True

def api_errorgroup_list():
    if checkPermissions():
        with lock_db:
            return getAll_group()

def api_errorgroup_modify(group_id,attrs):
    if checkPermissions():
        with lock_db:
            for i in attrs.keys():
                if not i=="description":
                    fault.raise_("Unsupported attribute for error group: %s" % i, fault.USER_ERROR)
            get_group(group_id).update_description(attrs['description'])

def api_errorgroup_info(group_id,include_dumps=False):
    if checkPermissions():
        with lock_db:
            group = get_group(group_id)
            res = group.info()
            if include_dumps:
                res['dumps'] = []
                for i in list(group.dumps):
                    res['dumps'].append(i.info())
            return res
        
        
def api_errordump_list(group_id=None, source=None, data_available=None):
    if checkPermissions():
        with lock_db:
            dumps = getAll_dumps()
            res = []
            for d in dumps:
                di = d.info(include_data=False)
                
                append_to_res=True
                if not group_id is None and di['group_id'] == group_id:
                    append_to_res = False
                if not source is None and di['source'] == source:
                    append_to_res = False
                if not data_available is None and di['data_available'] == data_available:
                    append_to_res = False
                
                if append_to_res:
                    res.append(di)
            return res

def api_errordump_info(source,dump_id,include_data=False):
    if checkPermissions():
        with lock_db:
            return get_dump(source, dump_id).info(include_data = include_data)
    
#TODO: functionality to remove error dumps and error groups.
