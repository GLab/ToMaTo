from .sslrpc2 import Proxy
from .error import Error, TransportError
from .settings import settings, Config

import ssl

def _convertError(error):
	if isinstance(error, Error):
		return error
	if isinstance(error, dict):
		return Error.parse(error)
	return error

def createProxy(address, sslcert, sslkey, sslca):
	if address.startswith("sslrpc2://"):
		address = address[10:]
	if not ":" in address:
		raise TransportError(code=TransportError.INVALID_URL, message="address must contain port: %s" % address)
	address, port = address.split(":")
	port = int(port)
	return Proxy((address, port), certfile=sslcert, keyfile=sslkey, ca_certs=sslca, cert_reqs=ssl.CERT_REQUIRED, onError=_convertError)

def get_tomato_inner_proxy(tomato_module):
	protocol = 'sslrpc2'
	conf = settings.get_interface(tomato_module, True, protocol)
	backend_users_address = "%s://%s:%s" % (protocol, conf['host'], conf['port'])
	return createProxy(backend_users_address, settings.get_ssl_cert_filename(), settings.get_ssl_key_filename(), settings.get_ssl_ca_filename())




# shortcuts and helpers

def get_backend_users_proxy():
	return get_tomato_inner_proxy(Config.TOMATO_MODULE_BACKEND_USERS)

def get_backend_core_proxy():
	return get_tomato_inner_proxy(Config.TOMATO_MODULE_BACKEND_CORE)

def get_backend_debug_proxy():
	return get_tomato_inner_proxy(Config.TOMATO_MODULE_BACKEND_DEBUG)

def get_backend_accounting_proxy():
	return get_tomato_inner_proxy(Config.TOMATO_MODULE_BACKEND_ACCOUNTING)

def is_reachable(tomato_module):
	if is_self(tomato_module):
		return True
	try:
		return get_tomato_inner_proxy(tomato_module).ping()
	except:
		return False

def is_self(tomato_module):
	return tomato_module == settings.get_tomato_module_name()

def list_other_modules():
	return [module for module in Config.TOMATO_BACKEND_MODULES if not is_self(module)]