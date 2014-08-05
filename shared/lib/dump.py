import sys, os, time, json, traceback, hashlib, zlib, threading, datetime, re

from .cmd import run, CommandError #@UnresolvedImport
from .. import config, scheduler

#the format used to convert datetime objects to strings, and back.
#changing this makes all previously created error dumps incompatible and may break the server initialization after upgrades.
timestamp_format = "%Y-%m-%dT%H:%M:%S.%f"

#in the init function, this is set to a number of commands to be run in order to collect environment data, logs, etc.
#these are different in hostmanager and backend, and thus not set in this file, which is shared between these both.
envCmds = {}

#Some version information about ToMaTo. Filled in the Init function
tomato_component = None
tomato_version = None

#this will contain all dumps, except for environment data, since environment data may be huge (about 20K if compressed, around 1M if not compressed)
#environment data is saved to disk loaded on demand if needed.
#the keys are the dumps IDs, for faster access.
dumps = {}
#when adding or removing keys to this array, it has to be locked.
dumps_lock = threading.RLock()

#structure for dumps:
# { timestamp:time.Time  # time the error was detected
#   description:dict     # short description about what happened (i.e., for an exception: position in code, exception subject)
#   type:string        # Teason why the dump was created (i.e., "Exception"). 
#   group_id:string      # an id given to what happened. Group ID should be the same iff it happened due to the same reason (same stack trace, same position in code, same exception, etc).
#   data:any             # anything, depending on what happened. not in RAM due to size, only in the file.
#   dump_id:string       # ID of the dump. used to address the dump
#   software_version:dict     # Information about software component (i.e., hostmanager or backend) and the version
# }
    
#use envCmds to get the environment data.
def getEnv():
	data = {}
	for name, cmd in envCmds.iteritems():
		try:
			data[name] = run(cmd).splitlines()
		except CommandError, err:
			data[name] = str(err)
	return data

def getCaller(self):
	caller = None
	for t in traceback.extract_stack():
			if t[0] == __file__:
					break
			caller = list(t[0:3])
	if caller:
			caller[0] = "..."+caller[0][-22:]
	return caller

#resolve a dump_id to a filename for a file inside the dumps directory
#get the absolute path of a dump for the given filename
#is_meta: if true, this is the filename for the meta file, if false, this is the filename for the data file
def get_absolute_path(dump_id, is_meta):
    filename = None
    if is_meta:
        filename = dump_id + ".meta.json"
    else:
        filename = dump_id + ".data.json"
    return os.path.join(config.DUMP_DIR, filename)

#get a free dump ID
def get_free_dumpid(timestamp):
    with dumps_lock:
        global dumps
        dump_id = str(timestamp)
        if not dump_id in dumps:
            return dump_id
        i = 0
        while dump_id+"_"+str(i) in dumps:
            i+=1
        return dump_id+"_"+str(i)
    
#save dump to a file and store it in the dumps dict. return the dump's ID
#arguments are mostly according to the dump structure.
#param caller: ???
#data should not contain environment data. this will be inserted automatically.
#group_id will be extended to type__group_id. this way, type becomes a namespace.
def save_dump(timestamp=None, caller=None, description={}, type=None, group_id=None, data={}):
    global dumps
    
    #collect missing info
    if not timestamp:
		timestamp = datetime.datetime.now()
    timestr = datetime.datetime.strftime(timestamp, timestamp_format)
    if not caller is False:
		data["caller"] = getCaller()
    data["environment"] = getEnv()
        
    #we need to lock between choosing an ID and saving it to the array.
    with dumps_lock:
        dump_id = get_free_dumpid(timestamp)
            
        #create the dump for saving
        dump_meta = {
            "timestamp": timestr,
            "description":description,
            "type":type,
            "group_id":type + "__" + group_id,
            'dump_id': dump_id,
            "software_version":{"component": tomato_component, "version": tomato_version}
            }
        dump_data = {
            #"data": zlib.compress(json.dumps(data),9),
            #"compressed": True
            "data": json.dumps(data),
            "compressed": False
            }
        
        #save it (in the dumps array, and on disk)
        with open(get_absolute_path(dump_id, True), "w") as f:
    		json.dump(dump_meta, f, indent=2)
        with open(get_absolute_path(dump_id, False), "w") as f:
            json.dump(dump_data, f, indent=2)
        dump_meta['timestamp'] = timestamp
        dumps[dump_id] = dump_meta
    
    return dump_id
    
#load a dump from file.
#similar arguments as list()
#param push_to_dumps: if true, the dump will stored in the dumps dict. this is only useful for the init function.
#param load_from_file: if true, the dump will be loaded from the meta file. if false, the dump will be taken from the dumps dict.
def load_dump(dump_id,load_data=False,compress_data=False,push_to_dumps=False,load_from_file=False):
    global dumps
    with dumps_lock:
        dump = None
        if load_from_file:
            with open(get_absolute_path(dump_id,True),"r") as f:
                dump = json.load(f)
            dump['timestamp'] = datetime.datetime.strptime(dump['timestamp'], timestamp_format)
        elif dump_id in dumps:
            dump = dumps[dump_id]
        else:
            return None
        
        if push_to_dumps:
            dumps[dump_id]=dump
        
        if load_data:
            with open(get_absolute_path(dump_id,False),"r") as f:
                dump_data = json.load(f)
                data = dump_data['data']
                is_compressed = dump_data['compressed']
            if compress_data:
                if is_compressed:
                    dump['data'] = data
                else:
                    dump['data'] = zlib.compress(json.dumps(dump['data']),9)
            else:
                if is_compressed:
                    dump['data'] = json.loads(zlib.decompress(data))
                else:
                    dump['data'] = data
            
        return dump

#remove a dump
def remove_dump(dump_id):
    with dumps_lock:
        global dumps
        if dump_id in dumps:
            os.remove(get_absolute_path(dump_id,True))
            os.remove(get_absolute_path(dump_id,False))
            del dumps[dump_id]
        
#remove all dumps matching a criterion. If criterion is set to None, ignore this criterion.
#before: remove only if the exception is older than this argument. time.Time object
#group_id: remove only if it is an instance of the given group_id
def remove_all_where(before=None,group_id=None):
    global dumps
    #if no criterion is selected, do nothing.
    if before is None and group_id is None:
        return
    
    with dumps_lock:
        for d in list(dumps):
            dump = dumps[d]
            
            #for every criterion: if it is not none and does not apply, do not remove the dump file
            matches_criteria = True
            if before is not None and before<dump['timestamp']:
                matches_criteria = False
            if group_id is not None and group_id!=dump['group_id']:
                matches_criteria = False
            
            if matches_criteria:
                remove_dump(d)

#this will be done daily.                
def auto_cleanup():
    before = datetime.datetime.now() - datetime.timedelta(seconds=config.DUMP_LIFETIME)
    remove_all_where(before=before)
    
#return the total number of error dumps
def getCount():
    global dumps
    return len(dumps)

#param after: if set, only return dumps with timestamp after this
#param list_only: if true, only return dumps with timestamp after this time (time.Time object)
#param include_data: include environment data (may be about 1M!, or set compress_data true). Only used if not list_only
#param compress_data: use zlib to compress environment data. only used if include_data==True. decompress with json.loads(zlib.decompress(dump['environment']))
def getAll(after=None,list_only=False,include_data=False,compress_data=True):
    global dumps
    return_list = []
    for d in dumps:
        if (after is None) or (dumps[d]['timestamp'] >= after):
            dump = dumps[d]
            if list_only:
                dump = d
            elif include_data:
                dump = load_dump(d['dump_id'],True,True)
            return_list.append(dump)
    return return_list
	
    
#initialize dump management on server startup.
def init(env_cmds,tomatoComponent,tomatoVersion):
    with dumps_lock:
        global envCmds
        global dumps
        global tomato_component
        global tomato_version
        envCmds = env_cmds
        tomato_component = tomatoComponent
        tomato_version = tomatoVersion
        
        if not os.path.exists(config.DUMP_DIR):
    		os.mkdir(config.DUMP_DIR)
        else:
            dump_file_list = os.listdir(config.DUMP_DIR)
            for d in dump_file_list:
                if d.endswith('.meta.json'):
                    dump_id = re.sub('\.meta\.json', '', d)
                    dump = load_dump(dump_id,push_to_dumps=True,load_data=False,load_from_file=True)
    scheduler.scheduleRepeated(60*60*24, auto_cleanup, immediate=True)







def dumpException(**kwargs):
    (type_, value, trace) = sys.exc_info()
    trace = traceback.extract_tb(trace) if trace else None
    
    exception = {"type": type_.__name__, "value": str(value), "trace": trace}
    exception_id = hashlib.md5(json.dumps(exception)).hexdigest()
    description={"subject":exception['value'],"type":exception['type']}
    
    data={"exception":exception}
    data.update(**kwargs)
    
    return save_dump(caller=False, description=description, type="Exception", group_id=exception_id, data=data)
