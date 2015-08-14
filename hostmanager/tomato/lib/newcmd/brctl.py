from . import Error, SUPPORT_CHECK_PERIOD
from util import run, net, cmd, cache
import os

class BrctlError(Error):
	CODE_UNKNOWN="brctl.unknown"
	CODE_UNSUPPORTED="brctl.unsupported"
	CODE_NO_SUCH_BRIDGE="brctl.no_such_bridge"
	CODE_NO_SUCH_IFACE="brctl.no_such_iface"

@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def _check():
	BrctlError.check(os.geteuid() == 0, BrctlError.CODE_UNSUPPORTED, "Not running as root")
	BrctlError.check(cmd.exists("brctl"), BrctlError.CODE_UNSUPPORTED, "Binary brctl does not exist")
	return True

def _public(method):
	def call(*args, **kwargs):
		_check()
		return method(*args, **kwargs)
	call.__name__ = method.__name__
	call.__doc__ = method.__doc__
	return call

def checkSupport():
	return _check()

@_public
def create(brname, stp=True):
	run(["brctl", "addbr", brname])
	run(["brctl", "stp", brname, {True: "on", False: "off"}[stp]])
	
@_public
def remove(brname):
	BrctlError.check(net.bridgeExists(brname), BrctlError.CODE_NO_SUCH_BRIDGE, "No such bridge", {"bridge": brname})
	run(["brctl", "delbr", brname])
	
@_public
def attach(brname, ifname):
	BrctlError.check(net.bridgeExists(brname), BrctlError.CODE_NO_SUCH_BRIDGE, "No such bridge", {"bridge": brname})
	BrctlError.check(net.ifaceExists(ifname), BrctlError.CODE_NO_SUCH_IFACE, "No such interface", {"interface": ifname})
	run(["brctl", "addif", brname, ifname])
	
@_public
def detach(brname, ifname):
	BrctlError.check(net.bridgeExists(brname), BrctlError.CODE_NO_SUCH_BRIDGE, "No such bridge", {"bridge": brname})
	BrctlError.check(net.ifaceExists(ifname), BrctlError.CODE_NO_SUCH_IFACE, "No such interface", {"interface": ifname})
	if ifname in net.bridgeInterfaces(brname):
		run(["brctl", "delif", brname, ifname])
