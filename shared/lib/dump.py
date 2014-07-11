from datetime import datetime
import sys, os, time, json, traceback, hashlib, zlib

from .cmd import run, CommandError #@UnresolvedImport
from .. import config

#the format used to convert datetime objects to strings, and back.
#changing this makes all previously created error dumps incompatible and may break the server initialization.
timestamp_format = "%Y-%m-%dT%H:%M:%S.%f%z"

#in the init function, this is set to a number of commands to be run in order to collect environment data, logs, etc.
#these are different in hostmanager and backend, and thus not set in this file, which is shared between these both.
envCmds = {}

#this will contain all dumps, except for environment data, since environment data may be huge (about 20K if compressed, around 1M if not compressed)
#environment data is saved to disk loaded on demand if needed.
#the keys are the dumps filename, for faster access.
dumps = {}

#structure for dumps:
# { timestamp:time.Time  # time the error was detected
#   exception_details:dict  # the exception object
#   excid:string         # an id given to an exception. ID should be the same iff it happened due to the same reason (same stack trace, same position in code, same exception, etc).
#   environment          # not in RAM, only in the file. a dict consisting of key,value. has the same keys as the envCmds dict, and values are the excecution results of the values in envCmds
#   filename:string      # filename inside the dump directory. used to load environment data on request
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

#dumps are identified by their filename relative to the dump directory.
#get the absolute path of a dump for the given filename    
def get_absolute_path(filename):
    return os.path.join(config.DUMP_DIR, filename)
    
#save dump to a file and store it in the dumps dict.
def save_dump(timestamp=None, caller=None, **kwargs):
    global dumps
    
    #collect missing info
    if not timestamp:
		timestamp = time.time()
    timestr = datetime.strftime(datetime.fromtimestamp(timestamp), timestamp_format)
    if not caller is False:
		data["caller"] = getCaller()
        
    #create the dump
    data = {"environment": getEnv(), "timestamp": timestr, 'filename':filename}
    data.update(kwargs)
    
    #save it (in the dumps array, and on disk)
    filename = "%s.json" % timestamp
    with open(get_absolute_path(filename), "w") as f:
		json.dump(data, f, indent=2)
    del data['environment']
    data['timestamp'] = timestamp
    dumps[filename] = data
    
#load a dump from file.
#similar arguments as list()
#param push_to_dumps: if true, the dump will be stored in the dumps dict. this is only useful for the init function.
def load_dump(filename,load_env=False,compress=False,push_to_dumps=False):
    with open(get_absolute_path(filename),"r") as f:
        dump = json.load(f)
        
    dump['timestamp'] = datetime.strptime(dump['timestamp'], timestamp_format)
    if not load_env:
        del dump['environment']
    elif compress:
        dump['environment'] = zlib.compress(str(dump['environment']),9)
        
    if push_to_dumps:
        global dumps
        dumps[d]=dump
        
    return dump

#remove a dump
def remove_dump(filename):
    global dumps
    if filename in dumps:
        os.remove(get_absolute_path(filename))
        del dumps[filename]
        
#remove all dumps matching a criterion. If criterion is set to None, ignore this criterion.
#before: remove only if the exception is older than this argument. time.Time object
#excid: remove only if it is an instance of the given exception id
def remove_all_where(before=None,excid=None):
    global dumps
    #if no criterion is selected, do nothing.
    if before is None and excid is None:
        return
    
    for d in dumps:
        dump = dumps[d]
        
        #for every criterion: if it is not none and does not apply, do not remove the dump file
        matches_criteria = True
        if before is not None and before<dump['timestamp_unix']:
            matches_criteria = False
        if excid is not None and excid!=dump['excid']:
            matches_criteria = False
        
        if matches_criteria:
            remove_dump(d)

#return the total number of error dumps
def getCount():
    global dumps
    return len(dumps)

#param after: if set, only return dumps with timestamp after this
#param list_only: if true, only return dumps with timestamp after this time (time.Time object)
#param include_env: include environment data (may be about 1M!, or set compress true). Only used if not list_only
#param compress: use zlib to compress environment data. only used if include_env==True. decompress with eval(zlib.decompress(dump['environment']))
def getAll(after=None,list_only=False,include_env=False,compress=True):
    global dumps
    return_list = []
    for d in dumps:
        if (after is None) or (d['timestamp_unix'] >= after):
            dump = dumps[d]
            if list_only:
                dump = d['filename']
            elif include_env:
                dump = load_dump(d['filename'],True,True)
            return_list.append(dump)
    return return_list
        


def dumpException(**kwargs):
	(type_, value, trace) = sys.exc_info()
	trace = traceback.extract_tb(trace) if trace else None
	exception = {"type": type_.__name__, "value": str(value), "trace": trace}
	exception_id = hashlib.md5(json.dumps(exception)).hexdigest()
	dump(caller=False, exception=exception, excid=exception_id, **kwargs)
	
    
#initialize dump management on server startup.
def init(env_cmds):
    global envCmds
    global dumps
    envCmds = env_cmds
    
    if not os.path.exists(config.DUMP_DIR):
		os.mkdir(config.DUMP_DIR)
    else:
        dump_list = os.listdir(config.DUMP_DIR)
        for d in dump_list:
            dump = load_dump(d,push_to_dumps=True)
