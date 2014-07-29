import collections

from ..error import TransportError


def createProxy(url, sslcert, timeout=30):
	if not ":" in url:
		raise TransportError(code=TransportError.INVALID_URL, message="invalid url: %s" % url)
	schema, address = url.split(":", 1)
	if schema == "https+xmlrpc":
		from . import xmlrpc

		if address.startswith("//"):
			address = address[2:]
		if not ":" in address:
			raise TransportError(code=TransportError.INVALID_URL,
				message="address must contain port: %s" % address)
		address, port = address.split(":")
		port = int(port)
		transport = xmlrpc.SafeTransportWithCerts(sslcert, sslcert, timeout=timeout)
		return xmlrpc.ServerProxy('https://%s:%d' % (address, port), allow_none=True, transport=transport)
	elif schema == "ssl+jsonrpc":
		from . import sslrpc

		if address.startswith("//"):
			address = address[2:]
		if not ":" in address:
			raise TransportError(code=TransportError.INVALID_URL,
				message="address must contain port: %s" % address)
		address, port = address.split(":")
		port = int(port)
		return sslrpc.RPCProxy((address, port), certfile=sslcert, keyfile=sslcert)
	else:
		raise TransportError(code=TransportError.INVALID_URL, message="unsupported protocol: %s" % schema)


SSLOpts = collections.namedtuple("SSLOpts", ["private_key", "certificate", "client_certs"])


def runServer(type, address, api, sslOpts, certCheck, beforeExecute, afterExecute, onError):
	if type == "https+xmlrpc":
		from . import xmlrpc
		from .. import util

		server = xmlrpc.XMLRPCServerIntrospection(address, sslOpts=sslOpts,
			loginFunc=lambda _, cert: certCheck(cert.get_subject().commonName),
			beforeExecute=beforeExecute, afterExecute=afterExecute,
			onError=onError)
		server.register(api)
		util.start_thread(server.serve_forever)
		return server
	elif type == "ssl+jsonrpc":
		from . import sslrpc
		from .. import util
		import ssl

		server = sslrpc.RPCServer(address, certCheck=lambda cert: certCheck(
			dict(map(lambda l: l[0], cert['subject']))['commonName']), beforeExecute=beforeExecute,
			afterExecute=afterExecute, onError=onError, keyfile=sslOpts.private_key,
			certfile=sslOpts.certificate, ca_certs=sslOpts.client_certs,
			cert_reqs=ssl.CERT_REQUIRED)
		server.registerContainer(api)
		util.start_thread(server.serve_forever)
		return server
	else:
		raise TransportError(code=TransportError.INVALID_URL, message="unsupported protocol: %s" % type)
