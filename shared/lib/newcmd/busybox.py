from . import netstat, Error, SUPPORT_CHECK_PERIOD
from util import params, cmd, cache, proc, spawnDaemon, wait
import os

class BusyboxError(Error):
	CODE_UNKNOWN="busybox.unknown"
	CODE_UNSUPPORTED="busybox.unsupported"
	CODE_STILL_RUNNING="busybox.still_running"

@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def plugins():
	return cmd.run(["busybox", "--list"]).splitlines()

@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def isSupported():
	return cmd.exists("busybox")

def _check(plugin=None):
	BusyboxError.check(isSupported(), BusyboxError.CODE_UNSUPPORTED, "Binary busybox does not exist")
	if plugin:
		BusyboxError.check(plugin in plugins(), BusyboxError.CODE_UNSUPPORTED, "Plugin not supported", {"plugin": plugin})
	return True

def _public(plugin=None):
	def wrap(method):
		def call(*args, **kwargs):
			_check(plugin)
			return method(*args, **kwargs)
		call.__name__ = method.__name__
		call.__doc__ = method.__doc__
		return call
	return wrap

######################
### Public methods ###
######################

def checkSupport():
	return _check()

@_public("httpd")
def httpd_start(folder, port):
	folder = params.convert(folder, convert=os.path.realpath, check=os.path.exists)
	port = params.convert(port, convert=int, gte=1, lt=2**16)
	netstat.checkPortFree(port)
	pid = spawnDaemon(["busybox", "httpd", "-f", "-p", str(port)], cwd=folder)
	try:
		wait.waitFor(lambda :netstat.isPortUsedBy(port, pid), failCond=lambda :not proc.isAlive(pid))
		return pid
	except wait.WaitError:
		proc.autoKill(pid, group=True)
		raise

@_public(None)
def httpd_stop(pid):
	proc.autoKill(pid, group=True)
	BusyboxError.check(not proc.isAlive(pid), BusyboxError.CODE_STILL_RUNNING, "Failed to stop http server")