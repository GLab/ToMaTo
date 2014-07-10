from datetime import datetime
import sys, os, time, json, traceback, hashlib, zlib

from .cmd import run, CommandError #@UnresolvedImport
from .. import config

envCmds = None
#structure for dumps
# { timestamp:string
#   timestamp_unit:float
#   exception_details:dict
#   excid:string
#   environment          # not in RAM, only in the file
#   filename:string      # filename inside the dump directory. used to load environment data on request
# }
dumps = []
    
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
    
    
    

def save_dump(timestamp=None, caller=None, **kwargs):
    global dumps
    
    #collect missing info
    if not timestamp:
		timestamp = time.time()
    timestr = datetime.strftime(datetime.fromtimestamp(timestamp), "%Y-%m-%dT%H:%M:%S.%f%z")
    if not caller is False:
		data["caller"] = getCaller()
        
    #create the dump
    data = {"environment": getEnv(), "timestamp": timestr, "timestamp_unix":timestamp, 'filename':filename}
    data.update(kwargs)
    
    #save it (in the dumps array, and on disk)
    filename = os.path.join(config.DUMP_DIR, "%s.json" % timestamp)
    with open(filename, "w") as f:
		json.dump(data, f, indent=2)
    del data['environment']
    dumps.append(data)
    
#similar arguments as list()
def load_dump(filename,load_env=False,compress=False):
    with open(filename,"r") as f:
        dump = json.load(f)
    if not load_env:
        del dump['environment']
    else:
        if compress:
            dump['environment'] = zlib.compress(str(dump['environment']),9)
    return dump



def dumpException(**kwargs):
	(type_, value, trace) = sys.exc_info()
	trace = traceback.extract_tb(trace) if trace else None
	exception = {"type": type_.__name__, "value": str(value), "trace": trace}
	exception_id = hashlib.md5(json.dumps(exception)).hexdigest()
	dump(caller=False, exception=exception, excid=exception_id, **kwargs)

def getCount():
    global dumps
    return len(dumps)

#param after: if set, only return dumps with timestamp after this
#param list_only: if true, only return dumps with timestamp after this time (time.Time object)
#param include_env: include environment data (may be about 1M!, or set compress true)
#param gzip_env: use zlib to compress environment data. only used if include_env=True. decompress with eval(zlib.decompress(dump['environment']))
def list(after=None,list_only=False,include_env=False,compress=True):
    global dumps
    return_list = []
    for d in dumps:
        if (after is None) or (d['timestamp_unix'] >= after):
            dump = d
            if list_only:
                dump = d['filename']
            elif include_env:
                dump = load_dump(d['filename'],True,True)
            return_list.append(dump)
    return return_list
	
def init(env_cmds):
    global envCmds
    envCmds = env_cmds
    
    if not os.path.exists(config.DUMP_DIR):
		os.mkdir(config.DUMP_DIR)
    else:
        dump_list = os.listdir(config.DUMP_DIR)
        global dumps
        for d in dump_list:
            dump = load_dump(d)
            dumps.append(dump)
