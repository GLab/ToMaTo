import struct as orig_struct

class struct:
    pack = orig_struct.pack
    unpack = orig_struct.unpack
    pack_into = orig_struct.pack_into
    unpack_from = orig_struct.unpack_from
    calcsize = orig_struct.calcsize
