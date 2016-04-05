from .lib import dump as dump_lib
from .lib import dump_autopush
from .lib.versioninfo import getVersionStr

envCmds = { 
}

def dumpException(**kwargs):
    return dump_lib.dumpException(**kwargs)

def getAll(after=None):
    return dump_lib.getAll(after=after,list_only=False,include_data=True)

def init():
    dump_lib.init(envCmds, getVersionStr())
    dump_autopush.init()
