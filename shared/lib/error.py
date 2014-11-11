import os
from dump import dumpError

MODULE = os.environ.get("TOMATO_MODULE", "unknown")
TYPES = {}

class Error(Exception):
	TYPE = "general"
	UNKNOWN = None

	def __init__(self, code=None, message=None, data=None, type=None, dump=True, module=MODULE):
		self.type = type or self.TYPE
		self.code = code
		self.message = message
		self.data = data or {}
		self.module = module
		self.dump = dump
		
	def group_id(self):
		return hashlib.md5(
						json.dumps({
									'code':self.code,
									'type':self.type,
									'message':self.message,
									'module':self.module})
						).hexdigest()

	@property
	def raw(self):
		return self.__dict__

	@staticmethod
	def parse(raw):
		return TYPES.get(raw["type"], Error)(**raw)

	@classmethod
	def check(cls, condition, code, message, dump=True *args, **kwargs):
		if condition: return
		excexption = cls(code, message, dump, *args, **kwargs)
		dumpExeption(Exception)
		raise excexption

	@classmethod
	def wrap(cls, error, code=UNKNOWN, message=None, *args, **kwargs):
		return cls(code=code, message=message or str(error), *args, **kwargs)

	def __str__(self):
		return "%s %s error [%s]: %s (%r)" % (self.module, self.type, self.code, self.message or "", self.data)

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
	ASSERTION = "assertion"


@ErrorType
class UserError(Error):
	TYPE = "user"
	ENTITY_DOES_NOT_EXIST = "entity_does_not_exist"
	UNSUPPORTED_ACTION = "unsupported_action"
	UNSUPPORTED_ATTRIBUTE = "unsupported_attribute"
	INVALID_STATE = "invalid_state" # The request is valid but the subject is in a wrong state
	ENTITY_BUSY = "entity_busy"
	UNABLE_TO_CONNECT = "unable_to_connect"
	ALREADY_CONNECTED = "already_connected"
	DIFFERENT_USER = "different_user" # The entity belongs to a different user
	UNSUPPORTED_TYPE = "unsupported_type"
	INVALID_CONFIGURATION = "invalid_configuration" # All of the values are valid in general but the combination is invalid
	INVALID_VALUE = "invalid_value" # One of the values is invalid
	NO_DATA_AVAILABLE = "no_data_available"
	COMMAND_FAILED = "command_failed" # A command executed by the user failed (OpenVZ)
	DENIED = "denied" # This action is denied because of permissions or by policy
	NOT_LOGGED_IN = "not_logged_in" # Request to log in to continue
	NOT_EMPTY = "not_empty" # Container can not be deleted because it is not empty
	TIMED_OUT = "timed_out" # The subject timed out
	AMBIGUOUS = "ambiguous" # The request was ambiguous
	ALREADY_EXISTS = "already_exists" # The object can not be created because it already exists
	NO_RESOURCES = "no_resources" # No resources to satisfy this request


@ErrorType
class TransportError(Error):
	TYPE = "transport"
	INVALID_URL = "invalid_url"
	UNAUTHORIZED = "unauthorized"
	SSL = "ssl"
	CONNECT = "connect"
	RPC = "rpc"


def assert_(condition, message, code=InternalError.ASSERTION, *args, **kwargs):
	if condition: return
	raise InternalError(message=message, code=code, *args, **kwargs)
