from datetime import datetime
import sys, os, time, json, traceback, hashlib

from .cmd import run, CommandError #@UnresolvedImport
from .. import config

envCmds = None
    
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

def dump(timestamp=None, caller=None, **kwargs):
	if not timestamp:
		timestamp = time.time()
	filename = os.path.join(config.DUMP_DIR, "%s.json" % timestamp)
	timestr = datetime.strftime(datetime.fromtimestamp(timestamp), "%Y-%m-%dT%H:%M:%S.%f%z")
	data = {"environment": getEnv(), "timestamp": timestr}
	if not caller is False:
		data["caller"] = getCaller()
	data.update(kwargs)
	with open(filename, "w") as f:
		json.dump(data, f, indent=2)

def dumpException(**kwargs):
	(type_, value, trace) = sys.exc_info()
	trace = traceback.extract_tb(trace) if trace else None
	exception = {"type": type_.__name__, "value": str(value), "trace": trace}
	exception_id = hashlib.md5(json.dumps(exception)).hexdigest()
	dump(caller=False, exception=exception, excid=exception_id, **kwargs)

def getCount():
	return len(os.listdir(config.DUMP_DIR))
	
def init(env_cmds):
    global envCmds
    envCmds = env_cmds
    
    if not os.path.exists(config.DUMP_DIR):
		os.mkdir(config.DUMP_DIR)
