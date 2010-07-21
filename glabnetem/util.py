# -*- coding: utf-8 -*-

def parse_bool(x):
	if x == False or x == True:
		return x
	return {"true": True, "false": False}.get(x.lower())

class static:  
    def __init__(self, anycallable):
        self.__call__ = anycallable
        
class curry:
    def __init__(self, fun, *args, **kwargs):
        self.fun = fun
        self.pending = args[:]
        self.kwargs = kwargs.copy()

    def __call__(self, selfref, *args, **kwargs):
        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs

        return self.fun(selfref, *(self.pending + args), **kw)

class XmlObject(object):
	def __init__ ( self, dom ):
		self.decode_xml ( dom )

	def get_attr(self, name, default=None, res_type=None):
		if name in self.attributes:
			val = self.attributes[name]
		else:
			val = default
		if res_type:
			return res_type(val)
		else:
			return val
	def set_attr(self, name, value):
		self.attributes[name]=value

	def decode_xml ( self, dom ):
		self.attributes = {}
		for key in dom.attributes.keys():
			self.attributes[key] = dom.attributes[key].value

	def encode_xml ( self, dom ):
		for key in self.attributes.keys():
			dom.setAttribute (key, str(self.attributes[key]))
