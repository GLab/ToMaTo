from . import netstat, Error, SUPPORT_CHECK_PERIOD
from util import spawnDaemon, params, proc, cmd, net, cache, wait

class VpnCloudError(Error):
	CODE_UNKNOWN="vpncloud.unknown"
	CODE_UNSUPPORTED="vpncloud.unsupported"
	CODE_STILL_RUNNING="vpncloud.still_running"

@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def isSupported():
	return cmd.exists("vpncloud")

def _check():
	VpnCloudError.check(isSupported(), VpnCloudError.CODE_UNSUPPORTED, "Binary vpncloud does not exist")
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
def start(iface, address, port, network_id, peers):
	iface = params.convert(iface, convert=str, check=lambda iface: not net.ifaceExists(iface))
	address = params.convert(address, convert=str)
	port = params.convert(port, convert=int, gte=1, lt=2**16)
	network_id = params.convert(network_id, convert=int, gte=1, lt=1<<64)
	peers = params.convert(peers, convert=list)
	netstat.checkPortFree(port, tcp=False, udp=True, ipv4=True)
	connect = []
	for p in peers:
		connect += ["-c", p]
	pid = spawnDaemon(["vpncloud", "-d", iface, "-l", "%s:%d" % (address, port), "--network-id", "%d" % network_id] + connect)
	wait.waitFor(lambda :net.ifaceExists(iface), failCond=lambda :not proc.isAlive(pid))
	return pid

@_public
def stop(pid):
	proc.autoKill(pid)
	VpnCloudError.check(not proc.isAlive(pid), VpnCloudError.CODE_STILL_RUNNING, "Failed to stop vpncloud")