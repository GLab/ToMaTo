import struct
from exception_hierarchy import *
import namespace

def pack(fmt, fields):
  try:
    return struct.pack(fmt, *fields)
  except struct.error, exc:
    raise RepyException(exc)

def unpack(fmt, data):
  try:
    return list(struct.unpack(fmt, data))
  except struct.error, exc:
    raise RepyException(exc)
  
def calcsize(fmt):
  try:
    return struct.calcsize(fmt)
  except struct.error, exc:
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