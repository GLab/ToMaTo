import os, hashlib, re, sys
import httplib
import inspect, traceback

import anyjson as json
from .exceptionhandling import writedown_current_exception

MODULE = os.environ.get("TOMATO_MODULE", "unknown")
TYPES = {}

def generate_inspect_trace(frame=None):
	res = []
	if frame is None:
		frame = inspect.currentframe()

	# there may be recursive errors if repr(obj) fails for any local variable at any point.
	# thus, we need to figure out whether we have such a recursion before any repr function is called.
	# we detect a recursion by testing whether this function appears multiple times in the stack.
	# the try: outside the repr() or str() function below does not mean that this function is not called in error handling.
	self_count = 0  # count how often this function is in the trace. abort if recursion may be happening
	for frame_ in inspect.getouterframes(frame):
		if frame_[3] == generate_inspect_trace.__name__:
			self_count += 1
		if self_count > 1:  # assume recursion if this function is in the stack 2 or more times
			return []

	for frame_ in inspect.getouterframes(frame):
		obj = {
			'locals': {},
			'file': frame_[1],
			'line_no': frame_[2],
			'function': frame_[3],
			'code': frame_[4]
		}
		for k, v in frame_[0].f_locals.iteritems():
			try:
				v_ = repr(v)
			except:
				try:
					v_ = str(v)
				except:
					v_ = "<unreadable object>"
			if len(v_) > 1000:
				v_ = v_[:1000]
			obj['locals'][k] = v_

		res.append(obj)


	res.reverse()
	return res

class Error(Exception):
	TYPE = "general"
	UNKNOWN = None

	def __init__(self, code=None, message=None, data=None, type=None, todump=None, module=MODULE, httpcode=None, onscreenmessage=None, frame=None, frame_trace=None, trace=None):
		self.type = type or self.TYPE
		self.code = code
		self.message = message
		self.data = data or {}
		self.module = module
		if trace is None:
			self.trace = traceback.extract_stack()
		else:
			self.trace = trace
		if httpcode is None:
			self.httpcode = getCodeHTTPErrorCode(code)
		else:
			self.httpcode = httpcode
		if onscreenmessage is None:
			self.onscreenmessage = message
		else:
			self.onscreenmessage = onscreenmessage
		if todump is not None:
			self.todump = todump  # will be set to False by dump.py after dumping
		else:
			self.todump = not isinstance(self, UserError) or self.module != MODULE
		if frame_trace is None:  # this must be last because it may call repr(self)
			if frame is None:
				self.frame_trace = generate_inspect_trace(inspect.currentframe())
			else:
				self.frame_trace = generate_inspect_trace(frame)
		else:
			self.frame_trace = frame_trace

	
	def group_id(self):
		"""
		Returns a group ID. This should be the same for errors thrown due to the same reason.
		"""
		return hashlib.md5(
						json.dumps({
									'code':self.code,
									'type':self.type,
									'message':re.sub('[a-fA-F0-9]+', 'x', str(self.message)),
									'module':self.module})
						).hexdigest()
	
	def dump(self):
		"""
		dump this error through the dump manager.
		"""
		import dump
		dump.dumpError(self)

	def handle(self):
		"""
		pass this error to the exceptionhandling library
		"""
		writedown_current_exception()

	@property
	def raw(self):
		"""
		creates a dict representation of this error.
		"""
		res = dict(self.__dict__)
		if 'frame_trace' in res:
			del res['frame_trace']
		return res

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
		exception = cls(code=code, message=message, todump=todump,
										frame=inspect.currentframe(), trace=traceback.extract_stack(), *args, **kwargs)
		raise exception

	@classmethod
	def wrap(cls, error, code=UNKNOWN, todump=None, message=None, trace=None, frame_trace=None, frame=None, *args, **kwargs):
		if trace is None:
			try:
				trace = traceback.extract_tb(sys.exc_traceback)
			except:
				pass
		return cls(code=code, message=message or repr(error), todump=todump, trace=trace, frame_trace=frame_trace, frame=frame, *args, **kwargs)

	def __str__(self):
		lines = []
		for k, v in self.data.items():
			if k == "trace":
				lines.append("\ttrace=")
				for l in v.splitlines():
					lines.append("\t\t" + l)
			else:
				lines.append("\t%s=%r" % (k, v))
		return "%s %s error [%s]: %s\n%s" % (self.module, self.type, self.code, self.message or "", "\n".join(lines))

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
	DEPRECATED_CODE = "deprecated_code"

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
	INVALID_RESOURCE_TYPE = "invalid_resource_type" # user requested an existing resource, but it is of the wrong type
	INVALID_DATA = "invalid_value"


@ErrorType
class TransportError(Error):
	TYPE = "transport"
	INVALID_URL = "invalid_url"
	UNAUTHORIZED = "unauthorized"
	SSL = "ssl"
	CONNECT = "connect"
	RPC = "rpc"

@ErrorType
class NetworkError(Error):
	TYPE = "network"
	NOT_REACHABLE = "not reachable"
	
	
# This is used by other functions. It maps error types to onscreen error types (i.e., better readable), and HTTP response codes.
type_translator = {
				# The details here are not really interesting to the user since they cannot do something about it anyway.
				# Thus, just show an internal error with code 500 in this case.
				InternalError.HOST_ERROR:			("Internal Error",httplib.INTERNAL_SERVER_ERROR),
				InternalError.INVALID_NEXT_STATE:	("Internal Error",httplib.INTERNAL_SERVER_ERROR),
				InternalError.UPCAST:				("Internal Error",httplib.INTERNAL_SERVER_ERROR),
				InternalError.MUST_OVERRIDE:		("Internal Error",httplib.INTERNAL_SERVER_ERROR),
				InternalError.WRONG_DATA:			("Internal Error",httplib.INTERNAL_SERVER_ERROR),
				InternalError.INVALID_STATE:		("Internal Error",httplib.INTERNAL_SERVER_ERROR),
				InternalError.COMMAND_FAILED:		("Internal Error",httplib.INTERNAL_SERVER_ERROR),
				InternalError.INVALID_PARAMETER:	("Internal Error",httplib.INTERNAL_SERVER_ERROR),
				InternalError.CONFIGURATION_ERROR:	("Internal Error",httplib.INTERNAL_SERVER_ERROR),
				InternalError.RESOURCE_ERROR:		("Internal Error",httplib.INTERNAL_SERVER_ERROR),
				InternalError.ASSERTION:			("Internal Error",httplib.INTERNAL_SERVER_ERROR),
				
				# These Errors are more important to the user
				UserError.ENTITY_DOES_NOT_EXIST:	("%(entity)s not found",httplib.NOT_FOUND),
				UserError.UNSUPPORTED_ACTION:		("Unsupported Action",httplib.METHOD_NOT_ALLOWED),
				UserError.UNSUPPORTED_ATTRIBUTE:	("Unsupported Attribute",httplib.BAD_REQUEST),
				UserError.INVALID_STATE:			("Invalid State",httplib.CONFLICT),
				UserError.ENTITY_BUSY:				("%(entity)s Busy",httplib.CONFLICT),
				UserError.UNABLE_TO_CONNECT:		("Unable to Connect",httplib.CONFLICT),
				UserError.ALREADY_CONNECTED:		("Already Connected",httplib.CONFLICT),
				UserError.DIFFERENT_USER:			("Different User",httplib.UNAUTHORIZED),
				UserError.UNSUPPORTED_TYPE:			("Unsupported Type",httplib.BAD_REQUEST),
				UserError.INVALID_CONFIGURATION:	("Invalid Configuration",httplib.BAD_REQUEST),
				UserError.INVALID_VALUE:			("Invalid Value",httplib.BAD_REQUEST),
				UserError.NO_DATA_AVAILABLE:		("No Data Available",httplib.CONFLICT),
				UserError.COMMAND_FAILED:			("Command Failed",httplib.INTERNAL_SERVER_ERROR),
				UserError.DENIED:					("Denied",httplib.UNAUTHORIZED),
				UserError.NOT_LOGGED_IN:			("Not Logged in",httplib.UNAUTHORIZED),
				UserError.NOT_EMPTY:				("Not Empty",httplib.CONFLICT),
				UserError.TIMED_OUT:				("Timed Out",httplib.INTERNAL_SERVER_ERROR),
				UserError.AMBIGUOUS:				("Ambiguous",httplib.BAD_REQUEST),
				UserError.ALREADY_EXISTS:			("%s Already Exists",httplib.CONFLICT),
				UserError.NO_RESOURCES:				("No Resources",httplib.SERVICE_UNAVAILABLE),
				UserError.INVALID_RESOURCE_TYPE:	("Invalid Resource Type", httplib.BAD_REQUEST)
				}

def _translate(code):
	return type_translator.get(code, ("Unexpected Error", httplib.INTERNAL_SERVER_ERROR))

def getCodeMsg(code, entity="Entity"):
	return _translate(code)[0] % {'entity':entity}

def getCodeHTTPErrorCode(code):
	return _translate(code)[1]


def assert_(condition, message, code=InternalError.ASSERTION, *args, **kwargs):
	if condition: return
	raise InternalError(message=message, code=code, *args, **kwargs)
