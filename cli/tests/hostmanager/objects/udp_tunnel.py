import lib, time, os

from openvz import checkCreate as openvzCreate
from openvz import tearDown as openvzTearDown


def checkCreate(indent=""):
	print indent + "creating udp_tunnel element..."
	res = element_create("udp_tunnel")
	assert res["id"]
	print indent + "\tID: %d" % res["id"]
	return res["id"]

def checkRemove(id, indent=""):
	print indent + "removing udp_tunnel element..."
	res = element_remove(id)
	assert not res

def checkAction(id, action, params={}, assertState=None, indent=""):
	print indent + "executing action %s on udp_tunnel element..." % action
	res = element_action(id, action, params)
	if assertState:
		info = element_info(id)
		assert info["state"] == assertState
	return res

def tearDown(id, indent=""):
	try:
		info = element_info(id)
	except:
		return
	if info["state"] == "started":
		checkAction(id, "stop", assertState="created", indent=indent)
	checkRemove(id, indent=indent)

def tearDownConnection(id, indent=""):
	try:
		info = connection_info(id)
	except:
		return
	if info["state"] == "started":
		connection_action(id, "stop")
	connection_remove(id)

def check(indent="", shellError=False):
	print indent + "checking UDP-Tunnel element type..." 
	indent += "\t"
	try:
		print indent+"creating udp_tunnel endpoints..."
		id1 = checkCreate(indent=indent)
		id2 = checkCreate(indent=indent)

		print indent+"pointing endpoints towards each others..."
		info1 = element_info(id1)
		info2 = element_info(id2)
		element_modify(id2, {"connect": "%s:%d" % (__hostname__, info1["attrs"]["port"])})

		print indent+"creating openvz device with two interfaces..."
		dev = element_create("openvz")["id"]
		print indent+"\tID: %d" % dev
		eth0 = element_create("openvz_interface", dev, {"use_dhcp": False, "ip4address": "10.0.0.1/24"})["id"]		
		print indent+"\tID: %d" % eth0
		eth1 = element_create("openvz_interface", dev, {"use_dhcp": False, "ip4address": "10.0.0.2/24"})["id"]
		print indent+"\tID: %d" % eth1

		print indent+"connecting interfaces with endpoints..."		
		con1 = connection_create(eth0, id1)["id"]
		print indent+"\tID: %d" % con1
		con2 = connection_create(eth1, id2)["id"]
		print indent+"\tID: %d" % con2
		
		print indent+"starting openvz device..."
		element_action(dev, "prepare")
		element_action(dev, "start")
		
		print indent+"starting udp_tunnel endpoints..."
		element_action(id1, "start")
		element_action(id2, "start")

		print indent+"starting connections..."
		connection_action(con1, "start")
		connection_action(con2, "start")
		
		print indent+"checking connectivity..."
		time.sleep(5)
		element_action(dev, "execute", {"cmd": "ping -I eth0 -A -c 10 -n -q 10.0.0.2"})
		
		print indent+"stopping connections..."
		connection_action(con1, "stop")
		connection_action(con2, "stop")

		print indent+"disconnecting interfaces and endpoints..."		
		connection_remove(con1)
		connection_remove(con2)
		
		print indent+"stopping tinc endpoints..."
		element_action(id1, "stop")
		element_action(id2, "stop")

		print indent+"tearing down openvz device..."
		openvzTearDown(dev, indent=indent)

		print indent+"removing tinc endpoints..."
		checkRemove(id1, indent=indent)
		checkRemove(id2, indent=indent)
	except:
		import traceback
		traceback.print_exc()
		if shellError:
			shell()
	finally:
		tearDownConnection(con1, indent)
		tearDownConnection(con2, indent)
		tearDown(id1, indent)
		tearDown(id2, indent)
		openvzTearDown(dev, indent=indent)

if __name__ == "__main__":
	try:
		check(shellError=True)
	except:
		import traceback
		traceback.print_exc()