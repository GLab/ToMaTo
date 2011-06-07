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
	assert top_action(topId, "execute", "device", "openvz1", attrs={"cmd": "cat /etc/deviceid"}) == "openvz1\n"
	top_action(topId, "execute", "device", "openvz2", attrs={"cmd": "echo openvz2 > /etc/deviceid"})
	assert top_action(topId, "execute", "device", "openvz2", attrs={"cmd": "cat /etc/deviceid"}) == "openvz2\n"
	#stop topology
	print "\tstopping topology..."
	task = top_action(topId, "stop")
	waitForTask(task, assertSuccess=True)
	#download images
	print "\tdownloading images..."
	downurl1 = download_image_uri(topId, "openvz1")
	download(downurl1,"openvz1.tar.gz")
	assert os.path.getsize("openvz1.tar.gz") > 10000000
	downurl2 = download_image_uri(topId, "openvz2")
	download(downurl2,"openvz2.tar.gz")
	assert os.path.getsize("openvz2.tar.gz") > 10000000
	downurl3 = download_image_uri(topId, "kvm1")
	download(downurl3,"kvm1.qcow2")
	assert os.path.getsize("kvm1.qcow2") > 100000000
	#switch images 
	print "\tuploading images..."
	upurl1 = upload_image_uri(topId, "openvz1")
	upload(upurl1["upload_url"], "openvz2.tar.gz")
	use_uploaded_image(topId, "openvz1", upurl1["filename"], direct=True)
	upurl2 = upload_image_uri(topId, "openvz2")
	upload(upurl2["upload_url"], "openvz1.tar.gz")
	use_uploaded_image(topId, "openvz2", upurl2["filename"], direct=True)
	upurl3 = upload_image_uri(topId, "kvm1")
	upload(upurl3["upload_url"], "kvm1.qcow2")
	use_uploaded_image(topId, "kvm1", upurl3["filename"], direct=True)
	#start topology
	print "\tstarting topology..."
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)
	#check that images have been switched
	print "\tchecking images..."
	assert top_action(topId, "execute", "device", "openvz1", attrs={"cmd": "cat /etc/deviceid"}) == "openvz2\n"
	assert top_action(topId, "execute", "device", "openvz2", attrs={"cmd": "cat /etc/deviceid"}) == "openvz1\n"
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
	