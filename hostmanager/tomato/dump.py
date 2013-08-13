from datetime import datetime
import sys, os, gzip, time, json, traceback

from .lib.cmd import run, CommandError #@UnresolvedImport
from . import config

envCmds = {
  "disks": ["df", "-h"],
  "processes": ["ps", "faux"],
  "network connections": ["netstat", "-tupen"],
  "bridges": ["brctl", "show"],
  "network interfaces": ["ifconfig", "-a"],
  "routing": ["route", "-n"],
  "routing (ipv6)": ["route", "-6", "-n"],
  "dmesg": ["dmesg"],
  "syslog": ["tail", "/var/log/syslog"],
  "vzctl.log": ["tail", "/var/log/vzctl.log"],
  "openvz": ["vzlist", "-a"],
  "kvmqm": ["qm", "list"],
  "tc": ["tc", "-s", "qdisc", "show"],
  "files": ["find", "/var/lib/tomato/", "-exec", "ls", "-lhd", "{}", ";"],
}

def getEnv():
	data = {}
	for name, cmd in envCmds.iteritems():
		try:
			data[name] = run(cmd)
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
	filename = os.path.join(config.DUMP_DIR, "%s.json.gz" % timestamp)
	timestr = datetime.strftime(datetime.fromtimestamp(timestamp), "%Y-%m-%dT%H:%M:%S.%f%z")
	data = {"environment": getEnv(), "timestamp": timestr}
	if not caller is False:
		data["caller"] = getCaller()
	data.update(kwargs)
	with gzip.open(filename, "wb") as f:
		json.dump(data, f)

def dumpException(**kwargs):
	(type_, value, trace) = sys.exc_info()
	trace = traceback.extract_tb(trace) if trace else None
	dump(caller=False, exception={"type": type_.__name__, "value": str(value), "trace": trace}, **kwargs)

def getCount():
	len(os.listdir(config.DUMP_DIR))
	
def init():
	if not os.path.exists(config.DUMP_DIR):
		os.mkdir(config.DUMP_DIR)