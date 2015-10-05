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
  "vzctl.log": ["tail", "/var/log/vzctl.log"],
  "openvz": ["vzlist", "-a"],
  "kvmqm": ["qm", "list"],
  "tc": ["tc", "-s", "qdisc", "show"],
  "files": ["find", "/var/lib/tomato/", "-exec", "ls", "-lhd", "{}", ";"],
}

def dumpException(**kwargs):
    return dump_lib.dumpException(**kwargs)

def getCount():
    return dump_lib.getCount()

def getRecentDumpCount():
    return dump_lib.get_recent_dumps()
    
def getAll(after=None,list_only=False,include_data=False,compress_data=True):
    return dump_lib.getAll(after=after,list_only=list_only,include_data=include_data,compress_data=compress_data)

def remove_all_where(before=None,excid=None):
    return dump_lib.remove_all_where(before=before, group_id=excid)

def get(dump_id, include_data=False, compress_data=False, dump_on_error=False):
    return dump_lib.load_dump(dump_id, load_data=include_data, compress_data=compress_data, dump_on_error=dump_on_error)


def init():
    dump_lib.init(envCmds,"Hostmanager",hostinfo.hostmanagerVersion())
