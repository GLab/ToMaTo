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

def dumpException(**kwargs):
    return dump_lib.dumpException(**kwargs)

def getCount():
    return dump_lib.getCount()
    
def getAll(after=None,list_only=False,include_env=False,compress_env=True):
    return dump_lib.getAll(after=after,list_only=list_only,include_env=include_env,compress=compress_env):

def remove_all_where(before=None,excid=None):
    return dump_lib.remove_all_where(before=before,excid=excid):

def get(filename,include_env=False,compress_env=False):
    return dump_lib.load_dump(filename,load_env=include_env,compress=compress_env)


def init():
    dump_lib.init(envCmds)
