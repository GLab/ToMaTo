import lib, time, os

from openvz import checkCreate as openvzCreate
from openvz import tearDown as openvzTearDown


def checkCreate(e1, e2, indent=""):
	print indent + "creating bridge connection..."
	res = connection_create(e1, e2, "bridge")
	assert res["id"]
	print indent + "\tID: %d" % res["id"]
	return res["id"]

def checkRemove(id, indent=""):
	print indent + "removing bridge connection..."
	res = connection_remove(id)
	assert res == {}

def checkAction(id, action, params={}, assertState=None, indent=""):
	print indent + "executing action %s on bridge connection..." % action
	res = connection_action(id, action, params)
	if assertState:
		info = connection_info(id)
		assert info["state"] == assertState
	return res

def tearDown(id, indent=""):
	try:
		info = connection_info(id)
	except:
		return
	if info["state"] == "started":
		checkAction(id, "stop", assertState="created", indent=indent)
	checkRemove(id, indent=indent)

def check(indent="", shellError=False):
	print indent + "checking Bridge connection type..." 
	indent += "\t"
	try:
		print indent+"creating openvz device with two interfaces..."
		dev = element_create("openvz")["id"]
		print indent+"\tID: %d" % dev
		eth0 = element_create("openvz_interface", dev, {"use_dhcp": False, "ip4address": "10.0.0.1/24"})["id"]		
		print indent+"\tID: %d" % eth0
		eth1 = element_create("openvz_interface", dev, {"use_dhcp": False, "ip4address": "10.0.0.2/24"})["id"]
		print indent+"\tID: %d" % eth1

		print indent+"creating bridge between interfaces..."
		id = checkCreate(eth0, eth1, indent=indent)

		print indent+"starting openvz device..."
		element_action(dev, "prepare")
		element_action(dev, "start")
		
		print indent+"starting bridge..."
		checkAction(id, "start", assertState="started", indent=indent)
		
		print indent+"checking connectivity..."
		time.sleep(5)
		element_action(dev, "execute", {"cmd": "ping -I eth0 -A -c 10 -n -q 10.0.0.2"})
		
		print indent+"changing link emulation values..."
		connection_modify(id, {"emulation": True, "delay_to": 5.0, "delay_from": 2.0, "jitter_to": 0.0,
			"jitter_from": 0.0, "distribution_to": "uniform", "distribution_from": "uniform", 
			"bandwidth_to": 10000, "bandwidth_from": 10000, "lossratio_to": 0.0, "lossratio_from": 0.0,
			"duplicate_to": 0.0, "duplicate_from": 0.0, "corrupt_to": 0.0, "corrupt_from": 0.0})
		
		print indent+"checking connectivity..."
		element_action(dev, "execute", {"cmd": "ping -I eth0 -A -c 10 -n -q 10.0.0.2"})

		print indent+"checking file capture..."
		connection_modify(id, {"capturing": True, "capture_mode": "file", "capture_filter": "icmp"})
		
		element_action(dev, "execute", {"cmd": "ping -I eth0 -A -c 10 -n -q 10.0.0.2"})
		
		print indent+"checking capture download..."
		fileserver_port = host_info()["fileserver_port"]
		assert fileserver_port	
		grant = connection_action(id, "download_grant")
		assert grant
		lib.download("http://%s:%d/%s/download" % (__hostname__, fileserver_port, grant), "capture.pcap")
		assert os.path.exists("capture.pcap")

		print indent+"checking live capture..."
		connection_modify(id, {"capture_mode": "net"})
		info = connection_info(id)
		assert "attrs" in info and "capture_port" in info["attrs"]
		assert lib.tcpPortOpen(__hostname__, info["attrs"]["capture_port"]), "Capture port not open"	
		
		print indent+"stopping bridge..."
		checkAction(id, "stop", assertState="created", indent=indent)

		print indent+"removing bridge..."
		checkRemove(id, indent=indent)

		print indent+"tearing down openvz device..."
		openvzTearDown(dev, indent=indent)
	except:
		import traceback
		traceback.print_exc()
		if shellError:
			shell()
	finally:
		if os.path.exists("capture.pcap"):
			os.remove("capture.pcap")
		tearDown(id, indent)
		openvzTearDown(dev, indent=indent)

if __name__ == "__main__":
	try:
		check(shellError=True)
	except:
		import traceback
		traceback.print_exc()