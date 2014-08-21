
import xmlrpclib, ssl, urllib

def tcpPortOpen(host, port):
    """

    Opens a connection to a remote socket at address (host, port) and closes it to open the TCP port.

    Parameter *host*:
        Host address of the socket 
    Parameter *port*:
        TCP port that will be opened
    
    Return value:
      This method returns a boolean which is true, if the TCP Port is open and false otherwise. 

    
    """
    from socket import socket, AF_INET, SOCK_STREAM
    s = socket(AF_INET, SOCK_STREAM)
    result = s.connect_ex((host, port))
    s.close()
    return not result

def download(url, file):
    """
    Downloads a network object from an URL to a local file.

    Parameter *url*:
        Url to the network object
  
    Parameter *file*:
        File to copy the network object to.
    
    """
    import urllib
    urllib.urlretrieve(url, file)
    
    
def upload(url, file, name="upload"):
    """
    
    Uploads a file to the target URL via the HTTP post command using name as content key.

    Parameter *url*:
        Target URL for the upload
  
    Parameter *file*:
        Path to the file to be uploaded
    
    Parameter *name*:
        Should always stay "upload". Content key for transmitted file.
    
    """
    import httplib, urlparse, os
    parts = urlparse.urlparse(url)
    conn = httplib.HTTPConnection(parts.netloc)
    req = parts.path
    if parts.query:
        req += "?" + parts.query
    conn.putrequest("POST",req)
    filename = os.path.basename(file)
    filesize = os.path.getsize(file)
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    prepend = "--" + BOUNDARY + CRLF + 'Content-Disposition: form-data; name="%s"; filename="%s"' % (name, filename) + CRLF + "Content-Type: application/data" + CRLF + CRLF 
    append = CRLF + "--" + BOUNDARY + "--" + CRLF + CRLF 
    conn.putheader("Content-Length", len(prepend) + filesize + len(append))
    conn.putheader("Content-Type", 'multipart/form-data; boundary=%s' % BOUNDARY)
    conn.endheaders()
    conn.send(prepend)
    fd = open(file, "r")
    data = fd.read(8192)
    while data:
        conn.send(data)
        data = fd.read(8192)
    fd.close()
    conn.send(append)
    resps = conn.getresponse()
    data = resps.read()
    
    
class SafeTransportWithCerts(xmlrpclib.SafeTransport):
    """
    A class containing a SSL connection to a host using the xmlrpclib.
    
    Parameter *xmlrpclib.SafeTransport*:
        A internal transport factory instance for the connection

    """
    def __init__(self, keyFile, certFile, *args, **kwargs):
        xmlrpclib.SafeTransport.__init__(self, *args, **kwargs)
        self.certFile = certFile
        self.keyFile = keyFile
    def make_connection(self,host):
        host_with_cert = (host, {'key_file' : self.keyFile, 'cert_file' : self.certFile})
        return xmlrpclib.SafeTransport.make_connection(self,host_with_cert)
    
class ServerProxy(object):
    """
    A server proxy class with a connection to a remote XML-RPC server.

    Parameter *object*:
        Dictionary which contains the host url and different optional arguments for the proxy connection.
        See the xmlrpclib documentation for details.

    """
    def __init__(self, url, **kwargs):
        self._xmlrpc_server_proxy = xmlrpclib.ServerProxy(url, **kwargs)
    def __getattr__(self, name):
        call_proxy = getattr(self._xmlrpc_server_proxy, name)
        def _call(*args, **kwargs):
            return call_proxy(args, kwargs)
        return _call

def getConnection(hostname, port, ssl, username=None, password=None, sslCert=None):
    """
    Creates a server proxy to a host using ssl transport optional.
    
    Parameter *hostname*:
        Address of the host of the server
    Parameter *port*:
        Port of the host server
    Parameter *ssl*:
        Boolean whether ssl should be used or not
    Parameter *username*:
        The username to use for login
    Parameter *password*:
        The password to user for login
    Parameter *sslCert*:
        SSL certificate to use for a ssl connection
    
    Return value:
        This method returns a server proxy object.
    
    """
    proto = 'https' if ssl else 'http'
    auth = ""
    if username:
        username = urllib.quote_plus(username)
        auth = username
        if password:
            password = urllib.quote_plus(password)
            auth += ":" + password
    if auth:
        auth += "@"
    transport = None
    if ssl and sslCert:
        transport = SafeTransportWithCerts(sslCert, sslCert)
    #print '%s://%s%s:%s' % (proto, auth, hostname, port)
    return ServerProxy('%s://%s%s:%s' % (proto, auth, hostname, port), allow_none=True, transport=transport)
    