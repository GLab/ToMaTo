import os

def _ifacePath(ifname):
	return "/sys/class/net/%s" % ifname

def _brifPath(brname):
	return os.path.join(_ifacePath(brname), "brif")

def ifaceExists(ifname):
	return os.path.exists(_ifacePath(ifname))

def ifaceList():
	return os.listdir(_ifacePath(""))

def bridgeExists(brname):
	return os.path.exists(_brifPath(brname))

def bridgeList():
	return filter(bridgeExists, ifaceList())

def bridgeInterfaces(brname):
	return os.listdir(_brifPath(brname))

def ifaceBridge(ifname):
	brlink = os.path.join(_ifacePath(ifname), "brport/bridge")
	if not os.path.exists(brlink):
		return None
	return os.path.basename(os.readlink(brlink))