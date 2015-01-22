import socket, select, os

from . import anyjson as json

class Port:
	def fileno(self):
		raise NotImplementedError
	def open(self, port):
		raise NotImplementedError
	def close(self):
		raise NotImplementedError
	def read(self):
		raise NotImplementedError
	def write(self, data):
		raise NotImplementedError
	def connect(self, address):
		raise NotImplementedError
	def disconnect(self):
		raise NotImplementedError

class TCP4Port(Port):
	pass

class UDP4Port(Port):
	pass

class TCP6Port(Port):
	pass

class UDP6Port(Port):
	pass

PROTOCOLS={"ipv4/tcp": TCP4Port, "ipv6/tcp": TCP6Port, "ipv4/udp": UDP4Port, "ipv6/udp": UDP6Port}

class Connection:
	def __init__(self, sock):
		self.socket = sock
		self.rfile = sock.makefile('rb', -1)
		self.wfile = sock.makefile('wb', 0)
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

class JsonConnection(Connection):
	def read(self, *args):
		return json.loads(Connection.readLine(self))
	def readLine(self):
		return self.read()
	def write(self, data):
		Connection.writeLine(self, json.dumps(data))
	def writeLine(self, data):
		self.wfile(data)

class CheckerClient:
	def __init__(self, server):
		pass

def checkRange(protocol="ipv4/tcp", address=None, ports=None, secret=None):
	if not protocol in PROTOCOLS:
		return {"error": "invalid protocol"}
	PortClass = PROTOCOLS[protocol]
	if ports is None:
		ports = []
	portObjs = []
	statuses = {"unknown": [], "open": [], "blocked": []}
	for port in ports:
		try:
			p = PortClass()
			p.connect((address, port))
		except:
			statuses["unknown"].append(port)
			continue
		portObjs.append(p)
	while portObjs:
		inReady, _, _ = select.select(portObjs, [], [])


class CheckerServer:
	COMMANDS=["check_range"]
	def __init__(self, port):
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind(('', port))
		self.server.listen(1)
		self.running = True
	def close(self):
		self.running = False
		self.server.close()
	def run(self):
		while self.running:
			self.handleConnection(JsonConnection(self.server.accept()))
	def handleConnection(self, con):
		while True:
			try:
				request = con.read()
			except:
				try:
					con.close()
				except:
					pass
				return
			result = self.handleRequest(request)
			con.write(result)
	def handleRequest(self, request):
		if not "command" in request:
			return {"error": "no command given"}
		command = request["command"]
		if not "command" in CheckerServer.COMMANDS:
			return {"error": "invalid command"}
		params = request.get("params", {})
		fn = getattr(self, "cmd_%s" % command)
		return fn(**params)


