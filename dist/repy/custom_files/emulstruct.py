import struct as orig_struct
from exception_hierarchy import *
import namespace

def pack(fmt, fields):
  try:
    return orig_struct.pack(fmt, *fields)
  except orig_struct.error, exc:
    raise RepyException(exc)

def unpack(fmt, data):
  try:
    return list(orig_struct.unpack(fmt, data))
  except orig_struct.error, exc:
    raise RepyException(exc)
  
def calcsize(fmt):
  try:
    return orig_struct.calcsize(fmt)
  except orig_struct.error, exc:
    raise RepyException(exc)
  
METHODS = {
    'struct_pack': {
        'func': pack,
        'args': [namespace.Str(), namespace.List()],
        'raise': [],
        'return': namespace.Str(),
    },
    'struct_unpack': {
        'func': unpack,
        'args': [namespace.Str(), namespace.Str()],
        'raise': [],
        'return': namespace.List(),
    },
    'struct_calcsize': {
        'func': calcsize,
        'args': [namespace.Str()],
        'raise': [],
        'return': namespace.Int(),
    },
}
