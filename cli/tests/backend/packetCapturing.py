from lib.misc import *
import time, os, socket

def simpleTop_checkPacketCapturing(topId):
	#make sure topology is started
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)
	#assert no packet capture available
	con_info = top_info(topId)["connectors"]["switch1"]["connections"]["openvz1.eth0"]
	assert not con_info["attrs"]["capture_to_file"]
	assert not con_info["attrs"]["capture_via_net"]
	assert not con_info["attrs"]["capture_filter"]
	assert not con_info["capabilities"]["action"]["download_capture"]
	#enable packet capturing to file
	top_modify(topId, [{"type":"connection-configure", "element":"switch1", "subelement":"openvz1.eth0", "properties":{"capture_to_file":True}}], direct=True)
	con_info = top_info(topId)["connectors"]["switch1"]["connections"]["openvz1.eth0"]
	assert con_info["attrs"]["capture_to_file"]
	#send some pings
	# throw away the first few samples
	i = 0
	while i < 10 and not link_info(topId, "openvz1", "10.0.0.2", samples=10):
		i += 1
		time.sleep(0.1)
	link_info(topId, "openvz1", "10.0.0.2", samples=100)
	#download capture file
	con_info = top_info(topId)["connectors"]["switch1"]["connections"]["openvz1.eth0"]
	assert con_info["capabilities"]["action"]["download_capture"]
	url = top_action(topId, "download_capture", "connector", "switch1", attrs={"iface":"openvz1.eth0"})
	download(url,"capture.pcap")
	assert os.path.getsize("capture.pcap") > 1000
	os.remove("capture.pcap")
	#disable packet capturing to file
	top_modify(topId, [{"type":"connection-configure", "element":"switch1", "subelement":"openvz1.eth0", "properties":{"capture_to_file":False}}], direct=True)
	con_info = top_info(topId)["connectors"]["switch1"]["connections"]["openvz1.eth0"]
	assert not con_info["attrs"]["capture_to_file"]
	#enable live capture
	top_modify(topId, [{"type":"connection-configure", "element":"switch1", "subelement":"openvz1.eth0", "properties":{"capture_via_net":True}}], direct=True)
	con_info = top_info(topId)["connectors"]["switch1"]["connections"]["openvz1.eth0"]
	assert con_info["attrs"]["capture_via_net"]
	assert con_info["capabilities"]["other"]["live_capture"]
	#send some pings in background process
	top_action(topId, "execute", "device", "openvz1", attrs={"cmd": "ping 10.0.0.2 -c 1000 >/dev/null 2>&1 </dev/null &"})
	#listen for live capture
	assert con_info["attrs"]["capture_port"]
	assert con_info["attrs"]["capture_host"]
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((con_info["attrs"]["capture_host"], con_info["attrs"]["capture_port"]))
	data = s.recv(250)
	assert len(data)
	data = s.recv(250)
	assert len(data)
	#disable capture
	top_modify(topId, [{"type":"connection-configure", "element":"switch1", "subelement":"openvz1.eth0", "properties":{"capture_via_net":False}}], direct=True)
	con_info = top_info(topId)["connectors"]["switch1"]["connections"]["openvz1.eth0"]
	assert not con_info["attrs"]["capture_via_net"]
	#assert no packet capture available
	assert not con_info["capabilities"]["other"]["live_capture"]

if __name__ == "__main__":
	from tests.top.simple import top
	errors_remove()
	topId = top_create()
	try:
		print "creating topology..."
		top_modify(topId, jsonToMods(top), True)

		print "starting topology..."
		task = top_action(topId, "start")
		waitForTask(task, assertSuccess=True)

		print "testing packet capturing..."
		simpleTop_checkPacketCapturing(topId)

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
	