import ssl, socket, SocketServer, inspect, threading, thread, sys
from ..error import TransportError

JSON = False
try:
	if not JSON:
		import simplejson as json

		JSON = json.__name__
except ImportError:
	pass
try:
	if not JSON:
		import ujson as json

		JSON = json.__name__
except ImportError:
	pass
if not JSON:
	import json

	JSON = json.__name__
# print "Using %s" % JSON


class SSLServer(SocketServer.TCPServer):
	def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, **sslargs):
		self.allow_reuse_address = True
		SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass, False)
		self.socket = ssl.wrap_socket(self.socket, server_side=True, **sslargs)
		self.children = set()
		self.children_lock = threading.RLock()
		self.children_event = threading.Event()
		if bind_and_activate:
			self.server_bind()
			self.server_activate()
		self.running = True

	def shutdown_request(self, request):
		try:
			request.shutdown(socket.SHUT_RDWR)
		except:
			pass
		with self.children_lock:
			self.children.remove(request)
			if not self.running and not self.children:
				self.children_event.set()

	def on_ssl_error(self, error):
		import traceback

		traceback.print_exc(error)

	def shutdown(self):
		self.running = False
		SocketServer.TCPServer.shutdown(self)
		with self.children_lock:
			if not self.children:
				return
		self.children_event.wait()

	def get_request(self):
		try:
			req = SocketServer.TCPServer.get_request(self)
			with self.children_lock:
				self.children.add(req[0])
			return req
		except Exception, exc:
			try:
				self.on_ssl_error(exc)
			except:
				pass
			raise exc


class SSLConnection:
	def __init__(self, server_address, **sslargs):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket = ssl.wrap_socket(self.socket, **sslargs)
		self.socket.connect(server_address)
		self.rfile = self.socket.makefile('rb', -1)
		self.wfile = self.socket.makefile('wb', 0)

	def read(self, size=-1):
		return self.rfile.read(size)

	def readLine(self):
		return self.rfile.readline()

	def write(self, data):
		self.wfile.write(data)

	def writeLine(self, data):
		self.wfile.write(data + "\n")
		self.wfile.flush()

	def close(self):
		self.rfile.close()
		self.wfile.close()
		self.socket.close()


def method_info(func):
	try:
		argspec = inspect.getargspec(func)
		args = argspec.args
		defaults = argspec.defaults
	except:
		return {"docs": func.__doc__}
	if not defaults:
		defaults = []
	if args and args[0] == "self":
		args = args[1:]
	defaults = dict((args[len(args) - len(defaults) + i], defaults[i]) for i in xrange(0, len(defaults)))
	return {"args": args, "defaults": defaults, "varargs": argspec.varargs, "varkwargs": argspec.keywords,
			"docs": func.__doc__}


class RPCError(Exception):
	class Category:
		UNKNOWN = "unknown"
		NETWORK = "network"
		JSON = "json"
		FORMAT = "format"
		CALL = "call"
		METHOD = "method"

	def __init__(self, id, category, type, message, data=None):
		self.id = id
		self.category = category
		self.type = type
		self.message = message
		self.data = data

	@classmethod
	def decode(cls, data, id):
		if not isinstance(data, dict):
			raise RPCError(id, RPCError.Category.FORMAT, "wrong_type_error",
						   "Field 'error' was expected to be 'object', was %s" % type(data).__name__)
		if not "category" in data:
			raise RPCError(id, RPCError.Category.FORMAT, "missing_error_category",
						   "Missing field in response.error: category")
		if not isinstance(data["category"], basestring):
			raise RPCError(id, RPCError.Category.FORMAT, "wrong_type_error_category",
						   "Field 'error.category' was expected to be 'string', was %s" % type(
							   data["category"]).__name__)
		ecategory = data["category"]
		if not "type" in data:
			raise RPCError(id, RPCError.Category.FORMAT, "missing_error_type",
						   "Missing field in response.error: type")
		if not isinstance(data["type"], basestring):
			raise RPCError(id, RPCError.Category.FORMAT, "wrong_type_error_type",
						   "Field 'error.type' was expected to be 'string', was %s" % type(data["type"]).__name__)
		etype = data["type"]
		if "message" in data:
			if not isinstance(data["message"], basestring):
				raise RPCError(id, RPCError.Category.FORMAT, "wrong_type_error_message",
							   "Field 'error.message' was expected to be 'string', was %s" % type(
								   data["message"]).__name__)
			emessage = data["message"]
		else:
			emessage = None
		if "data" in data:
			edata = data["data"]
		else:
			edata = None
		return cls(id, ecategory, etype, emessage, edata)

	def encode(self):
		return {
			"category": self.category,
			"type": self.type,
			"message": self.message,
			"data": self.data
		}

	def __str__(self):
		return "RPC error (%s): %s, %s" % (self.category, self.type, self.message)

	def __repr__(self):
		return "RPCError(category=%s, type=%s, message=%r, data=%r)" % (
			self.category, self.type, self.message, self.data)


class RPCRequest:
	def __init__(self, id, method, args=None, kwargs=None):
		if not kwargs: kwargs = {}
		if not args: args = []
		self.id = id
		self.method = method
		self.args = args
		self.kwargs = kwargs

	@classmethod
	def decode_json(cls, json_data):
		try:
			data = json.loads(json_data)
		except Exception, exc:
			raise RPCError(json, RPCError.Category.JSON, "invalid_json",
						   "Request was invalid JSON: %s" % exc)
		return cls.decode(data, json_data)

	@classmethod
	def decode(cls, data, json):
		if not "id" in data:
			raise RPCError(json, RPCError.Category.FORMAT, "missing_id",
						   "Missing field in request: id")
		id = data["id"]
		if not "type" in data:
			raise RPCError(id, RPCError.Category.FORMAT, "missing_type",
						   "Missing field in request: type")
		if data["type"] != "request":
			raise RPCError(id, RPCError.Category.FORMAT, "invalid_type",
						   "Field 'type' of requests must be set to 'request'")
		if not "method" in data:
			raise RPCError(id, RPCError.Category.FORMAT, "missing_method",
						   "Missing field in request: method")
		if not isinstance(data["method"], basestring):
			raise RPCError(id, RPCError.Category.FORMAT, "wrong_type_method",
						   "Field 'method' was expected to be 'string', was %s" % type(data["method"]).__name__)
		method = data["method"]
		if "args" in data:
			if not isinstance(data["args"], list):
				raise RPCError(id, RPCError.Category.FORMAT, "wrong_type_args",
							   "Field 'args' was expected to be 'array', was %s" % type(data["args"]).__name__)
			args = data["args"]
		else:
			args = []
		if "kwargs" in data:
			if not isinstance(data["kwargs"], dict):
				raise RPCError(id, RPCError.Category.FORMAT, "wrong_type_kwargs",
							   "Field 'kwargs' was expected to be 'object', was %s" % type(data["kwargs"]).__name__)
			kwargs = data["kwargs"]
		else:
			kwargs = {}
		return cls(id, method, args, kwargs)

	def encode(self):
		if self.id is None:
			raise RPCError(None, RPCError.Category.FORMAT, "missing_id",
						   "Missing field in request: id")
		if not isinstance(self.method, basestring):
			raise RPCError(self.id, RPCError.Category.FORMAT, "wrong_type_method",
						   "Field 'method' was expected to be 'basestring', was %s" % type(self.method).__name__)
		if not isinstance(self.args, list) and not isinstance(self.args, tuple):
			raise RPCError(self.id, RPCError.Category.FORMAT, "wrong_type_args",
						   "Field 'args' was expected to be 'list' or 'tuple', was %s" % type(self.args).__name__)
		if not isinstance(self.kwargs, dict):
			raise RPCError(self.id, RPCError.Category.FORMAT, "wrong_type_kwargs",
						   "Field 'kwargs' was expected to be 'dict', was %s" % type(self.kwargs).__name__)
		try:
			return json.dumps(
				{"type": "request", "id": self.id, "method": self.method, "args": self.args, "kwargs": self.kwargs})
		except Exception, exc:
			raise RPCError(self.id, RPCError.Category.JSON, "invalid_data", "Failed to encode request: %s" % exc)


class RPCResponse:
	def __init__(self, id=None, result=None, error=None, hasResult=False):
		self.id = id
		self.result = result
		self.error = error
		self.hasResult = hasResult or bool(result)

	@classmethod
	def decode_json(cls, json_data):
		try:
			data = json.loads(json_data)
		except Exception, exc:
			raise RPCError(json, RPCError.Category.JSON, "invalid_json",
						   "Response was invalid JSON: %s" % exc)
		return cls.decode(data, json_data)

	@classmethod
	def decode(cls, data, json):
		if not "id" in data:
			raise RPCError(json, RPCError.Category.FORMAT, "missing_id",
						   "Missing field in response: id")
		id = data["id"]
		if not "type" in data:
			raise RPCError(id, RPCError.Category.FORMAT, "missing_type",
						   "Missing field in response: type")
		if data["type"] != "response":
			raise RPCError(id, RPCError.Category.FORMAT, "invalid_type",
						   "Field 'type' of responses must be set to 'response'")
		if "error" in data and "result" in data:
			raise RPCError(id, RPCError.Category.FORMAT, "result_and_error",
						   "Response must either specify result or error, not both")
		if "error" in data:
			result = None
			hasResult = False
			error = RPCError.decode(data["error"], id)
		elif "result" in data:
			error = None
			result = data["result"]
			hasResult = True
		else:
			raise RPCError(id, RPCError.Category.FORMAT, "missing_result_or_error",
						   "Missing field in response: result or error")
		return cls(id, result=result, hasResult=hasResult, error=error)

	def encode(self):
		if not self.error and not self.hasResult:
			raise RPCError(self.id, RPCError.Category.FORMAT, "missing_result_or_error",
						   "Missing field in response: result or error")
		if self.error and self.hasResult:
			raise RPCError(self.id, RPCError.Category.FORMAT, "result_and_error",
						   "Response must either specify result or error, not both")
		if self.error:
			if not isinstance(self.error, RPCError):
				raise RPCError(self.id, RPCError.Category.FORMAT, "wrong_type_error",
							   "Field 'error' was expected to be 'RPCError', was %s" % type(self.error).__name__)
			self.id = self.error.id
			data = {"type": "response", "id": self.error.id, "error": self.error.encode()}
		else:
			if self.id is None:
				raise RPCError(None, RPCError.Category.FORMAT, "missing_id",
							   "Missing field in response: id")
			data = {"type": "response", "id": self.id, "result": self.result}
		try:
			return json.dumps(data)
		except Exception, exc:
			raise RPCError(self.id, RPCError.Category.JSON, "invalid_data", "Failed to encode request: %s" % exc)

class DummyWrapper:
	def __enter__(self):
		pass
	def __exit__(self, exc_type, exc_val, exc_tb):
		pass

class RPCServer(SocketServer.ThreadingMixIn, SSLServer):
	def __init__(self, server_address, certCheck=None, wrapper=DummyWrapper, beforeExecute=None, afterExecute=None, onError=None, **sslargs):
		SSLServer.__init__(self, server_address, RPCHandler, **sslargs)
		self.beforeExecute = beforeExecute
		self.afterExecute = afterExecute
		self.wrapper = wrapper
		self.onError = onError
		self.certCheck = certCheck
		self.funcs = {}
		self._connectionLocal = threading.local()
		self.register(self._list, "$list$")
		self.register(self._info, "$info$")
		self.register(self._infoall, "$infoall$")
		self.register(self._multicall, "$multicall$")

	def register(self, func, name=None):
		if not callable(func):
			raise Exception("Method '%s' is not callable" % func)
		if not name:
			name = func.__name__
		self.funcs[name] = func

	def registerContainer(self, container):
		for func in filter(callable, map(lambda name: getattr(container, name),
										 filter(lambda name: not name.startswith("_"), dir(container)))):
			self.register(func)

	def unregister(self, name):
		del self.funcs[name]

	def getSession(self):
		return self._connectionLocal.session if hasattr(self._connectionLocal, "session") else None

	def setSession(self, value):
		self._connectionLocal.session = value

	def delSession(self):
		if hasattr(self._connectionLocal, "session"):
			del self._connectionLocal.session

	session = property(getSession, setSession, delSession)

	def getMethod(self, name):
		return self.funcs.get(name)

	def handleRequest(self, request):
		method = self.getMethod(request.method)
		if not method:
			raise RPCError(request.id, RPCError.Category.METHOD, "unknown_method",
						   "Unknown method: %s" % request.method)
		try:
			if callable(self.beforeExecute):
				self.beforeExecute(method, request.args, request.kwargs)
			res = method(*request.args, **request.kwargs)
			if callable(self.afterExecute):
				self.afterExecute(method, request.args, request.kwargs, res)
			return res
		except Exception, exc:
			if callable(self.onError):
				res = self.onError(exc, method, request.args, request.kwargs)
				if res:
					exc = res
			if isinstance(exc, RPCError):
				exc.id = request.id
				raise exc
			raise RPCError(request.id, RPCError.Category.CALL, type(exc).__name__, str(exc))

	def _list(self):
		return self.funcs.keys()

	def _info(self, name):
		method = self.getMethod(name)
		if not method:
			raise AttributeError("Method not found: %s" % name)
		return method_info(method)

	def _infoall(self):
		return dict([(key, method_info(func)) for (key, func) in self.funcs.iteritems()])

	def _multicall(self, calls):
		if not isinstance(calls, list):
			raise TypeError("Argument must be a list")
		responses = []
		for i in xrange(0, len(calls)):
			call = calls[i]
			call["id"] = i
			call["type"] = "request"
			request = RPCRequest.decode(call, None)
			try:
				result = self.handleRequest(request)
				responses.append({"result": result})
			except RPCError, err:
				responses.append({"error": err.encode()})
		return responses


class RPCHandler(SocketServer.StreamRequestHandler):
	def __init__(self, *args, **kwargs):
		self._wlock = threading.RLock()
		self.failed = False
		SocketServer.StreamRequestHandler.__init__(self, *args, **kwargs)

	def handle(self):
		while self.server.running and not self.failed:
			request_line = self.readLine()
			if not request_line:
				break
			session = self.server.session
			thread.start_new_thread(self.handleRequestLine, (request_line, session))
		self.server.delSession()

	def handleRequestLine(self, request_line, session):
		with self.server.wrapper:
			self.server.session = session
			request = None
			try:
				if callable(self.server.certCheck):
					if not self.server.certCheck(self.connection.getpeercert()):
						raise RPCError(
							id=request.id,
							category=RPCError.Category.METHOD,
							type="unauthorized",
							message="Certificate is not accepted"
						)
				request = RPCRequest.decode_json(request_line)
				result = self.server.handleRequest(request)
				resp = RPCResponse(id=request.id, result=result, hasResult=True).encode()
				self.writeLine(resp)
			except RPCError, err:
				self.writeLine(RPCResponse(error=err).encode())
			except Exception, exc:
				err = RPCError(
					id=request.id if request else request_line,
					category=RPCError.Category.UNKNOWN,
					type=type(exc).__name__,
					message=str(exc)
				)
				try:
					self.writeLine(RPCResponse(error=err).encode())
				except:
					self.failed = True

	def readLine(self):
		line = self.rfile.readline()
		# print "IN: " + line.strip()
		return line

	def writeLine(self, line):
		# print "OUT: " + line
		with self._wlock:
			self.wfile.write(line + "\n")
			self.wfile.flush()


class RPCProxy:
	def __init__(self, address, onError=(lambda x: x), **args):
		self._con = None
		self._onError = onError
		self._methods = {}
		try:
			self._con = SSLConnection(address, **args)
		except socket.error, err:
			raise self._onError(RPCError(id=None, category=RPCError.Category.NETWORK, type="connect", message=repr(err),
										 data={"address": address}))
		self._id = 0
		self._rlock = threading.RLock()
		self._wlock = threading.RLock()
		self._resLock = threading.RLock()
		self._resCond = threading.Condition(self._resLock)
		self._results = {}
		self._errors = {}
		self._methods = self._call("$infoall$")

	def _nextId(self):
		with self._wlock:
			self._id += 1
			return self._id

	def _writeLine(self, line):
		# print "OUT: %s" % line
		self._con.writeLine(line)

	def _readLine(self):
		line = self._con.readLine()
		# print "IN: %s" % line.strip()
		return line

	def _callInternal(self, name, args=None, kwargs=None):
		if not kwargs: kwargs = {}
		if not args: args = []
		with self._wlock:
			request_id = self._nextId()
			request_line = RPCRequest(id=request_id, method=name, args=args, kwargs=kwargs).encode()
			self._writeLine(request_line)
		while True:
			with self._resLock:
				# Check if our response is there
				if request_id in self._results:
					result = self._results[request_id]
					del self._results[request_id]
					return result
				if request_id in self._errors:
					error = self._errors[request_id]
					del self._errors[request_id]
					# if error.category == RPCError.Category.CALL:
					# if error.type.endswith("Error") and error.type in __builtins__:
					# raise __builtins__[error.type](error.message)
					raise error
				if request_line in self._errors:
					error = self._errors[request_line]
					del self._errors[request_line]
					raise error
			if self._rlock.acquire(blocking=False):
				# We are waiting for a message
				try:
					response = RPCResponse.decode_json(self._readLine())
					with self._resLock:
						# Save response
						if response.hasResult:
							self._results[response.id] = response.result
						else:
							self._errors[response.id] = response.error
						# Notify everyone who is waiting for responses
						self._resCond.notifyAll()
				finally:
					self._rlock.release()
			else:
				# Someone else is waiting for a message
				with self._resCond:
					# Wait for a message to come in
					self._resCond.wait()

	def _call(self, name, args=None, kwargs=None):
		if not kwargs: kwargs = {}
		if not args: args = []
		try:
			return self._callInternal(name, args, kwargs)
		except ssl.SSLError, err:
			raise self._onError(
				RPCError(id=None, category=RPCError.Category.NETWORK, type="ssl", message=str(err))), None, \
			sys.exc_info()[2]
		except socket.error, err:
			raise self._onError(
				RPCError(id=None, category=RPCError.Category.NETWORK, type="connection", message=str(err))), None, \
			sys.exc_info()[2]
		except RPCError, err:
			raise self._onError(err), None, sys.exc_info()[2]

	def multicall(self, *callargs):
		return MultiCallProxy(self, callargs)

	def _listMethods(self):
		return self.__getattr__("$list$")()

	def __getattr__(self, name):
		if not name in self._methods:
			raise AttributeError(name)
		return MethodProxy(self, name, self._methods[name])

	def __del__(self):
		try:
			self._con.close()
		except:
			pass


class MethodProxy:
	def __init__(self, proxy, name, info):
		self.proxy = proxy
		self.name = name
		self.info = info
		self.__name__ = name
		self.__doc__ = info["docs"]

	def __call__(self, *args, **kwargs):
		return self.proxy._call(self.name, args, kwargs)

	def _asyncCall(self, callback, error, args, kwargs):
		try:
			res = self(*args, **kwargs)
		except Exception, exc:
			if error:
				error(exc)
			return
		callback(res)

	def async(self, callback, args, kwargs=None, error=None):
		if not kwargs: kwargs = {}
		if not callable(callback):
			raise TypeError("Callback not callable")
		if error and not callable(error):
			raise TypeError("Error callback not callable")
		thread.start_new_thread(self._asyncCall, (callback, error, args, kwargs))


class MultiCallProxy(MethodProxy):
	def __init__(self, proxy, callargs):
		self.proxy = proxy
		self.callargs = callargs

	def __call__(self):
		calls = []
		for method, args, kwargs in self.callargs:
			calls.append({"method": method, "args": args, "kwargs": kwargs})
		responses = []
		for resp in self.proxy._call("$multicall$", [calls]):
			if "result" in resp:
				responses.append((True, resp["result"]))
			else:
				responses.append((False, RPCError.decode(resp["error"], None)))
		return responses
