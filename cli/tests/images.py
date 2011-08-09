from lib.misc import *
import time, os

def simpleTop_checkImages(topId):
	#make sure topology is started
	print "\tstarting topology..."
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)
	#mark hosts uniquely
	print "\tmarking hosts..."
	top_action(topId, "execute", "device", "openvz1", attrs={"cmd": "echo openvz1 > /etc/deviceid"})
	assert top_action(topId, "execute", "device", "openvz1", attrs={"cmd": "cat /etc/deviceid"}) == "openvz1"
	top_action(topId, "execute", "device", "openvz2", attrs={"cmd": "echo openvz2 > /etc/deviceid"})
	assert top_action(topId, "execute", "device", "openvz2", attrs={"cmd": "cat /etc/deviceid"}) == "openvz2"
	#stop topology
	print "\tstopping topology..."
	task = top_action(topId, "stop")
	waitForTask(task, assertSuccess=True)
	#download images
	print "\tdownloading images..."
	downurl1 = top_action(topId, "download_image", "device", "openvz1")
	download(downurl1,"openvz1.tar.gz")
	assert os.path.getsize("openvz1.tar.gz") > 10000000
	downurl2 = top_action(topId, "download_image", "device", "openvz2")
	download(downurl2,"openvz2.tar.gz")
	assert os.path.getsize("openvz2.tar.gz") > 10000000
	downurl3 = top_action(topId, "download_image", "device", "kvm1")
	download(downurl3,"kvm1.qcow2")
	assert os.path.getsize("kvm1.qcow2") > 100000000
	downurl4 = top_action(topId, "download_image", "device", "prog1")
	download(downurl4,"prog1.repy")
	assert 10000 > os.path.getsize("prog1.repy") > 1000
	#switch images 
	print "\tuploading images..."
	upurl1 = top_action(topId, "upload_image_prepare", "device", "openvz1")
	upload(upurl1["upload_url"], "openvz2.tar.gz")
	task = top_action(topId, "upload_image_use", "device", "openvz1", attrs={"filename": upurl1["filename"]})
	waitForTask(task, assertSuccess=True)
	upurl2 = top_action(topId, "upload_image_prepare", "device", "openvz2")
	upload(upurl2["upload_url"], "openvz1.tar.gz")
	task = top_action(topId, "upload_image_use", "device", "openvz2", attrs={"filename": upurl2["filename"]})
	waitForTask(task, assertSuccess=True)
	upurl3 = top_action(topId, "upload_image_prepare", "device", "kvm1")
	upload(upurl3["upload_url"], "kvm1.qcow2")
	task = top_action(topId, "upload_image_use", "device", "kvm1", attrs={"filename": upurl3["filename"]})
	waitForTask(task, assertSuccess=True)
	upurl4 = top_action(topId, "upload_image_prepare", "device", "prog1")
	upload(upurl4["upload_url"], "prog1.repy")
	task = top_action(topId, "upload_image_use", "device", "prog1", attrs={"filename": upurl4["filename"]})
	waitForTask(task, assertSuccess=True)
	#start topology
	print "\tstarting topology..."
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)
	#check that images have been switched
	print "\tchecking images..."
	assert top_action(topId, "execute", "device", "openvz1", attrs={"cmd": "cat /etc/deviceid"}) == "openvz2"
	assert top_action(topId, "execute", "device", "openvz2", attrs={"cmd": "cat /etc/deviceid"}) == "openvz1"
	#remove files
	os.remove("openvz1.tar.gz")
	os.remove("openvz2.tar.gz")
	os.remove("kvm1.qcow2")
	
if __name__ == "__main__":
	from tests.top.simple import top
	errors_remove()
	topId = top_create()
	try:
		print "creating topology..."
		top_modify(topId, jsonToMods(top), True)

		print "testing image upload and download..."
		simpleTop_checkImages(topId)

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
	