import os
from . import Error, netstat, SUPPORT_CHECK_PERIOD
from util import spawnDaemon, params, proc, wait, cmd, cache

BLOCKED_PORTS = [6000, 6666]

class WebsockifyError(Error):
	CODE_UNKNOWN="websockify.unknown"
	CODE_UNSUPPORTED="websockify.unsupported"
	CODE_PORT_BLOCKED="websockify.port_blocked"
	CODE_PORT_USED="websockify.port_used"
	CODE_DEST_PORT_FREE="websockify.dest_port_free"
	CODE_STILL_RUNNING="websockify.still_running"

@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def _check():
	WebsockifyError.check(cmd.exists("websockify"), WebsockifyError.CODE_UNSUPPORTED, "Binary websockify does not exist")
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
def start(port, vncport, sslcert=None):
	port = params.convert(port, convert=int, gte=1, lt=2**16)
	vncport = params.convert(vncport, convert=int, gte=1, lt=2**16)
	sslcert = params.convert(sslcert, convert=str, null=True, check=os.path.exists)
	WebsockifyError.check(not netstat.isPortFree(vncport), WebsockifyError.CODE_DEST_PORT_FREE, "Destination port is free", {"port": vncport})
	netstat.checkPortFree(port, tcp=True, ipv4=True)
	pid = spawnDaemon(["websockify", "0.0.0.0:%d" % port, "localhost:%d" % vncport] + (["--cert=%s" % sslcert] if sslcert else []))
	try:
		wait.waitFor(lambda :netstat.isPortUsedBy(port, pid), failCond=lambda :not proc.isAlive(pid))
		return pid
	except wait.WaitError:
		proc.autoKill(pid, group=True)
		raise

@_public
def stop(pid):
	proc.autoKill(pid, group=True)
	WebsockifyError.check(not proc.isAlive(pid), WebsockifyError.CODE_STILL_RUNNING, "Failed to stop websockify")
