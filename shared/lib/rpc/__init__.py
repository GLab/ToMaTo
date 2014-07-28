import collections


class RemoteError(Exception):
    TYPE = "general"

    def __init__(self, code=None, message=None, type=None, data={}):
        self.type = type or self.TYPE
        self.code = code
        self.message = message
        self.data = data

    @property
    def raw(self):
        return self.__dict__

    @staticmethod
    def parse(raw):
        return {
            RemoteInternalError.TYPE: RemoteInternalError,
            RemoteTransportError.TYPE: RemoteTransportError,
            RemoteUserError.TYPE: RemoteUserError,
        }[raw["type"]](**raw)

    def __str__(self):
        return "%s error [%s]: %s" % (self.type, self.code, self.message or "")

    def __repr__(self):
        return "RemoteError(type=%r, code=%r, message=%r, data=%r)" % (self.type, self.code, self.message, self.data)


class RemoteInternalError(RemoteError):
    TYPE = "internal"
    UNKNOWN = None
    HOST_ERROR = "host_error"


class RemoteTransportError(RemoteError):
    TYPE = "transport"
    UNKNOWN = None
    INVALID_URL = "invalid_url"
    UNAUTHORIZED = "unauthorized"


class RemoteUserError(RemoteError):
    TYPE = "user"
    UNKNOWN = None
    ENTITY_DOES_NOT_EXIST = "entity_does_not_exist"
    UNSUPPORTED_ACTION = "unsupported_action"
    UNSUPPORTED_ATTRIBUTE = "unsupported_attribute"
    INVALID_STATE = "invalid_state"
    ENTITY_BUSY = "entity_busy"


def getProxy(url, sslcert, timeout=30):
    if not ":" in url:
        raise RemoteTransportError(code=RemoteTransportError.INVALID_URL, message="invalid url: %s" % url)
    schema, address = url.split(":", 1)
    if schema == "https+xmlrpc":
        from . import xmlrpc

        if address.startswith("//"):
            address = address[2:]
        if not ":" in address:
            raise RemoteTransportError(code=RemoteTransportError.INVALID_URL,
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
            raise RemoteTransportError(code=RemoteTransportError.INVALID_URL,
                                       message="address must contain port: %s" % address)
        address, port = address.split(":")
        port = int(port)
        return sslrpc.RPCProxy((address, port), cert=sslcert, key=sslcert)
    else:
        raise RemoteTransportError(code=RemoteTransportError.INVALID_URL, message="unsupported protocol: %s" % schema)


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

        server = sslrpc.RPCServer(address, certCheck=lambda cert: certCheck(
            dict(map(lambda l: l[0], cert['subject']))['commonName']), beforeExecute=beforeExecute,
                                  afterExecute=afterExecute, onError=onError)
        server.registerContainer(api)
        util.start_thread(server.serve_forever)
        return server
    else:
        raise RemoteTransportError(code=RemoteTransportError.INVALID_URL, message="unsupported protocol: %s" % type)