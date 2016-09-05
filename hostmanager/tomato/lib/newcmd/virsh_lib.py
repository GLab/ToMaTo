from util import run
from ..constants import ActionName, StateName, TypeName
from ..error import UserError, InternalError
import time
import xml.etree.ElementTree as ET
import uuid, random


class virsh:

	vm_list = []
	kvm_config_path = "/home/stephan/ToMaTo/hostmanager/tomato/lib/standard_kvm_config.xml" #standard_kvm_config.xml"
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

	def __init__(self,type):
		self.update_vm_list()

		self.TYPE = type
		if self.TYPE == TypeName.KVM:
			#read standard kvm config, extracting path to images
			self.tree = ET.parse(self.kvm_config_path)
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
		self.update_vm_list()
		if self.vm_list.__contains__(vmid):
			run(["virsh", "start", "%s" % vmid])
		else:
			InternalError.check(self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does not exist on this host and cannot be started" % vmid, data={"type": self.TYPE})

	def vm_prepare(self, vmid, type=TypeName.KVM, template=None):
		self.update_vm_list()
		InternalError.check(not self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does already exist on this host" % vmid, data={"type": self.TYPE})
		#read standard config:
		if type == TypeName.KVM:
			#read standard kvm config
			self.tree = ET.parse(self.kvm_config_path)
			self.root = self.tree.getroot()

		#copy template
		if type == TypeName.KVM and template == None:
			self._setImage(vmid, self.original_image)
		else:
			path = self.imagepath + template
			self._setImage(vmid, path)

		config_path = self.imagepath
		config_path += ("%s.xml" % vmid)
		#run(["cp", self.original_image, path])
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

		#define vm
		run(["virsh", "define", "%s" % config_path])
		#run(["virsh", "create", "%s" % config_path])

	def vm_stop(self, vmid, forced=False):
		self.update_vm_list()
		InternalError.check(self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does not exist on this host and cannot be stopped" % vmid, data={"type": self.TYPE})
		if forced:
			run(["virsh", "destroy", "vm_%s" % vmid])
		else:
			run(["virsh", "shutdown", "vm_%s" % vmid])

	def vm_destroy(self, vmid):
		self.update_vm_list()
		InternalError.check(self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does not exist on this host and cannot be destroyed" % vmid, data={"type": self.TYPE})
		if self._checkState(vmid) == "running":
			run(["virsh", "destroy", "vm_%s" % vmid])
		while(self._checkState(vmid) != "shut off"):
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

	def _checkState(self, vmid):
		state = run(["virsh", "domstate", "vm_%s" % vmid])
		state = state[:-2]
		#print self.state
		return state

	def getVMs(self):
		self.update_vm_list()
		return self.vm_list

	def getState(self,vmid):
		self.update_vm_list()
		#InternalError.check(self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does not exist on this host" % vmid, data={"type": self.TYPE})
		if self.vm_list.__contains__(vmid):
			if self._checkState(vmid) == "shut off":
				return StateName.PREPARED
			if self._checkState(vmid) == "running":
				return StateName.STARTED
		else:
			return StateName.CREATED

	def update_vm_list(self):
		#go through currently listed vms and add them to vm_list
		self.vm_list = []
		list_raw = run(["virsh", "list --all"])
		list_split = list_raw.split("vm_")[1:]
		list_vm_ids = []
		for item in list_split:
			list_vm_ids.append(item.split(" ")[0])
		for id in list_vm_ids:
			self.vm_list.append(int(id))
		#print self.vm_list

	def set_Attributes(self, vmid, attrs):
		self.update_vm_list()
		InternalError.check(self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does not exist on this host" % vmid, data={"type": self.TYPE})

		#reading xml file of vm:
		config_path = self.imagepath
		config_path += ("%s.xml" % vmid)
		self.tree = ET.parse(self.config_path)
		self.root = self.tree.getroot()

		print "checking attrs"
		print attrs
		for attr in attrs:
			print attr
			if attr == "cpu":
				InternalError.check(self.getState(vmid) == StateName.PREPARED, InternalError.HOST_ERROR, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})

				print "cpu changed"
				self.root.find("vcpu").text = str(attrs.get("cpu"))
			if attr == "ram":
				InternalError.check(self.getState(vmid) == StateName.PREPARED, InternalError.HOST_ERROR, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})

				self.root.find("memory").text = str(attrs.get("ram"))
				self.root.find("currentMemory").text = str(attrs.get("ram"))
			if attr == "kblang":
				InternalError.check(self.getState(vmid) == StateName.PREPARED, InternalError.HOST_ERROR, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})

				self.root.find("devices").find("graphics").set("keymap",str(attrs.get("kblang")))
			if attr == "usbtablet":
				InternalError.check(self.getState(vmid) == StateName.PREPARED, InternalError.HOST_ERROR, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})

				usbtablet_exists = False
				usbtablet_entry = None
				for device in self.root.find("devices"):
					if device.get("bus") == "usb" and device.tag == "input":
						usbtablet_exists = True
						usbtablet_entry = device

				print "usbtable exits: " + str(usbtablet_exists)

				if bool(attrs.get("usbtablet")):
					print "setting to True"
					if not usbtablet_exists:
						usbtablet_entry = ET.Element("input", {"bus": "usb", "type": "tablet"})
						usbtablet_entry.append(ET.Element("alias",{"name": "input0"}))
						for element in self.root.getchildren():
							if element.tag == "devices":
								element.append(usbtablet_entry)
				else:
					if usbtablet_exists:
						print "removing usbtablet"
						for element in self.root.getchildren():
							if element.tag == "devices":
								element.remove(usbtablet_entry)
			if attr == "template":
				path = self.imagepath + attrs.get("template")
				self._setImage(vmid, path)


		self.tree.write(config_path)

	def _setImage(self, vmid, img_path):
		InternalError.check(self.getState(vmid) == StateName.STARTED, InternalError.HOST_ERROR, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})

		path = self.imagepath
		path += ("%s.qcow2" % vmid)

		#run(["cp", self.original_image, path])
		run(["cp", img_path, path])

	def random_mac(self):
		mac = [ 0x00, 0x16, 0x3e,
			random.randint(0x00, 0x7f),
			random.randint(0x00, 0xff),
			random.randint(0x00, 0xff) ]
		return ':'.join(map(lambda x: "%02x" % x, mac))

