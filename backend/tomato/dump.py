from .lib import dump as dump_lib
import misc

envCmds = { 
  "disks": ["df", "-h"],
  "processes": ["ps", "faux"],
  "network connections": ["netstat", "-tupen"],
  "dmesg": ["dmesg", "-xT", "-s", "4096"],
  "syslog": ["tail", "/var/log/syslog"],
  "tc": ["tc", "-s", "qdisc", "show"]
}

def dumpException(**kwargs):
    return dump_lib.dumpException(**kwargs)

def getCount():
    return dump_lib.getCount()
    
def getAll(after=None,list_only=False,include_data=False,compress_data=True):
    return dump_lib.getAll(after=after,list_only=list_only,include_data=include_data,compress_data=compress_data)

def remove_all_where(before=None,excid=None):
    return dump_lib.remove_all_where(before=before, group_id=excid)

def get(dump_id,include_data=False,compress_data=False):
    return dump_lib.load_dump(dump_id,load_data=include_data,compress_data=compress_data)


def init():
    dump_lib.init(envCmds,"Backend",misc.getVersion())
