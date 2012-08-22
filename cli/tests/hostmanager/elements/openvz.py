import lib, time, os

def checkCreate(indent=""):
	print indent + "creating element..."
	res = element_create("openvz")
	assert res["id"]
	print indent + "\tID: %d" % res["id"]
	return res["id"]

def checkCreateInterface(id, indent=""):
	print indent + "creating interface..."
	res = element_create("openvz_interface", id)
	assert res["id"]
	print indent + "\tID: %d" % res["id"]
	return res["id"]

def checkRemove(id, indent=""):
	print indent + "removing element..."
	res = element_remove(id)
	assert res == {}

def checkAction(id, action, params={}, assertState=None, indent=""):
	print indent + "executing action %s on element..." % action
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
	if info["state"] == "prepared":
		checkAction(id, "destroy", assertState="created", indent=indent)
	if info["state"] == "started":
		checkAction(id, "stop", assertState="prepared", indent=indent)
		checkAction(id, "destroy", assertState="created", indent=indent)
	checkRemove(id, indent=indent)

def check(indent="", shellError=False):
	print indent + "checking OpenVZ element type..." 
	indent += "\t"
	try:
		id = checkCreate(indent=indent)

		id1 = checkCreateInterface(id, indent=indent)
		
		checkAction(id, "prepare", assertState="prepared", indent=indent)
		
		id2 = checkCreateInterface(id, indent=indent)

		print indent + "checking attribute changes in state prepared..."
		element_modify(id, {"ram": 128, "diskspace": 10000, "template": None})
		
		checkAction(id, "start", assertState="started", indent=indent)
		
		print indent + "checking VNC server..."
		info = element_info(id)
		assert "attrs" in info and "vncport" in info["attrs"]
		assert lib.tcpPortOpen(__hostname__, info["attrs"]["vncport"]), "VNC Port not open"
		
		print indent + "checking execute..."
		res = element_action(id, "execute", {"cmd":"whoami"})
		assert res.strip() == "root", "Result of whoami was %s" % res
		
		print indent + "checking attribute changes in state started..."
		element_modify(id1, {"ip4address": "10.0.0.1/24", "ip6address": "fdb2:a935:f0f5:b82b::1/64"})
		element_modify(id, {"rootpassword": "test123", "hostname": "test", "gateway4": "10.0.0.254", "gateway6": "fdb2:a935:f0f5:b82b::ffff"})
		element_modify(id1, {"use_dhcp": True})
		
		checkAction(id, "stop", assertState="prepared", indent=indent)
		
		print indent + "checking disk download and upload..."
		fileserver_port = host_info()["fileserver_port"]
		assert fileserver_port	
		grant = element_action(id, "download_grant")
		assert grant
		lib.download("http://%s:%d/%s/download" % (__hostname__, fileserver_port, grant), "disk.tar.gz")
		assert os.path.exists("disk.tar.gz")
		grant = element_action(id, "upload_grant")
		assert grant
		lib.upload("http://%s:%d/%s/upload" % (__hostname__, fileserver_port, grant), "disk.tar.gz")
		element_action(id, "upload_use")
		
		checkRemove(id1, indent=indent)		
		
		checkAction(id, "destroy", assertState="created", indent=indent)
		
		checkRemove(id, indent=indent)
	except:
		import traceback
		traceback.print_exc()
		if shellError:
			shell()
	finally:
		if os.path.exists("disk.tar.gz"):
			os.remove("disk.tar.gz")
		tearDown(id, indent)

if __name__ == "__main__":
	try:
		check(shellError=True)
	except:
		import traceback
		traceback.print_exc()