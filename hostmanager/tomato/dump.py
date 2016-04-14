from .lib import dump as dump_lib
from .lib.cmd import hostinfo #@UnresolvedImport

envCmds = {
  "disks": ["df", "-h"],
  "processes": ["ps", "faux"],
  "network connections": ["netstat", "-tupen"],
  "bridges": ["brctl", "show"],
  "network interfaces": ["ifconfig", "-a"],
  "routing": ["route", "-n"],
  "routing (ipv6)": ["route", "-6", "-n"],
  "dmesg": ["dmesg", "-xT", "-s", "4096"],
  "syslog": ["tail", "/var/log/syslog"],
  "vzctl_log": ["tail", "/var/log/vzctl.log"],  # key may not contain '.' character
  "openvz": ["vzlist", "-a"],
  "kvmqm": ["qm", "list"],
  "tc": ["tc", "-s", "qdisc", "show"],
  "files": ["find", "/var/lib/tomato/", "-exec", "ls", "-lhd", "{}", ";"],
}

def getCount():
    return dump_lib.getCount()

def dumpException(**kwargs):
    return dump_lib.dumpException(**kwargs)

def getAll(after=None):
    return dump_lib.getAll(after=after,list_only=False,include_data=True)


def init():
    dump_lib.init(envCmds, hostinfo.hostmanagerVersion())
