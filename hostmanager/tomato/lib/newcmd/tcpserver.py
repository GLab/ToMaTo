from . import Error, netstat, SUPPORT_CHECK_PERIOD
from util import spawnDaemon, params, proc, wait, cmd, cache

class TcpserverError(Error):
	CODE_UNKNOWN="tcpserver.unknown"
	CODE_UNSUPPORTED="tcpserver.unsupported"
	CODE_PORT_USED="tcpserver.port_used"
	CODE_STILL_RUNNING="tcpserver.still_running"

@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def _check():
	TcpserverError.check(cmd.exists("tcpserver"), TcpserverError.CODE_UNSUPPORTED, "Binary tcpserver does not exist")
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

@_public
def start(port, command):
	port = params.convert(port, convert=int, gte=1, lt=2**16)
	command = params.convert(command, convert=list)
	netstat.checkPortFree(port, tcp=True, ipv4=True)
	pid = spawnDaemon(["tcpserver", "-qHRl", "0",  "0", str(port)] + command)
	try:
		wait.waitFor(lambda :netstat.isPortUsedBy(port, pid), failCond=lambda :not proc.isAlive(pid))
		return pid
	except wait.WaitError:
		proc.autoKill(pid, group=True)
		raise

@_public
def stop(pid):
	proc.autoKill(pid, group=True)
	TcpserverError.check(not proc.isAlive(pid), TcpserverError.CODE_STILL_RUNNING, "Failed to stop tcpserver")