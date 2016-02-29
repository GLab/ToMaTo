from .sslrpc2 import Proxy
from .error import Error, TransportError
from .settings import settings

import ssl

def _convertError(error):
	if isinstance(error, Error):
		return error
	if isinstance(error, dict):
		return Error.parse(error)
	return error

def createProxy(address, sslcert, sslca):
	if address.startswith("sslrpc2://"):
		address = address[10:]
	if not ":" in address:
		raise TransportError(code=TransportError.INVALID_URL, message="address must contain port: %s" % address)
	address, port = address.split(":")
	port = int(port)
	return Proxy((address, port), certfile=sslcert, keyfile=sslcert, ca_certs=sslca, cert_reqs=ssl.CERT_REQUIRED, onError=_convertError)


def get_tomato_inner_proxy(tomato_module):
	protocol = 'sslrpc2'
	conf = settings.get_interface(tomato_module, True, protocol)
	backend_users_address = "%s://%s:%s" % (protocol, conf['host'], conf['port'])
	return createProxy(backend_users_address, settings.get_ssl_cert_filename(), settings.get_ssl_ca_filename())
