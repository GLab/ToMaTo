import rpc, urllib


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
	conn.putrequest("POST", req)
	filename = os.path.basename(file)
	filesize = os.path.getsize(file)
	BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
	CRLF = '\r\n'
	prepend = "--" + BOUNDARY + CRLF + 'Content-Disposition: form-data; name="%s"; filename="%s"' % (
	name, filename) + CRLF + "Content-Type: application/data" + CRLF + CRLF
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


def createUrl(protocol, hostname, port, username=None, password=None):
	"""
	Creates a URL for connecting to a server.

	Parameter *protocol*:
		Protocol of the server
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

	Return value:
		This method returns a full server URL.

	"""
	auth = ""
	if username:
		username = urllib.quote_plus(username)
		auth = username
		if password:
			password = urllib.quote_plus(password)
			auth += ":" + password
	if auth:
		auth += "@"
	url = '%s://%s%s:%s' % (protocol, auth, hostname, port)
	return url


def getConnection(url, sslCert=None):
	"""
	Creates a server proxy to a host using the given URL.

	Parameter *url*:
		URL of the server
	Parameter *sslCert*:
		SSL certificate to use for a ssl connection

	Return value:
		This method returns a server proxy object.

	"""
	return rpc.createProxy(url, sslCert, sslCert, sslCert)
