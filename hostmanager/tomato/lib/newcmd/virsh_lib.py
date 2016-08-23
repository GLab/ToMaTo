from util import run
from ..constants import ActionName, StateName, TypeName
from ..error import UserError, InternalError
import time
import xml.etree.ElementTree as ET
import uuid, random


class virsh:

	vm_list = []
	config_path = "/home/stephan/ToMaTo/hostmanager/tomato/lib/standard_kvm_config.xml" #standard_kvm_config.xml"
	imagepath = ""
	original_image = ""

	TYPE = TypeName.KVM
	CAP_ACTIONS = {
		ActionName.PREPARE: [StateName.CREATED],
		ActionName.DESTROY: [StateName.PREPARED],
		ActionName.START: [StateName.PREPARED],
		ActionName.STOP: [StateName.STARTED],
	}
	CAP_NEXT_STATE = {
		ActionName.PREPARE: StateName.PREPARED,
		ActionName.DESTROY: StateName.CREATED,
		ActionName.START: StateName.STARTED,
		ActionName.STOP: StateName.PREPARED,
	}

	def __init__(self):
		#go through currently listed vms and add them to vm_list
		list_raw = run(["virsh", "list --all"])
		list_split = list_raw.split("vm_")[1:]
		list_vm_ids = []
		for item in list_split:
			list_vm_ids.append(item.split(" ")[0])
		for id in list_vm_ids:
			self.vm_list.append(int(id))
		print self.vm_list

		#read standard kvm config, extracting path to images
		self.tree = ET.parse(self.config_path)
		self.root = self.tree.getroot()

		for devices in self.root.findall('devices'):
			for disks in devices.findall('disk'):
				for original in disks.findall('source'):
					self.original_image = original.get('file')
					print self.original_image
					parts = self.original_image.split("/")
					self.imagepath = ""
					for i in range(0, parts.__len__() - 1):
						self.imagepath += parts[i]
						self.imagepath += "/"

	def vm_start(self, vmid, params=None):
		#check if vmid is already in list:
		if self.vm_list.__contains__(vmid):
			run(["virsh", "start", "%s" % vmid])
		else:
			InternalError.check(self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does not exist on this host and cannot be started" % vmid, data={"type": self.TYPE})

	def vm_prepare(self, vmid, type="kvm"):
		InternalError.check(not self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does already exist on this host" % vmid, data={"type": self.TYPE})
		#copy template
		path = self.imagepath
		path += ("%s.qcow2" % vmid)
		config_path = self.imagepath
		config_path += ("%s.xml" % vmid)
		run(["cp", self.original_image, path])
		#copy xml file and adjust UUID etc.
		self.root.set("id",str(vmid))
		self.root.find("name").text = ("vm_%s" % vmid)
		vm_uuid = uuid.uuid4()
		self.root.find("uuid").text = str(vm_uuid)
		self.root.find("devices").find("disk").find("source").set("file",path)
		self.root.find("devices").find("interface").find("mac").set("address", self.random_mac())
		self.root.find("seclabel").find("label").text = ("libvirt-%s" % vm_uuid)
		self.root.find("seclabel").find("imagelabel").text = ("libvirt-%s" % vm_uuid)

		self.tree.write(config_path)

		#define and start vm
		run(["virsh", "define", "%s" % config_path])
		run(["virsh", "create", "%s" % config_path])

	def vm_stop(self, vmid, forced=False):
		InternalError.check(self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does not exist on this host and cannot be stopped" % vmid, data={"type": self.TYPE})
		if forced:
			run(["virsh", "destroy", "vm_%s" % vmid])
		else:
			run(["virsh", "shutdown", "vm_%s" % vmid])

	def vm_destroy(self, vmid):
		InternalError.check(self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does not exist on this host and cannot be destroyed" % vmid, data={"type": self.TYPE})
		if self.checkState(vmid) == "running":
			run(["virsh", "destroy", "vm_%s" % vmid])
		while(self.checkState(vmid) != "shut off"):
			time.sleep(1)
		time.sleep(1)
		run(["virsh", "undefine", "vm_%s" % vmid]) #--remove-all-storage --managed-save --snapshots-metadata
		path = self.imagepath
		path += ("%s.qcow2" % vmid)
		run(["rm", path])
		config_path = self.imagepath
		config_path += ("%s.xml" % vmid)
		run(["rm", config_path])
		self.vm_list.remove(vmid)

	def checkState(self, vmid):
		state = run(["virsh", "domstate", "vm_%s" % vmid])
		state = state[:-2]
		#print self.state
		return state

	def random_mac(self):
		mac = [ 0x00, 0x16, 0x3e,
			random.randint(0x00, 0x7f),
			random.randint(0x00, 0xff),
			random.randint(0x00, 0xff) ]
		return ':'.join(map(lambda x: "%02x" % x, mac))

