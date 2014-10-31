from . import Error, SUPPORT_CHECK_PERIOD
from util import run, CommandError, cmd, proc, cache
import collections

class NetstatError(Error):
	CODE_UNKNOWN="netstat.unknown"
	CODE_UNSUPPORTED="netstat.unsupported"
	CODE_EXECUTE="netstat.execute"
	CODE_PARSE="netstat.parse"
	CODE_PORT_USED="netstat.port_used"

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
		raise NetstatError(NetstatError.CODE_EXECUTE, "Failed to execute netstat", {"cmd": cmd, "error": exc})
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
		raise NetstatError(NetstatError.CODE_PARSE, "Unable to parse netstat output", {"cmd": cmd, "error": exc, "output": res})
	return entries

@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def _check():
	NetstatError.check(cmd.exists("netstat"), NetstatError.CODE_UNSUPPORTED, "Binary netstat does not exist")
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

def isPortUsedBy(port, pid=None, group=True, pname=None, *args, **kwargs):
	for user in getPortUsers(port, *args, **kwargs):
		if user[0] == pid or user[1] == pname or (group and proc.isSameGroup(pid, user[0])):
			return True
	return False

def checkPortFree(port, *args, **kwargs):
	users = getPortUsers(port, *args, **kwargs)
	NetstatError.check(not users, NetstatError.CODE_PORT_USED, "Port is in use", {"port": port, "users": users})