from .lib import dump as dump_lib
from .lib.versioninfo import getVersionStr

envCmds = { 
}

def dumpException(**kwargs):
    return dump_lib.dumpException(**kwargs)

def getCount():
    return dump_lib.getCount()
    
def getAll(after=None,list_only=False,include_data=False,compress_data=True):
    return dump_lib.getAll(after=after,list_only=list_only,include_data=include_data,compress_data=compress_data)

def remove_all_where(before=None,excid=None):
    return dump_lib.remove_all_where(before=before, group_id=excid)

def get(dump_id, include_data=False, compress_data=False, dump_on_error=False):
    return dump_lib.load_dump(dump_id, load_data=include_data, compress_data=compress_data, dump_on_error=dump_on_error)


def init():
    dump_lib.init(envCmds, "backend_core", getVersionStr())
