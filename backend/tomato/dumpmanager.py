import dump
import host

import datetime, time
import threading











#First part: fetching dumps from all the sources.



#this class should not be instantiated. There are two subclasses available: one that can connect to a host, and one that connects to this backend.
class DumpSource:
    last_fetch = None #this time works more like a sequence number for the server.
    
    def __init__(self):
        self.last_fetch = datetime.datetime.utcfromtimestamp(0)
        
    #to be implemented in subclass
    #fetches all dumps from the source, which were thrown after after.
    #after is a datetime object and will be used unchanged.
    def _fetch(self,after):
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
        fetch_results = self._fetch(last_fetch_better)
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
        
    def _fetch(self,after): #TODO: return None if unreachable
        return self.host_obj.getProxy().dump_list(after=after,list_only=False,include_data=False,compress_data=True)
    
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
        
    def _fetch(self,after):
        return dump.getAll(after=after,list_only=False,include_data=False,compress_data=True)
    
    def _clock_offset(self):
        return datetime.timedelta(seconds=0)
    
    def _source_name(self):
        return "backend"
        
        
#contains all dump sources
dumpsources=[]

#only one thread may write to the dump table at a time.
lock = threading.RLock()

def insert_dump(dump,source): #TODO: add database table and actually do this
    with lock:
        source_name = source._source_name()
        return

def update_source(source):
    new_entries = source.getUpdates()
    for e in new_entries:
        insert_dump(e,source)
    
def update_all():
    global dumpsources
    for s in list(dumpsources): #a removed host while iterating is caught by this, since dumpSource.getUpdates() will return [] in this case
        threading.thread.start_new(update_source,(s)) #host might need longer to respond. no reason not to parallelize this
        time.sleep(1) #do not connect to all hosts at the same time. There is no need to rush.

def remove_host(host_obj): #TODO: call this from host.py
    global dumpsources
    with lock:
        for s in list(dumpsources):
            if s.matches_host(host_obj):
                dumpsources.remove(s)
                break
            

def add_host(host_obj): #TODO: call this from host.py
    global dumpsources
    s = HostDumpSource(host_obj)
    with lock:
        dumpsources.append(s)
    threading.thread.start_new(update_source, (s)) #this update should not interfere with the actual host_add call.
        

def init():
    global dumpsources
    with lock:
        dumpsources.append(BackendDumpSource())
        for h in host.getAll():
            dumpsources.append(HostDumpSource(h))
    #TODO: start a task to call updateAll repeatedly






# Second Part: Access to known dumps

#TODO: actually provide these methods