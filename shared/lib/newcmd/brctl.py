from . import Error 
from util import run, CommandError, net, cmd
import os

class BrctlError(Error):
	CATEGORY="cmd_brctl"
	TYPE_UNKNOWN="unknown"
	TYPE_UNSUPPORTED="unsupported"
	TYPE_NO_SUCH_BRIDGE="no_such_bridge"
	TYPE_NO_SUCH_IFACE="no_such_iface"
	def __init__(self, type, message, data=None):
		Error.__init__(self, category=BrctlError.CATEGORY, type=type, message=message, data=data)

def _check():
	BrctlError.check(os.geteuid() == 0, BrctlError.TYPE_UNSUPPORTED, "Not running as root")
	BrctlError.check(cmd.exists("brctl"), BrctlError.TYPE_UNSUPPORTED, "Binary brctl does not exist")
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
def create(brname):
	run(["brctl", "addbr", brname])
	
@_public
def remove(brname):
	BrctlError.check(net.bridgeExists(brname), BrctlError.TYPE_NO_SUCH_BRIDGE, "No such bridge: %s" % brname, {"bridge": brname})
	run(["brctl", "delbr", brname])
	
@_public
def attach(brname, ifname):
	BrctlError.check(net.bridgeExists(brname), BrctlError.TYPE_NO_SUCH_BRIDGE, "No such bridge: %s" % brname, {"bridge": brname})
	BrctlError.check(net.ifaceExists(ifname), BrctlError.TYPE_NO_SUCH_IFACE, "No such interface: %s" % ifname, {"interface": ifname})
	run(["brctl", "addif", brname, ifname])
	
@_public
def detach(brname, ifname):
	BrctlError.check(net.bridgeExists(brname), BrctlError.TYPE_NO_SUCH_BRIDGE, "No such bridge: %s" % brname, {"bridge": brname})
	BrctlError.check(net.ifaceExists(ifname), BrctlError.TYPE_NO_SUCH_IFACE, "No such interface: %s" % ifname, {"interface": ifname})
	if ifname in net.bridgeInterfaces(brname):
		run(["brctl", "delif", brname, ifname])
