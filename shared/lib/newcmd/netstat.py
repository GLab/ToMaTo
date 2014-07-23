from . import Error
from util import run, CommandError, cmd
import collections

class NetstatError(Error):
	CATEGORY="cmd_netstat"
	TYPE_UNKNOWN="unknown"
	TYPE_UNSUPPORTED="unsupported"
	TYPE_EXECUTE="execute"
	TYPE_PARSE="parse"
	TYPE_PORT_USED="port_used"
	def __init__(self, type, message, data=None):
		Error.__init__(self, category=NetstatError.CATEGORY, type=type, message=message, data=data)

Entry = collections.namedtuple("Entry", ["protocol", "local_ip", "local_port", "remote_ip", "remote_port", "state", "prog_pid", "prog_name"])

def _netstat(tcp, udp, ipv4, ipv6, listen):
	cmd = ["netstat", "-Wpn"]
	if tcp:
		cmd.append("-t")
	if udp:
		cmd.append("-u")
	if ipv4:
		cmd.append("-4")
	if ipv6:
		cmd.append("-6")
	if listen:
		cmd.append("-l")
	try:
		res = run(cmd)
	except CommandError, exc:
		raise NetstatError(NetstatError.TYPE_EXECUTE, "Failed to execute netstat: %s" % exc, {"cmd": cmd, "error": exc})
	try:
		entries = []
		for line in res.splitlines():
			fields = line.split()
			if len(fields) != 7 or not ":" in fields[3] or not ":" in fields[4]:
				continue
			local_ip, local_port = fields[3].rsplit(":", 1)
			remote_ip, remote_port = fields[4].rsplit(":", 1)
			local_port = int(local_port)
			if remote_port != "*":
				remote_port = int(remote_port)
			prog_pid, prog_name = fields[6].split("/") if fields[6] != "-" else (None, None)
			if prog_pid:
				prog_pid = int(prog_pid)
			entries.append(Entry(fields[0], local_ip, local_port, remote_ip, remote_port, fields[5], prog_pid, prog_name))
	except Exception, exc:
		raise NetstatError(NetstatError.TYPE_PARSE, "Unable to parse netstat output: %s" % exc, {"cmd": cmd, "error": exc, "output": res})
	return entries

def _check():
	NetstatError.check(cmd.exists("netstat"), NetstatError.TYPE_UNSUPPORTED, "Binary netstat does not exist")
	return True

def _public(method):
	def call(*args, **kwargs):
		_check()
		return method(*args, **kwargs)
	call.__name__ = method.__name__
	call.__doc__ = method.__doc__
	return call

######################
### Public methods ###
######################

def checkSupport():
	return _check()

def getPortUsers(port, tcp=True, udp=False, ipv4=True, ipv6=True):
	users = []
	entries = _netstat(tcp=tcp, udp=udp, ipv4=ipv4, ipv6=ipv6, listen=True)
	for e in entries:
		if e.local_port == port:
			users.append((e.prog_pid, e.prog_name))
	return users

def isPortFree(port, *args, **kwargs):
	return not bool(getPortUsers(port, *args, **kwargs))

def isPortUsedBy(port, pid, *args, **kwargs):
	for user in getPortUsers(port, *args, **kwargs):
		return user[0] == pid
	return False

def checkPortFree(port, *args, **kwargs):
	users = getPortUsers(port, *args, **kwargs)
	NetstatError.check(not users, NetstatError.TYPE_PORT_USED, "Port is in use: %d" % port, {"port": port, "users": users}) 