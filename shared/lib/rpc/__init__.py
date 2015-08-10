import collections, ssl
from xmlrpclib import Fault

from ..error import TransportError, Error, InternalError, UserError
from .. import util
from . import xmlrpc, sslrpc

def unwrapXmlRpcError(err):
	if not isinstance(err, Fault):
		return TransportError(code=TransportError.UNKNOWN, message=repr(err), module="hostmanager")
	if err.faultCode == 999:
		return Error.parsestr(err.faultString)
	elif err.faultCode == 300:
		return TransportError(code=TransportError.UNAUTHORIZED, module="hostmanager")
	elif err.faultCode == 500:
		return InternalError(code=InternalError.UNKNOWN, message=err.faultString, module="hostmanager")
	elif err.faultCode == 401:
		return UserError(code=UserError.INVALID_STATE, message=err.faultString, module="hostmanager")
	elif err.faultCode == 402:
		return UserError(code=UserError.ENTITY_DOES_NOT_EXIST, message=err.faultString, module="hostmanager")
	elif err.faultCode == 403:
		return UserError(code=UserError.UNSUPPORTED_ACTION, message=err.faultString, module="hostmanager")
	elif err.faultCode == 404:
		return UserError(code=UserError.ENTITY_BUSY, message=err.faultString, module="hostmanager")
	elif err.faultCode == 400:
		return UserError(code=UserError.UNKNOWN, message=err.faultString, module="hostmanager")
	else:
		return InternalError(code=InternalError.UNKNOWN, message=err.faultString, module="hostmanager")

def isReusable(proxy):
	if isinstance(proxy, xmlrpc.ServerProxy):
		return False
	if isinstance(proxy, sslrpc.RPCProxy):
		return True
	return True

def createXmlRpcProxy(url, sslcert, timeout):
	schema, address = url.split(":", 1)
	schema, _ = schema.split("+")
	if address.startswith("//"):
		address = address[2:]
	if schema == "https":
		transport = xmlrpc.SafeTransportWithCerts(sslcert, sslcert, timeout=timeout)
	else:
		transport = None
	return xmlrpc.ServerProxy('%s://%s' % (schema, address), allow_none=True, transport=transport,
							  onError=unwrapXmlRpcError)

def unwrapJsonRpcError(err):
	assert isinstance(err, sslrpc.RPCError)
	if err.category == sslrpc.RPCError.Category.CALL:
		return Error.parse(err.data)
	return TransportError(code="%s.%s" % (err.category, err.type), message=err.message, data=err.data)

def createJsonRpcProxy(address, sslcert, timeout):
	if address.startswith("//"):
		address = address[2:]
	if not ":" in address:
		raise TransportError(code=TransportError.INVALID_URL,
								 message="address must contain port: %s" % address)
	address, port = address.split(":")
	port = int(port)
	return sslrpc.RPCProxy((address, port), certfile=sslcert, keyfile=sslcert, onError=unwrapJsonRpcError)

def createProxy(url, sslcert, timeout=30):
	if not ":" in url:
		raise TransportError(code=TransportError.INVALID_URL, message="invalid url: %s" % url)
	schema, address = url.split(":", 1)
	if schema == "http+xmlrpc" or schema == "https+xmlrpc":
		return createXmlRpcProxy(url, sslcert, timeout)
	elif schema == "ssl+jsonrpc":
		return createJsonRpcProxy(address, sslcert, timeout)
	else:
		raise TransportError(code=TransportError.INVALID_URL, message="unsupported protocol: %s" % schema)


SSLOpts = collections.namedtuple("SSLOpts", ["private_key", "certificate", "client_certs"])

def runXmlRpcServer(address, api, sslOpts, certCheck, wrapper, beforeExecute, afterExecute, onError):
	def wrapError(error, func, args, kwargs):
		error = onError(error, func, args, kwargs)
		if isinstance(error, Fault):
			return error
		assert isinstance(error, Error)
		if error.code == UserError.NOT_LOGGED_IN:
			return xmlrpc.ErrorUnauthorized()
		return Fault(999, error.rawstr)
	server = xmlrpc.XMLRPCServerIntrospection(address, sslOpts=sslOpts,
											  loginFunc=lambda _, cert: certCheck(cert.get_subject().commonName),
											  wrapper=wrapper, beforeExecute=beforeExecute, afterExecute=afterExecute,
											  onError=wrapError)
	server.register(api)
	util.start_thread(server.serve_forever)
	return server

def runJsonRpcServer(address, api, sslOpts, certCheck, wrapper, beforeExecute, afterExecute, onError):
	def wrapError(error, func, args, kwargs):
		error = onError(error, func, args, kwargs)
		assert isinstance(error, Error)
		return sslrpc.RPCError(None, category=sslrpc.RPCError.Category.CALL, type="call_error", message="", data=error.raw)
	server = sslrpc.RPCServer(address, certCheck=lambda cert: certCheck(
		dict(map(lambda l: l[0], cert['subject']))['commonName']), wrapper=wrapper, beforeExecute=beforeExecute,
							  afterExecute=afterExecute, onError=wrapError, keyfile=sslOpts.private_key,
							  certfile=sslOpts.certificate, ca_certs=sslOpts.client_certs,
							  cert_reqs=ssl.CERT_REQUIRED)
	server.registerContainer(api)
	util.start_thread(server.serve_forever)
	return server

def runServer(type, address, api, sslOpts, certCheck, wrapper, beforeExecute, afterExecute, onError):
	if type == "https+xmlrpc":
		return runXmlRpcServer(address, api, sslOpts, certCheck, wrapper, beforeExecute, afterExecute, onError)
	elif type == "ssl+jsonrpc":
		return runJsonRpcServer(address, api, sslOpts, certCheck, wrapper, beforeExecute, afterExecute, onError)
	else:
		raise TransportError(code=TransportError.INVALID_URL, message="unsupported protocol: %s" % type)
