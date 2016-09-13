from util import run, CommandError, cmd
from ..constants import ActionName, StateName, TypeName
from ..error import UserError, InternalError
import time
import xml.etree.ElementTree as ET
import uuid, random
from .. import decorators
from threading import Lock

class IDManager(object):

	__slots__ = ("minid", "maxid", "idpoint", "lock")

	def __init__(self):
		self.minid = 1000
		self.maxid = 9999
		self.idpoint = self.maxid
		self.lock = Lock()

	def _move_right(self):
		self.idpoint+=1
		if self.idpoint > self.maxid:
			self.idpoint = self.minid

	def _check_free(self, id_):
		raise NotImplementedError()

	def getFreeID(self):
		with self.lock:
			self._move_right()
			while not self._check_free(self.idpoint):
				self._move_right()
			return self.idpoint

idmanager = IDManager()

class virsh:

	vm_list = []
	kvm_config_path = "/home/stephan/ToMaTo/hostmanager/tomato/lib/standard_kvm_config.xml" #standard_kvm_config.xml"
	lxc_config_path = "/home/stephan/ToMaTo/hostmanager/tomato/lib/standard_lxc_config.xml" #standard_lxc_config.xml"
	imagepath = ""
	original_image = ""

	TYPE = TypeName.KVM

	HYPERVISOR_MAPPING = {
		"lxc": "LXC://",
		"kvm": "qemu:///system"
	}

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
		print "init"
		self.TYPE = type
		if self.TYPE == TypeName.KVM:
			#read standard kvm config, extracting path to images
			self.tree = self.writeInitialConfig(self.TYPE, 1337)
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

		if self.TYPE == TypeName.LXC:
			#read standard kvm config, extracting path to images
			self.tree = self.writeInitialConfig(self.TYPE, 1337)
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


	def _virsh(self, cmd_, args=None, timeout=None):
		if not args: args = []
		cmd_ = ["virsh", "-c", self.HYPERVISOR_MAPPING[self.TYPE], cmd_] + args
		if timeout:
			cmd_ = ["perl", "-e", "alarm %d; exec @ARGV" % timeout] + cmd_
		out = cmd.run(cmd_)
		return out

	def vm_start(self, vmid, params=None):
		#check if vmid is already in list:
		self.update_vm_list()
		if self.vm_list.__contains__(vmid):
			self._virsh("start", ["vm_%s" % vmid])
		else:
			InternalError.check(self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does not exist on this host and cannot be started" % vmid, data={"type": self.TYPE})

	def vm_prepare(self, vmid, type=TypeName.KVM, template=None):
		self.update_vm_list()
		InternalError.check(not self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does already exist on this host" % vmid, data={"type": self.TYPE})
		#read standard config:
		self.tree = self.writeInitialConfig(type, vmid)
		#self.tree = ET.parse(self.lxc_config_path)
		self.root = self.tree.getroot()

		#copy template
		path = self.imagepath
		path += ("%s.qcow2" % vmid)

		if template == None:
			self._setImage(vmid, self.original_image)
		else:
			pathToImage = self.imagepath + template
			self._setImage(vmid, pathToImage)

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
		self._virsh("define", ["%s" % config_path])
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
		#InternalError.check(self.getState(vmid) == StateName.STARTED, InternalError.HOST_ERROR, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})

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

	def writeInitialConfig(self, type, vmid):
		initNode = ET.fromstring("<domain></domain>")
		initNode.set("id", "%s" % vmid)
		if type == TypeName.KVM:
			initNode.set("type", "kvm")
		if type == TypeName.LXC:
			initNode.set("type", "lxc")

		elementName = ET.Element("name")
		elementName.text = "vm_%s" % vmid
		initNode.append(elementName)

		elementUUID = ET.Element("uuid")
		elementUUID.text = "1b565254-c508-eabf-ce0e-2ba22f4d6e40"
		initNode.append(elementUUID)

		elementMemory = ET.Element("memory", {"unit": "KiB"})
		elementMemory.text = "1048576"
		initNode.append(elementMemory)

		elementCurrentMemory = ET.Element("currentMemory", {"unit": "KiB"})
		elementCurrentMemory.text = "1048576"
		initNode.append(elementCurrentMemory)

		elementVCPU = ET.Element("vcpu", {"placement": "static"})
		elementVCPU.text = "1"
		initNode.append(elementVCPU)

		elementResource = ET.Element("resource")
		elementPartition = ET.Element("partition")
		elementPartition.text = "/machine"
		elementResource.append(elementPartition)
		initNode.append(elementResource)

		elementOS = ET.Element("os")
		if type == TypeName.KVM:
			elementType =ET.Element("type", {"arch": "x86_64", "machine": "pc-i440fx-trusty"})
			elementType.text = "hvm"
			elementOS.append(elementType)
			elementBoot = ET.Element("boot", {"dev": "hd"})
			elementOS.append(elementBoot)
		if type == TypeName.LXC:
			elementType =ET.Element("type", {"arch": "x86_64"})
			elementType.text = "exe"
			elementOS.append(elementType)
			elementInit = ET.Element("init")
			elementInit.text = "/sbin/init"
			elementOS.append(elementInit)

		initNode.append(elementOS)

		if type == TypeName.KVM:
			elementFeatures = ET.Element("features")
			elementACPI = ET.Element("acpi")
			elementFeatures.append(elementACPI)
			elementAPIC = ET.Element("apic")
			elementFeatures.append(elementAPIC)
			elementPAE = ET.Element("pae")
			elementFeatures.append(elementPAE)
			initNode.append(elementFeatures)

		elementClock = ET.Element("clock", {"offset": "utc"})
		initNode.append(elementClock)

		elementONPOWEROFF = ET.Element("on_poweroff")
		elementONPOWEROFF.text = "destroy"
		initNode.append(elementONPOWEROFF)

		elementOnReboot = ET.Element("on_reboot")
		elementOnReboot.text = "restart"
		initNode.append(elementOnReboot)

		elementOnCrash = ET.Element("on_crash")
		elementOnCrash.text = "restart"
		if type == TypeName.LXC:
			elementOnCrash.text = "destroy"
		initNode.append(elementOnCrash)

		elementDevices = ET.Element("devices")

		elementEmulator = ET.Element("emulator")
		if type == TypeName.KVM:
			elementEmulator.text = "/usr/bin/kvm-spice"
		if type == TypeName.LXC:
			elementEmulator.text = "/usr/lib/libvirt/libvirt_lxc"
		elementDevices.append(elementEmulator)

		if type == TypeName.KVM:
			elementDisk = ET.Element("disk", {"device": "disk", "type": "file"})
			elementDriver = ET.Element("driver", {"name": "qemu", "type": "qcow2"})
			elementDisk.append(elementDriver)
			elementSource = ET.Element("source",{"file": "/home/stephan/work/kvm_test/bob_image.qcow2"})
			elementDisk.append(elementSource)
			elementOriginal = ET.Element("original", {"file": "/home/stephan/work/kvm_test/initial_image.qcow2"})
			elementDisk.append(elementOriginal)
			elementTarget = ET.Element("target", {"bus": "virtio", "dev": "vda"})
			elementDisk.append(elementTarget)
			elementAlias = ET.Element("alias", {"name": "virtio-disk0"})
			elementDisk.append(elementAlias)
			elementAddress = ET.Element("address", {"bus": "0x00", "domain": "0x0000", "function": "0x0", "slot": "0x05", "type": "pci"})
			elementDisk.append(elementAddress)
			elementDevices.append(elementDisk)
		if type == TypeName.LXC:
			elementFileSystem = ET.Element("filesystem", {"type": "mount", "accessmode": "passthrough"})
			elementFSSource = ET.Element("source", {"dir": "/var/lib/lxc/vm_%s/rootfs" % vmid})
			elementFileSystem.append(elementFSSource)
			elementFSTarget = ET.Element("target", {"dir": "/"})
			elementFileSystem.append(elementFSTarget)
			elementDevices.append(elementFileSystem)

		if type == TypeName.KVM:
			elementController2 = ET.Element("controller", {"index": "0", "type": "usb"})
			elementControllerAlias2 = ET.Element("alias", {"name": "usb0"})
			elementController2.append(elementControllerAlias2)
			elementControllerAddress = ET.Element("address", {"bus": "0x00", "domain": "0x0000", "function": "0x2", "slot": "0x01", "type": "pci"})
			elementController2.append(elementControllerAddress)
			elementDevices.append(elementController2)

			elementController = ET.Element("controller", {"index": "0", "model": "pci-root", "type": "pci"})
			elementControllerAlias = ET.Element("alias", {"name": "pci.0"})
			elementController.append(elementControllerAlias)
			elementDevices.append(elementController)

		if type == TypeName.KVM:
			elementInterface = ET.Element("interface", {"type": "bridge"})
			elementInterfaceSource = ET.Element("source", {"bridge": "br0"})
			elementInterface.append(elementInterfaceSource)
			elementMac = ET.Element("mac", {"address": "52:54:00:bb:d5:2b" })
			elementInterface.append(elementMac)
			elementDevices.append(elementInterface)
		if type == TypeName.LXC:
			elementInterface = ET.Element("interface", {"type": "network"})
			elementInterfaceTarget = ET.Element("target", {"dev": "vnet0"})
			elementInterface.append(elementInterfaceTarget)
			elementInterfaceSource = ET.Element("source", {"network": "default", "bridge": "virbr0"})
			elementInterface.append(elementInterfaceSource)
			elementMac = ET.Element("mac", {"address": "52:54:00:bb:d5:2b" })
			elementInterface.append(elementMac)
			elementGuest = ET.Element("guest", {"dev": "eth0"})
			elementInterface.append(elementGuest)
			elementDevices.append(elementInterface)

		if type == TypeName.KVM:
			elementSerial = ET.Element("serial", {"type": "pty"})
			elementSerialSource = ET.Element("source", {"path": "/dev/pts/6"})
			elementSerial.append(elementSerialSource)
			elementSerialTarget = ET.Element("target", {"port": "0"})
			elementSerial.append(elementSerialTarget)
			elementSerialAlias = ET.Element("alias", {"name": "serial0"})
			elementSerial.append(elementSerialAlias)
			elementDevices.append(elementSerial)

		if type == TypeName.KVM:
			elementConsole = ET.Element("console", {"tty": "/dev/pts/6", "type": "pty"})
			elementConsoleSource = ET.Element("source", {"path": "/dev/pts/6"})
			elementConsole.append(elementConsoleSource)
			elementConsoleTarget = ET.Element("target", {"port": "0", "type": "serial"})
			elementConsole.append(elementConsoleTarget)
			elementConsoleAlias = ET.Element("alias", {"name": "serial0"})
			elementConsole.append(elementConsoleAlias)
			elementDevices.append(elementConsole)
		if type == TypeName.LXC:
			elementConsole = ET.Element("console", {"tty": "/dev/pts/22", "type": "pty"})
			elementConsoleSource = ET.Element("source", {"path": "/dev/pts/22"})
			elementConsole.append(elementConsoleSource)
			elementConsoleTarget = ET.Element("target", {"port": "0", "type": "lxc"})
			elementConsole.append(elementConsoleTarget)
			elementConsoleAlias = ET.Element("alias", {"name": "console0"})
			elementConsole.append(elementConsoleAlias)
			elementDevices.append(elementConsole)

		if type == TypeName.KVM:
			elementInput = ET.Element("input", {"bus": "usb", "type": "tablet"})
			elementInputAlias = ET.Element("alias", {"name": "input0"})
			elementInput.append(elementInputAlias)
			elementDevices.append(elementInput)

			elementInput2 = ET.Element("input", {"bus": "ps2", "type": "mouse"})
			elementDevices.append(elementInput2)

			elementInput3 = ET.Element("input", {"bus": "ps2", "type": "keyboard"})
			elementDevices.append(elementInput3)

			elementGraphics = ET.Element("graphics", {"autoport": "yes", "listen": "127.0.0.1", "port": "5900", "type": "vnc"})
			elementListen = ET.Element("listen", {"address": "127.0.0.1", "type": "address"})
			elementGraphics.append(elementListen)
			elementDevices.append(elementGraphics)

			elementSound = ET.Element("sound", {"model": "ich6"})
			elementSoundAlias = ET.Element("alias", {"name": "sound0"})
			elementSound.append(elementSoundAlias)
			elementSoundAddress = ET.Element("address", {"bus": "0x00", "domain": "0x0000", "function": "0x0", "slot": "0x04", "type": "pci"})
			elementSound.append(elementSoundAddress)
			elementDevices.append(elementSound)

			elementVideo = ET.Element("video")
			elementModel = ET.Element("model", {"heads": "1", "type": "cirrus", "vram": "9216"})
			elementVideo.append(elementModel)
			elementVideoAlias = ET.Element("alias", {"name": "video0"})
			elementVideo.append(elementVideoAlias)
			elementVideoAddress = ET.Element("address", {"bus": "0x00", "domain": "0x0000", "function": "0x0", "slot": "0x02", "type": "pci"})
			elementVideo.append(elementVideoAddress)
			elementDevices.append(elementVideo)

			elementMemBalloon = ET.Element("memballoon", {"model": "virtio"})
			elementMemBalloonAlias = ET.Element("alias", {"name": "balloon0"})
			elementMemBalloon.append(elementMemBalloonAlias)
			elementMemballoonAddress = ET.Element("address", {"bus": "0x00", "domain": "0x0000", "function": "0x0", "slot": "0x06", "type": "pci"})
			elementMemBalloon.append(elementMemballoonAddress)
			elementDevices.append(elementMemBalloon)

		initNode.append(elementDevices)

		elementSecLabel = ET.Element("seclabel", {"model": "apparmor", "relabel": "yes", "type": "dynamic"})
		elementLabel = ET.Element("label")
		elementLabel.text = "libvirt-1b565254-c508-eabf-ce0e-2ba22f4d6e40"
		elementSecLabel.append(elementLabel)
		elementImageLabel = ET.Element("imagelabel")
		elementImageLabel.text = "libvirt-1b565254-c508-eabf-ce0e-2ba22f4d6e40"
		elementSecLabel.append(elementImageLabel)
		initNode.append(elementSecLabel)

		print "Writing test.xml"

		config_path = self.imagepath
		config_path += ("%test.xml")
		tree = ET.ElementTree(initNode)
		tree.write(config_path)

		return tree
