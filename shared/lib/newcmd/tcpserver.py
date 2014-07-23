from . import Error, netstat
from util import spawnDaemon, CommandError, params, proc, wait, cmd

class TcpserverError(Error):
	CATEGORY="cmd_tcpserver"
	TYPE_UNKNOWN="unknown"
	TYPE_UNSUPPORTED="unsupported"
	TYPE_PORT_USED="port_used"
	TYPE_STILL_RUNNING="still_running"
	def __init__(self, type, message, data=None):
		Error.__init__(self, category=TcpserverError.CATEGORY, type=type, message=message, data=data)

def _check():
	TcpserverError.check(cmd.exists("tcpserver"), TcpserverError.TYPE_UNSUPPORTED, "Binary tcpserver does not exist")
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
		proc.autoKill(pid, group=True, force=True)
		raise

@_public
def stop(pid):
	proc.autoKill(pid, group=True)
	TcpserverError.check(not proc.isAlive(pid), TcpserverError.TYPE_STILL_RUNNING, "Failed to stop tcpserver")