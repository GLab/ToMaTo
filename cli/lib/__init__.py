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
