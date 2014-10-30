import os, random

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

def trafficInfo(ifname):
	if not ifaceExists(ifname):
		return None, None
	with open(os.path.join(_ifacePath(ifname), "statistics/tx_bytes")) as fp:
		tx = int(fp.readline().strip())
	with open(os.path.join(_ifacePath(ifname), "statistics/rx_bytes")) as fp:
		rx = int(fp.readline().strip())
	return rx, tx

def randomMac():
	bytes = [random.randint(0x00, 0xff) for _ in xrange(6)]
	bytes[0] = bytes[0] & 0xfc | 0x02 # local and individual
	return ':'.join(map(lambda x: "%02x" % x, bytes))