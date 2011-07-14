import struct as orig_struct

class struct:
    @classmethod
    def pack(cls, *args, **kwargs):
        return orig_struct.pack(*args, **kwargs)
    @classmethod
    def unpack(cls, *args, **kwargs):
        return orig_struct.unpack(*args, **kwargs)
    @classmethod
    def pack_into(cls, *args, **kwargs):
        return orig_struct.pack_into(*args, **kwargs)
    @classmethod
    def unpack_from(cls, *args, **kwargs):
        return orig_struct.unpack_from(*args, **kwargs)
    @classmethod
    def calcsize(cls, *args, **kwargs):
        return orig_struct.calcsize(*args, **kwargs)
