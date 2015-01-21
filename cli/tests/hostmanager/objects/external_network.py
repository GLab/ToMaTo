import lib, time, os

from openvz import checkCreate as openvzCreate
from openvz import tearDown as openvzTearDown


def checkCreate(indent=""):
	print indent + "creating external_network element..."
	res = element_create("external_network", attrs={'network': 'internet'})
	assert res["id"]
	print indent + "\tID: %d" % res["id"]
	return res["id"]

def checkRemove(id, indent=""):
	print indent + "removing external_network element..."
	res = element_remove(id)
	assert not res

def tearDown(id, indent=""):
	try:
		info = element_info(id)
	except:
		return
	checkRemove(id, indent=indent)

def tearDownConnection(id, indent=""):
	try:
		info = connection_info(id)
	except:
		return
	connection_remove(id)

def check(indent="", shellError=False):
	print indent + "checking External Network element type..." 
	indent += "\t"
	try:
		print indent+"creating external_network..."
		id = checkCreate(indent=indent)

		print indent+"creating openvz device with one interface..."
		dev = element_create("openvz")["id"]
		print indent+"\tID: %d" % dev
		eth0 = element_create("openvz_interface", dev, {"use_dhcp": True})["id"]		
		print indent+"\tID: %d" % eth0

		print indent+"connecting interface with network..."		
		con = connection_create(eth0, id)["id"]
		print indent+"\tID: %d" % con
		
		print indent+"starting openvz device..."
		element_action(dev, "prepare")
		element_action(dev, "start")
		
		print indent+"checking connectivity..."
		time.sleep(5)
		element_action(dev, "execute", {"cmd": "ping -I eth0 -A -c 10 -n -q 8.8.8.8"})
		
		print indent+"disconnecting interface and network..."		
		connection_remove(con)
		
		print indent+"tearing down openvz device..."
		openvzTearDown(dev, indent=indent)

		print indent+"removing external network..."
		checkRemove(id, indent=indent)
	except:
		import traceback
		traceback.print_exc()
		if shellError:
			shell()
	finally:
		tearDownConnection(con, indent)
		tearDown(id, indent=indent)
		openvzTearDown(dev, indent=indent)

if __name__ == "__main__":
	try:
		check(shellError=True)
	except:
		import traceback
		traceback.print_exc()