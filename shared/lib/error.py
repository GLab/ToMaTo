import os, hashlib, json
from dump import dumpError

MODULE = os.environ.get("TOMATO_MODULE", "unknown")
TYPES = {}

class Error(Exception):
	TYPE = "general"
	UNKNOWN = None

	def __init__(self, code=None, message=None, data=None, type=None, todump=None, module=MODULE, httpcode=500,onscreenmessage=None):
		self.type = type or self.TYPE
		self.code = code
		self.httpcode = httpcode
		self.message = message
		self.data = data or {}
		self.module = module
		if onscreenmessage is None:
			self.onscreenmessage = message
		else:
			self.onscreenmessage = onscreenmessage
		if todump is not None:
			self.todump = todump
		else:
			self.todump = not isinstance(self, UserError)
		
	
	def group_id(self):
		"""
		Returns a group ID. This should be the same for errors thrown due to the same reason.
		"""
		return hashlib.md5(
						json.dumps({
									'code':self.code,
									'type':self.type,
									'message':self.message,
									'module':self.module})
						).hexdigest()
	
	def dump(self):
		"""
		dump this error through the dump manager.
		"""
		dumpError(self)

	@property
	def raw(self):
		"""
		creates a dict representation of this error.
		"""
		return self.__dict__

	@property
	def rawstr(self):
		"""
		creates a string representation of this error.
		"""
		return json.dumps(self.raw)

	@staticmethod
	def parse(raw):
		return TYPES.get(raw["type"], Error)(**raw)
	
	@staticmethod
	def parsestr(rawstr):
		"""
		creates an Error object from the string representation
		"""
		raw = json.loads(rawstr)
		return Error.parse(raw)

	@classmethod
	def check(cls, condition, code, message, todump=None, *args, **kwargs):
		if condition: return
		exception = cls(code=code, message=message,todump=todump, *args, **kwargs)
		exception.dump()
		raise exception

	@classmethod
	def wrap(cls, error, code=UNKNOWN, message=None, *args, **kwargs):
		return cls(code=code, message=message or str(error), *args, **kwargs)

	def __str__(self):
		return "%s %s error [%s]: %s (%r)" % (self.module, self.type, self.code, self.message or "", self.data)

	def __repr__(self):
		return "Error(module=%r, type=%r, code=%r, message=%r, data=%r, onscreenmessage=%r)" % (self.module, self.type, self.code, self.message, self.data,self.onscreenmessage)


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
	INVALID_DATA = "invalid data" #The user sent invalid data in a request (i.e., webfrontend forms)


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
