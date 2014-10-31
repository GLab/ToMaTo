import json
from . import Error, SUPPORT_CHECK_PERIOD
from util import spawnDaemon, params, proc, cmd, net, cache

class IpspyError(Error):
	CODE_UNKNOWN="ipspy.unknown"
	CODE_UNSUPPORTED="ipspy.unsupported"
	CODE_STILL_RUNNING="ipspy.still_running"
	CODE_PARSE_ERROR="ipspy.parse_error"

@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def _check():
	IpspyError.check(cmd.exists("ipspy"), IpspyError.CODE_UNSUPPORTED, "Binary ipspy does not exist")
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
def start(iface, output):
	iface = params.convert(iface, convert=str, check=net.ifaceExists)
	output = params.convert(output, convert=str)
	return spawnDaemon(["ipspy", "-i", iface, "-o", output, "--dhcp"])

@_public
def read(filename):
	data = ""
	try:
		with open(filename, "r") as fn:
			data = json.load(fn)
			ips = data.keys()
			ips.sort(key=lambda ip: data[ip]["last_seen"] + data[ip]["pkg_count"] * 1000, reverse=True)
			return ips
	except Exception, err:
		raise IpspyError(IpspyError.CODE_PARSE_ERROR, "Failed to parse data", {"filename": filename, "data": data, "error": repr(err)})


@_public
def stop(pid):
	proc.autoKill(pid, group=True)
	IpspyError.check(not proc.isAlive(pid), IpspyError.CODE_STILL_RUNNING, "Failed to stop ipspy")