import ssl, socket, SocketServer, inspect, threading, thread, sys, msgpack, snappy

if msgpack.version < (0, 4, 0):
	print >>sys.stderr, "Warning: Older msgpack-python versions are broken"

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

	def read(self, size):
		try:
			data = self.rfile.read(size)
			if len(data) < size:
				raise ConnectionEnded()
			return data
		except:
			raise NetworkError(NetworkError.ReadError)

	def write(self, data):
		try:
			self.wfile.write(data)
		except:
			raise NetworkError(NetworkError.WriteError)

	def close(self):
		self.rfile.close()
		self.wfile.close()
		self.socket.close()


class NetworkError(Exception):
	ReadError = 0
	WriteError = 1

	def __init__(self, code):
		self.code = code

	def __str__(self):
		return "Network error: %s" % self.code


class FramingError(Exception):
	UnknownEncoding = 0
	InvalidCompressedData = 1
	MessageTooLarge = 2
	InvalidFormatedData = 3

	def __init__(self, code):
		self.code = code

	def __str__(self):
		return "Framing error: %s" % self.code


class MessageError(Exception):
	UnknownError = 0
	InvalidBaseType = 1
	InvalidBaseSize = 2
	InvalidIdType = 3
	InvalidMethodType = 4
	InvalidArgsType = 5
	InvalidKwArgsType = 6
	InvalidKwArgsKeyType = 7
	InvalidReplyTypeType = 8
	InvalidErrorType = 9
	UnknownReplyType = 10

	def __init__(self, code, id=None):
		self.code = code
		self.id = id

	def __str__(self):
		return "Message error: %s" % self.code



class NoSuchMethodError(Exception):
	def __init__(self, method):
		self.method = method

	def __str__(self):
		return "No such method error: %s" % self.method


class ConnectionEnded(Exception):
	def __init__(self):
		pass


class TimedOut(Exception):
	def __init__(self):
		pass


class Failure(Exception):
	def __init__(self, data):
		self.data = data

	def __str__(self):
		"Failure: %s" % self.data


class Message:
	def encode(self):
		raise NotImplementedError()

	class Encoding:
		Raw = 0
		Snappy = 1

	def writeTo(self, con):
		bytes = msgpack.packb(self.encode())
		method = Message.Encoding.Raw
		if len(bytes) > 100:
			compressed = snappy.compress(bytes)
			if len(compressed) < len(bytes):
				bytes = compressed
				method = Message.Encoding.Snappy
		size = len(bytes)
		con.write(chr(method) + chr(size>>16) + chr((size>>8) & 0xff) + chr(size & 0xff) + bytes)

	@classmethod
	def readFrom(cls, con):
		header = con.read(4)
		method = ord(header[0])
		size = (ord(header[1]) << 16) + (ord(header[2]) << 8) + (ord(header[3]))
		bytes = con.read(size)
		if method == Message.Encoding.Raw:
			pass
		elif method == Message.Encoding.Snappy:
			try:
				bytes = snappy.uncompress(bytes)
			except snappy.UncompressError:
				raise FramingError(FramingError.InvalidCompressedData)
			size = len(bytes)
			if size >= 1<<24:
				raise FramingError(FramingError.MessageTooLarge)
		else:
			raise FramingError(FramingError.UnknownEncoding)
		try:
			data = msgpack.unpackb(bytes)
		except msgpack.UnpackException:
			raise FramingError(FramingError.InvalidFormatedData)
		return cls.decode(data)


class Request(Message, object):
	__slots__ = ("id", "method", "args", "kwargs")

	def __init__(self, id, method, args, kwargs):
		self.id = id
		self.method = method
		self.args = args
		self.kwargs = kwargs

	def encode(self):
		return (self.id, self.method, self.args, self.kwargs)

	@classmethod
	def decode(cls, val):
		if not isinstance(val, (tuple, list)):
			raise MessageError(MessageError.InvalidBaseType)
		if len(val) != 4:
			raise MessageError(MessageError.InvalidBaseSize)
		id, method, args, kwargs = val
		if not isinstance(id, int):
			raise MessageError(MessageError.InvalidIdType)
		if not isinstance(method, basestring):
			raise MessageError(MessageError.InvalidMethodType, id)
		if not isinstance(args, (list, tuple)):
			raise MessageError(MessageError.InvalidArgsType, id)
		if not isinstance(kwargs, dict):
			raise MessageError(MessageError.InvalidKwArgsType, id)
		for k, v in kwargs.items():
			if isinstance(k, basestring):
				raise MessageError(MessageError.InvalidKwArgsKeyType, id)
		return cls(id, method, args, kwargs)


class Reply(Message, object):
	__slots__ = ("id", "result", "value")

	class Result:
		Success = 0
		Failure = 1
		NoSuchMethod = 2
		RequestError = 3

	def __init__(self, id, result, value):
		self.id = id
		self.result = result
		self.value = value

	def encode(self):
		return (self.id, self.result, self.value)

	@classmethod
	def decode(cls, val):
		if not isinstance(val, (tuple, list)):
			raise MessageError(MessageError.InvalidBaseType)
		if len(val) != 3:
			raise MessageError(MessageError.InvalidBaseSize)
		id, result, value = val
		if not isinstance(id, (int, type(None))):
			raise MessageError(MessageError.InvalidIdType)
		if not isinstance(result, int):
			raise MessageError(MessageError.InvalidReplyTypeType, id)
		if result == Reply.Result.Success:
			if not isinstance(id, int):
				raise MessageError(MessageError.InvalidIdType)
		elif result == Reply.Result.Failure:
			if not isinstance(id, int):
				raise MessageError(MessageError.InvalidIdType)
		elif result == Reply.Result.NoSuchMethod:
			if not isinstance(id, int):
				raise MessageError(MessageError.InvalidIdType)
			if not isinstance(value, basestring):
				raise MessageError(MessageError.InvalidMethodType, id)
		elif result == Reply.Result.RequestError:
			if not isinstance(value, int):
				raise MessageError(MessageError.InvalidErrorType, id)
		else:
			raise MessageError(MessageError.UnknownReplyType, id)
		return cls(id, result, value)


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


class DummyWrapper:
	def __enter__(self):
		pass
	def __exit__(self, exc_type, exc_val, exc_tb):
		pass


class Server(SocketServer.ThreadingMixIn, SSLServer):
	def __init__(self, server_address, certCheck=None, wrapper=DummyWrapper(), beforeExecute=None, afterExecute=None, onError=None, **sslargs):
		SSLServer.__init__(self, server_address, Handler, **sslargs)
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
			raise NoSuchMethodError(request.method)
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
			raise exc

	def _list(self):
		return self.funcs.keys()

	def _info(self, name):
		method = self.getMethod(name)
		if not method:
			raise AttributeError("Method not found: %s" % name)
		return method_info(method)

	def _infoall(self):
		return dict([(key, method_info(func)) for (key, func) in self.funcs.iteritems()])


class Handler(SocketServer.StreamRequestHandler):
	def __init__(self, *args, **kwargs):
		self._wlock = threading.RLock()
		self.failed = False
		SocketServer.StreamRequestHandler.__init__(self, *args, **kwargs)

	def handle(self):
		if callable(self.server.certCheck):
			if not self.server.certCheck(self.connection.getpeercert()):
				self.connection.close()
				self.server.delSession()
				return
		self.server.session = None
		while self.server.running and not self.failed:
			try:
				request = Request.readFrom(self)
			except ConnectionEnded:
				break
			except NetworkError as err:
				break
			except FramingError as err:
				break
			except MessageError as err:
				reply = Reply(err.id, Reply.Result.RequestError, err.code)
				try:
					reply.writeTo(self)
					continue
				except NetworkError as err:
					break
			except Exception as err:
				import traceback
				traceback.print_exc()
				break
			thread.start_new_thread(self.handleRequest, (request, self.server.session))
		self.server.delSession()

	def handleRequest(self, request, session):
		with self.server.wrapper:
			self.server.session = session
			try:
				result = self.server.handleRequest(request)
				reply = Reply(request.id, Reply.Result.Success, result)
			except NoSuchMethodError as err:
				reply = Reply(request.id, Reply.Result.NoSuchMethod, err.method)
			except Failure as err:
				reply = Reply(request.id, Reply.Result.Failure, err.data)
			except Exception as err:
				reply = Reply(request.id, Reply.Result.Failure, {"type": type(err), "message": str(err)})
		try:
			reply.writeTo(self)
		except:
			self.failed = True

	def read(self, size):
		try:
			data = self.rfile.read(size)
			if len(data) < size:
				raise ConnectionEnded()
			return data
		except:
			raise NetworkError(NetworkError.ReadError)

	def write(self, data):
		try:
			with self._wlock:
				self.wfile.write(data)
				self.wfile.flush()
		except:
			raise NetworkError(NetworkError.WriteError)


class Proxy:
	def __init__(self, address, onError=(lambda x: x), **args):
		self._con = None
		self._onError = onError
		try:
			self._con = SSLConnection(address, **args)
		except socket.error, err:
			raise self._onError(NetworkError(NetworkError.ReadError))
		self._id = 0
		self._rlock = threading.RLock()
		self._wlock = threading.RLock()
		self._resLock = threading.RLock()
		self._resCond = threading.Condition(self._resLock)
		self._results = {}
		self._errors = {}

	def _nextId(self):
		with self._wlock:
			self._id += 1
			return self._id

	def _callInternal(self, name, args=None, kwargs=None):
		if not kwargs: kwargs = {}
		if not args: args = []
		with self._wlock:
			request_id = self._nextId()
			request = Request(request_id, name, args, kwargs)
			request.writeTo(self._con)
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
					raise error
			if self._rlock.acquire(blocking=False):
				# We are waiting for a message
				try:
					response = Reply.readFrom(self._con)
					with self._resLock:
						# Save response
						if response.result == Reply.Result.Success:
							self._results[response.id] = response.value
						elif response.result == Reply.Result.Failure:
							self._errors[response.id] = response.value
						elif response.result == Reply.Result.RequestError:
							self._errors[response.id] = MessageError(response.value)
						elif response.result == Reply.Result.NoSuchMethod:
							self._errors[response.id] = NoSuchMethodError(response.value)
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
		except Exception, err:
			raise self._onError(err), None, sys.exc_info()[2]

	def _listMethods(self):
		return self._call("$list$")

	def __getattr__(self, name):
		return MethodProxy(self, name, {})

	def __dir__(self):
		return self._listMethods()

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
		self.__doc__ = info.get("desc")

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
