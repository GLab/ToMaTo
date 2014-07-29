import os

MODULE = os.environ.get("TOMATO_MODULE", "unknown")
TYPES = {}

class Error(Exception):
	TYPE = "general"
	UNKNOWN = None

	def __init__(self, code=None, message=None, type=None, data=None, module=MODULE):
		self.type = type or self.TYPE
		self.code = code
		self.message = message
		self.data = data
		self.module = module

	@property
	def raw(self):
		return self.__dict__

	@staticmethod
	def parse(raw):
		return TYPES.get(raw["type"], Error)(**raw)

	@classmethod
	def check(cls, condition, message, *args, **kwargs):
		if condition: return
		raise cls(message=message, *args, **kwargs)

	@classmethod
	def wrap(cls, error, message=None, *args, **kwargs):
		return cls(message=message or str(error), *args, **kwargs)

	def __str__(self):
		return "%s %s error [%s]: %s" % (self.module, self.type, self.code, self.message or "")

	def __repr__(self):
		return "Error(module=%r, type=%r, code=%r, message=%r, data=%r)" % (self.module, self.type, self.code, self.message, self.data)


def ErrorType(Type):
	TYPES[Type.TYPE]=Type


@ErrorType
class InternalError(Error):
	TYPE = "internal"
	HOST_ERROR = "host_error"


@ErrorType
class UserError(Error):
	TYPE = "user"
	ENTITY_DOES_NOT_EXIST = "entity_does_not_exist"
	UNSUPPORTED_ACTION = "unsupported_action"
	UNSUPPORTED_ATTRIBUTE = "unsupported_attribute"
	INVALID_STATE = "invalid_state"
	ENTITY_BUSY = "entity_busy"


@ErrorType
class TransportError(Error):
	TYPE = "transport"
	INVALID_URL = "invalid_url"
	UNAUTHORIZED = "unauthorized"
	SSL = "ssl"
	CONNECT = "connect"
