from datetime import datetime
import sys, os, time, json, traceback, hashlib

import .lib.dump as dump_lib #@UnresolvedImport

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
	return dump_lib.getEnv()

def getCaller(self):
	return dump_lib.getCaller

def dump(timestamp=None, caller=None, **kwargs):
	return dump_lib.dump(timestamp,caller,**kwargs)

def dumpException(**kwargs):
	return dump_lib.dumpException(**kwargs)

def getCount():
	return dump_lib.getCount()
	


def init():
	dump_lib.setEnvCmds(envCmds)
    dump_lib.init()