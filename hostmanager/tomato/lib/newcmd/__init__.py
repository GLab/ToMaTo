
#no parent dependencies

SUPPORT_CHECK_PERIOD = 3 * 60 * 60 # every 3 hours

try:
	from ..error import InternalError as Error
except (ImportError, ValueError,):
	class Error(Exception):
		TYPE = "general"
		UNKNOWN = None
		def __init__(self, code=None, message=None, data=None, type=None, module="testcase"):
			self.type = type or self.TYPE
			self.code = code
			self.message = message
			self.data = data or {}
			self.module = module
		@classmethod
		def check(cls, condition, code, message, *args, **kwargs):
			if condition: return
			raise cls(code, message, *args, **kwargs)
		@classmethod
		def wrap(cls, error, code=UNKNOWN, message=None, *args, **kwargs):
			return cls(code=code, message=message or str(error), *args, **kwargs)
		def __str__(self):
			return "%s %s error [%s]: %s (%r)" % (self.module, self.type, self.code, self.message or "", self.data)
		def __repr__(self):
			return "Error(module=%r, type=%r, code=%r, message=%r, data=%r)" % (self.module, self.type, self.code, self.message, self.data)