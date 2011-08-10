from lib.misc import *
import time, os

verbatimCodes = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ\n"
translationCodes = {".": "0x34", "-": "0x35", "*": "0x37", " ": "0x39"}
def keycodes(s):
	codes = []
	for c in s:
		if c in translationCodes:
			codes.append(translationCodes[c])
		else:
			if not c in verbatimCodes:
				print "Unknown translation for %s, just trying" % c
			codes.append(c)
	return codes
			

def simpleTop_checkTincConnectors(topId):
	print "\tstarting topology..."
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)
	time.sleep(30)
	print "\tlogin to kvm1..."
	top_action(topId, "send_keys", "device", "kvm1", attrs={"keycodes": keycodes("root\n")})
	time.sleep(5)
	top_action(topId, "send_keys", "device", "kvm1", attrs={"keycodes": keycodes("glab-root\n")})
	time.sleep(5)
	print "\tconfigure ip, netmask and route on kvm1..."
	top_action(topId, "send_keys", "device", "kvm1", attrs={"keycodes": keycodes("ifconfig eth0 10.1.2.1 netmask 255.255.255.0 up\n")})
	top_action(topId, "send_keys", "device", "kvm1", attrs={"keycodes": keycodes("route add default gw 10.1.2.254\n")})
	top_action(topId, "send_keys", "device", "kvm1", attrs={"keycodes": keycodes("ifconfig eth2 10.2.0.2 netmask 255.255.255.0 up\n")})
	print "\tchecking hub..."
	assert link_check(topId, "openvz2", "10.2.0.2")
	print "\tchecking switch..."
	assert link_check(topId, "openvz1", "10.0.0.2")
	assert link_check(topId, "openvz2", "10.0.0.1")
	top_action(topId, "execute", "device", "openvz1", attrs={"cmd": "route add default gw 10.1.1.254; true"})
	print "\tchecking router, to remote device..."
	assert link_check(topId, "openvz1", "10.1.2.1")
	print "\tchecking router, no connection to host..."
	host = top_info(topId)["devices"]["openvz1"]["attrs"]["host"]
	assert not link_check(topId, "openvz1", host, tries=2, waitBetween=1)
	#FIXME: test ipv6
	
if __name__ == "__main__":
	from tests.top.simple import top
	errors_remove()
	topId = top_create()
	try:
		print "creating topology..."
		top_modify(topId, jsonToMods(top), True)

		print "testing tinc connectors..."
		simpleTop_checkTincConnectors(topId)

		print "destroying topology..."
		top_action(topId, "destroy", direct=True)
	except:
		import traceback
		traceback.print_exc()
		print "-" * 50
		errors_print()
		print "-" * 50
		print "Topology id is: %d" % topId
		raw_input("Press enter to remove topology")
	finally:
		top_action(topId, "remove", direct=True)
	
