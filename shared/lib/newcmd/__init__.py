 
class Error(Exception):
	def __init__(self, category, type, message, data=None):
		self.category = category
		self.type = type
		self.message = message
		self.data = data
	def __str__(self):
		s = "Error[%s]: [%s] %s" % (self.category, self.type, self.message)
		if self.data:
			s += ", %r" % self.data
		return s
	def __repr__(self):
		return str(self)
	@classmethod
	def check(cls, condition, *args, **kwargs):
		if not condition:
			raise cls(*args, **kwargs)