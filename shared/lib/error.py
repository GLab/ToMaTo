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
	return Type


@ErrorType
class InternalError(Error):
	TYPE = "internal"
	HOST_ERROR = "host_error"
	INVALID_NEXT_STATE = "invalid_next_state"
	UPCAST = "upcast"
	MUST_OVERRIDE = "must_override"
	WRONG_DATA = "wrong_data"
	INVALID_STATE = "invalid_state"
	COMMAND_FAILED = "command_failed"
	INVALID_PARAMETER = "invalid_parameter"
	CONFIGURATION_ERROR = "configuration_error"
	RESOURCE_ERROR = "resource_error"


@ErrorType
class UserError(Error):
	TYPE = "user"
	ENTITY_DOES_NOT_EXIST = "entity_does_not_exist"
	UNSUPPORTED_ACTION = "unsupported_action"
	UNSUPPORTED_ATTRIBUTE = "unsupported_attribute"
	INVALID_STATE = "invalid_state"
	ENTITY_BUSY = "entity_busy"
	UNABLE_TO_CONNECT = "unable_to_connect"
	ALREADY_CONNECTED = "already_connected"
	DIFFERENT_USER = "different_user"
	UNSUPPORTED_TYPE = "usupported_type"
	INVALID_CONFIGURATION = "invalid_configuration"
	INVALID_VALUE = "invalid_value"
	NO_DATA_AVAILABLE = "no_data_available"
	COMMAND_FAILED = "command_failed"


@ErrorType
class TransportError(Error):
	TYPE = "transport"
	INVALID_URL = "invalid_url"
	UNAUTHORIZED = "unauthorized"
	SSL = "ssl"
	CONNECT = "connect"
