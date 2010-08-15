# -*- coding: utf-8 -*-

import subprocess

def run_shell(cmd, pretend=False):
	if pretend:
		cmd.insert(0,"echo")
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	res=proc.communicate()
	return res[0]

def parse_bool(x):
	"""
	Parses a boolean from a string. The values "True" "true" "False" "false" are recognized, all others result in an exception.
	@param x string
	"""
	if x == False or x == True:
		return x
	return {"true": True, "false": False}.get(x.lower())

class static:
	"""
	Allows to specify a method as static by using method=static(method)
	"""
	def __init__(self, anycallable):
		self.__call__ = anycallable

class curry:
	"""
	Allows to create new methods by currying.
	"""
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
	"""
	An object that allows to read and write its attributes to an xml dom element.
	"""
	
	def __init__ ( self, dom ):
		"""
		Creates a new object
		@param dom the dom to read the attributes from
		"""
		self.decode_xml ( dom )

	def get_attr(self, name, default=None, res_type=None):
		"""
		Retrieves an attribute if it exists or the default value if not
		@param name the name of the attribute
		@param default the default value
		@param res_type the result type of the method
		"""
		if name in self.attributes:
			val = self.attributes[name]
		else:
			val = default
		if res_type:
			return res_type(val)
		else:
			return val
			
	def set_attr(self, name, value):
		"""
		Set an sttribute.
		@param name the name of the attribute
		@param value the value
		"""
		self.attributes[name]=value

	def decode_xml ( self, dom ):
		"""
		Read the attributes from xml
		@param dom the dom to read the attributes from
		"""
		self.attributes = {}
		for key in dom.attributes.keys():
			self.attributes[key] = dom.attributes[key].value

	def encode_xml ( self, dom ):
		"""
		Writes the attributes to xml
		@param dom the dom to write the attributes to
		"""
		for key in self.attributes.keys():
			dom.setAttribute (key, str(self.attributes[key]))
