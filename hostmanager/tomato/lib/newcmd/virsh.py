from util import run, CommandError, cmd, proc
from ..constants import ActionName, StateName, TypeName
from ..error import UserError, InternalError
import time
from util import LockMatrix, params, spawnDaemon, wait, net
import xml.etree.ElementTree as ET
import uuid, random, collections, re
from . import websockify, Error, brctl
from threading import Lock
import os

locks = LockMatrix()

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

class QMError(Error):
	CODE_UNKNOWN="qm.unknown"
	CODE_UNKNOWN_STATUS="qm.unknown_status"
	CODE_INVALID_STATUS="qm.invalid_status"
	CODE_INVALID_PARAMETER="qm.invalid_parameter"
	CODE_PARAMETER_NOT_SET="qm.parameter_not_set"
	CODE_PARAMETER_STILL_SET="qm.parameter_still_set"
	CODE_UNSUPPORTED="qm.unsupported"
	CODE_NOT_INITIALIZED="qm.not_initialized"
	CODE_CONTROL="qm.control_socket"
	CODE_NO_SUCH_NIC="qm.no_such_nic"
	CODE_NIC_ALREADY_EXISTS="qm.nix_already_exists"
	CODE_COMMAND="qm.command"
	CODE_STILL_RUNNING="qm.still_running"

class virsh:

	vm_list = []
	imagepath = ""
	original_image = ""

	TYPE = TypeName.KVM

	HYPERVISOR_MAPPING = {
		"lxc": "LXC://",
		"kvm": "qemu:///session"
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
		self.TYPE = type

		"""
		if self.TYPE == TypeName.KVM:
			#read standard kvm config, extracting path to images
			self.tree = self.writeInitialConfig(self.TYPE, vmid)
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
		"""

	def _virsh(self, cmd_, args=None, timeout=None):
		if not args: args = []
		cmd_ = ["virsh", "-c", self.HYPERVISOR_MAPPING[self.TYPE], cmd_] + args
		if timeout:
			cmd_ = ["perl", "-e", "alarm %d; exec @ARGV" % timeout] + cmd_
		#print "Executing virsh command: %s" % cmd_
		out = cmd.run(cmd_)
		return out

	def _configPath(self, vmid):
		return "/var/lib/vz/images/%d/vm_%d.xml" % (vmid, vmid)

	def _imagePath(self, vmid):
		return "/var/lib/vz/images/%d/disk.qcow2" % vmid

	def _folderPath(self, vmid):
		return "/var/lib/vz/images/%d/" % vmid

	def start(self, vmid, detachInterfaces=True):
		vmid = params.convert(vmid, convert=int, gte=1)
		if not net.bridgeExists("dummy"):
			brctl.create("dummy")
		with locks[vmid]:
			self._checkStatus(vmid,[StateName.PREPARED])
			self._virsh("start", ["vm_%s" % vmid])
			self._checkStatus(vmid,[StateName.STARTED])
			try:
				for ifname in self._getNicNames(vmid).values():
					wait.waitFor(lambda :net.ifaceExists(ifname), failCond=lambda :self.getState(vmid) != StateName.STARTED)
					bridge = net.ifaceBridge(ifname)
					if bridge and detachInterfaces:
						brctl.detach(bridge, ifname)
			except:
				self._virsh("destroy", ["vm_%s" % vmid])
				raise

	def prepare(self,vmid,imagepath,ram=512,cpus=1, vncport=None, vncpassword=None):
		self._checkStatus(vmid,[StateName.CREATED])
		cmd_ = ["virt-install",
				"--connect", self.HYPERVISOR_MAPPING[self.TYPE],
				"--name", "vm_%d" % vmid,
				"--ram",  str(ram),
				"--vcpus", str(cpus),
				#"--os-type", ostype,
				"--disk", "path=%s,device=disk,bus=virtio" % imagepath,
				"--graphics", "vnc%s%s" % (
					(",port=%s" % vncport if vncpassword else ""),
					(",password=%s" % vncpassword if vncpassword else "")),
				"--nonetworks", #Don't create a bridge without my permission
				"--noautoconsole", # Don't enter a console on the device after install
				"--import", #Use the image given to install a guest os
				"--noreboot"] #Don't boot the device after install
		out = cmd.run(cmd_)


	def stop(self, vmid, forced=True):
		self.update_vm_list()
		if forced:
			self._virsh("destroy", ["vm_%s" % vmid])
		else:
			self._virsh("shutdown", ["vm_%s" % vmid])

	def destroy(self, vmid):
		self._checkStatus(vmid, [StateName.PREPARED])
		self._virsh("undefine", ["vm_%s" % vmid])
		run(["rm","-rf", self._folderPath(vmid)])
		self.update_vm_list()

	def _checkState(self, vmid):
		return self._virsh("domstate", ["vm_%s" % vmid])


	def getVMs(self):
		self.update_vm_list()
		return self.vm_list

	def getState(self,vmid):
		self.update_vm_list()
		#InternalError.check(self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does not exist on this host" % vmid, data={"type": self.TYPE})
		if not vmid:
			return StateName.CREATED
		try:
			state = self._checkState(vmid)
		except:
			return StateName.CREATED
		if state.find("shut off") >= 0:
			return StateName.PREPARED
		if state.find("paused") >= 0:
			return StateName.PREPARED
		if state.find("running") >= 0:
			return StateName.STARTED
		#if "error:" in state:
			#InternalError.check(self.vm_list.__contains__(vmid), InternalError.HOST_ERROR,
			#					"VM %s does not exist on this host and cannot be started" % vmid,
			#					data={"type": self.TYPE,"errorMsg": state})
		#else:
			#return StateName.CREATED
		return StateName.CREATED


	def _checkStatus(self,vmid, statuses):
		if not isinstance(statuses, collections.Iterable):
			statuses = [statuses]
		status = self.getState(vmid)
		#TODO: Correct error typing
		InternalError.check(status in statuses, InternalError.INVALID_STATE, "VM is in invalid status",
					  {"vmid": vmid, "status": status, "expected": statuses})

	def getNicList(self, vmid):
		with locks[vmid]:
			self._checkStatus(vmid, [StateName.CREATED,StateName.PREPARED])
			return self._getNicNames(vmid).keys()

	def _getNicNames(self, vmid):
		vmNicList = ET.parse(self._configPath(vmid))
		vmNicList = vmNicList.findall(".//interface")
		vmNicNameList = []
		for iface in vmNicList:
			alias = iface.find("alias").get("name")
			number = re.findall("net(\d+)", alias)[0]
			bridge = iface.find("target").get("dev")
			vmNicNameList.append((number, bridge))

		return dict((int(num), name) for num, name in vmNicNameList)

	def getNicName(self, vmid, num):
		with locks[vmid]:
			self._checkStatus(vmid, [StateName.PREPARED, StateName.STARTED])
			names = self._getNicNames(vmid)
		InternalError.check(num in names, InternalError.INVALID_PARAMETER, "No such nic", {"vmid": vmid, "num": num})

		return names[num]

	def	addNic(self, vmid, num, bridge="dummy", model="e1000", mac=None):
		vmid = params.convert(vmid, convert=int, gte=1)
		num = params.convert(num, convert=int, gte=0, lte=31)
		bridge = params.convert(bridge, convert=str)
		model = params.convert(model, convert=str, oneOf=["e1000", "i82551", "rtl8139"])
		mac = params.convert(mac, convert=str, regExp="^([0-9A-F]{2}[:-]){5}([0-9A-F]{2})$", null=True)
		with locks[vmid]:
			self._checkStatus(vmid, [StateName.CREATED, StateName.PREPARED])
			if num in self.getNicList(vmid):
				raise InternalError(InternalError.INVALID_PARAMETER, "Nic already exists", {"vmid": vmid, "num": num})
				#raise QMError(QMError.CODE_NIC_ALREADY_EXISTS, "Nic already exists", {"vmid": vmid, "num": num})

			tree = ET.parse(self._configPath(vmid))
			root = tree.getroot()

			elementInterface = ET.Element("interface", {"type": "bridge"})

			if mac:
				elementMac = ET.Element("mac", {"address": "%s" % mac})
				elementInterface.append(elementMac)
			elementSource = ET.Element("source", {"bridge": bridge})
			elementAlias = ET.Element("alias", {"name": "net%d" % num})
			elementTarget = ET.Element("target", {"dev": "tap%di%d" % (vmid, num)})
			elementModel = ET.Element("model", {"type": "%s" % model})

			"""
			elementInterface = ET.Element("network")

			if mac:
				elementMac = ET.Element("mac", {"address": "%s" % mac})
				elementInterface.append(elementMac)
			elementSource = ET.Element("bridge", {"name": bridge})
			elementAlias = ET.Element("name")
			elementAlias.set("name","net%d" % num)
			elementModel = ET.Element("model", {"type": "%s" % model})
"""
			elementInterface.append(elementSource)
			elementInterface.append(elementTarget)
			elementInterface.append(elementAlias)
			elementInterface.append(elementModel)


			for element in root.getchildren():
				if element.tag == "devices":
					element.append(elementInterface)

			if not os.path.exists(os.path.dirname(self._configPath(vmid))):
				os.makedirs(os.path.dirname(self._configPath(vmid)))

			tree.write(self._configPath(vmid))
			self._virsh("define", [self._configPath(vmid)])


	def delNic(self, vmid, num):
		with locks[vmid]:
			self._checkStatus(vmid, [StateName.CREATED, StateName.PREPARED])
			if not num in self.getNicList(vmid):
				raise InternalError(InternalError.INVALID_PARAMETER, "No such nic", {"vmid": vmid, "num": num})
			mac = ET.fromstring(self._virsh(vmid, "dumpxml")).find("interface/alias[@name='net%d']/../mac" % num).get("address")

			print ET.tostring(mac)

			self._virsh("detach-interface",
						["--domain vm_%d" % vmid,
						 "--type bridge",
						 ("--mac %s" % ET.tostring(mac)) if mac else "",
						 "--config"])

	def update_vm_list(self):
		#go through currently listed vms and add them to vm_list
		self.vm_list = []
		list_raw = self._virsh("list",["--all"])
		list_split = list_raw.split("vm_")[1:]
		list_vm_ids = []
		for item in list_split:
			list_vm_ids.append(item.split(" ")[0])
		for id in list_vm_ids:
			self.vm_list.append(int(id))

	def startVnc(self, vmid,vncpassword, vncport, websockifyPort=None, websockifyCert=None):
		vmid = params.convert(vmid, convert=int, gte=1)
		vncpassword = params.convert(vncpassword, convert=unicode)
		vncport = params.convert(vncport, convert=int, gte=1, lt=2 ** 16)
		with locks[vmid]:
			self._checkStatus(vmid, StateName.STARTED)
			self._setVncPassword(vmid, vncpassword)
			self._virsh("qemu-monitor-command", ["vm_%d" % vmid, "--hmp", "change", "vnc", "unix:/var/run/qemu-server/%d.vnc,password" % vmid])
			vncPid = spawnDaemon(
				["socat", "TCP-LISTEN:%d,reuseaddr,fork" % vncport, "UNIX-CLIENT:/var/run/qemu-server/%d.vnc" % vmid])
			websockifyPid = None
			try:
				if websockifyPort:
					websockifyPid = websockify.start(websockifyPort, vncport, websockifyCert)
			except:
				self.stopVnc(vncPid)
				raise
			return vncPid, websockifyPid

	def stopVnc(self, pid, websockifyPid=None):
			proc.autoKill(pid, group=True)
			#QMError.check(not proc.isAlive(pid), QMError.CODE_STILL_RUNNING, "Failed to stop socat")
			if websockifyPid:
				websockify.stop(websockifyPid)

	def _setVncPassword(self, vmid, vncpassword):
		self.setAttributes(vmid, vncpassword=vncpassword)

	def	getStatistics(self, vmid):
		with locks[vmid]:
			self._checkStatus(vmid, StateName.STARTED)
			pid = self._getPid(vmid)
			return proc.getStatistics(pid)

	def _getPid(self, vmid):
		try:
			with open("/var/run/libvirt/qemu/vm_%d.pid" % vmid) as fp:
				pid = int(fp.readline().strip())
			return pid
		except IOError:
			raise InternalError(InternalError.INVALID_STATE, "Pid file does not exist", {"vmid": vmid})

	def setAttributes(self, vmid, cores=None, memory=None, keyboard=None, tablet=None,
			hda=None, fda=None, hdb=None, vncpassword=None, vncport=None):
		self.update_vm_list()
		InternalError.check(self.vm_list.__contains__(vmid), InternalError.HOST_ERROR, "VM %s does not exist on this host" % vmid, data={"type": self.TYPE})

		#reading xml file of vm:
		self.tree = ET.parse(self._configPath(vmid))
		self.root = self.tree.getroot()

		if hda:
			if type == TypeName.KVM:
				self.root.find("./devices/disk/target[@dev='vda']/../source").set("file",hda)
			if type == TypeName.LXC:
				self.root.find("./devices/filesystem/target[@dir='/']/../source").set("dir",hda)
		#if fda:
		#if hdb:


		if cores:
			InternalError.check(self.getState(vmid) == StateName.PREPARED, InternalError.HOST_ERROR, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})

			self.root.find("vcpu").text = str(cores)
		if memory:
			InternalError.check(self.getState(vmid) == StateName.PREPARED, InternalError.HOST_ERROR, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})

			self.root.find("memory").text = str(memory)
			self.root.find("currentMemory").text = str(memory)

		if keyboard:
			InternalError.check(self.getState(vmid) == StateName.PREPARED, InternalError.HOST_ERROR, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})
			self.root.find("devices").find("graphics").set("keymap",str(keyboard))

		if vncpassword:
			self.root.find("devices").find("graphics").set("passwd", vncpassword)
		if vncport:
			self.root.find("devices").find("graphics").set("port", vncport)

		if tablet:
			InternalError.check(self.getState(vmid) == StateName.PREPARED, InternalError.HOST_ERROR, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})

			usbtablet_exists = False
			usbtablet_entry = None
			for device in self.root.find("devices"):
				if device.get("bus") == "usb" and device.tag == "input":
					usbtablet_exists = True
					usbtablet_entry = device


			if bool(tablet):
				if not usbtablet_exists:
					usbtablet_entry = ET.Element("input", {"bus": "usb", "type": "tablet"})
					usbtablet_entry.append(ET.Element("alias",{"name": "input0"}))
					for element in self.root.getchildren():
						if element.tag == "devices":
							element.append(usbtablet_entry)
			else:
				if usbtablet_exists:
					for element in self.root.getchildren():
						if element.tag == "devices":
							element.remove(usbtablet_entry)
		self.tree.write(self._configPath(vmid))
		self._virsh("define", [self._configPath(vmid)])

	def random_mac(self):
		mac = [ 0x00, 0x16, 0x3e,
			random.randint(0x00, 0x7f),
			random.randint(0x00, 0xff),
			random.randint(0x00, 0xff) ]
		return ':'.join(map(lambda x: "%02x" % x, mac))



	def writeInitialConfig(self, type, vmid):

		config_path = self._configPath(vmid)
		if not os.path.exists(os.path.dirname(config_path)):
			os.makedirs(os.path.dirname(config_path))

		configeXML=ET.fromstring(self._virsh("dumpxml", ["vm_%s" % vmid, "--security-info"]))

		tree = ET.ElementTree(configeXML)
		tree.write(config_path)

		return tree

		"""
		initNode = ET.fromstring("<domain></domain>")
		initNode.set("id", "%s" % vmid)

		if type == TypeName.KVM:
			initNode.set("type", "kvm")
		if type == TypeName.LXC:
			initNode.set("type", "lxc")

		elementName = ET.Element("name")
		elementName.text = "vm_%s" % vmid
		initNode.append(elementName)

		vm_uuid = uuid.uuid4()
		elementUUID = ET.Element("uuid")
		elementUUID.text = str(vm_uuid)
		initNode.append(elementUUID)

		elementMemory = ET.Element("memory", {"unit": "MiB"})
		elementMemory.text = "1048576"
		initNode.append(elementMemory)

		elementCurrentMemory = ET.Element("currentMemory", {"unit": "MiB"})
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
			elementType =ET.Element("type", {"arch": "x86_64", "machine": "pc-i440fx-2.2"})
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
			elementEmulator.text = "/usr/bin/kvm"
		if type == TypeName.LXC:
			elementEmulator.text = "/usr/lib/libvirt/libvirt_lxc"
		elementDevices.append(elementEmulator)

		if type == TypeName.KVM:
			elementDisk = ET.Element("disk", {"device": "disk", "type": "file"})
			elementDriver = ET.Element("driver", {"name": "qemu", "type": "qcow2"})
			elementDisk.append(elementDriver)
			elementSource = ET.Element("source",{"file": ("%s" % self._imagePath(vmid))})
			elementDisk.append(elementSource)
			elementTarget = ET.Element("target", {"bus": "virtio", "dev": "vda"})
			elementDisk.append(elementTarget)
			elementAlias = ET.Element("alias", {"name": "virtio-disk0"})
			elementDisk.append(elementAlias)
			#elementAddress = ET.Element("address", {"bus": "0x00", "domain": "0x0000", "function": "0x0", "slot": "0x05", "type": "pci"})
			#elementDisk.append(elementAddress)
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

			#elementInput3 = ET.Element("input", {"bus": "ps2", "type": "keyboard"})
			#elementDevices.append(elementInput3)

			elementGraphics = ET.Element("graphics", {"listen": "127.0.0.1", "port": "5900", "type": "vnc"})
			elementDevices.append(elementGraphics)


			elementVideo = ET.Element("video")
			elementModel = ET.Element("model", {"heads": "1", "type": "cirrus", "vram": "9216"})
			elementVideo.append(elementModel)
			elementVideoAlias = ET.Element("alias", {"name": "video0"})
			elementVideo.append(elementVideoAlias)
			elementVideoAddress = ET.Element("address", {"bus": "0x00", "domain": "0x0000", "function": "0x0", "slot": "0x02", "type": "pci"})
			elementVideo.append(elementVideoAddress)
			elementDevices.append(elementVideo)

		#	elementMemBalloon = ET.Element("memballoon", {"model": "virtio"})
		#	elementMemBalloonAlias = ET.Element("alias", {"name": "balloon0"})
		#	elementMemBalloon.append(elementMemBalloonAlias)
		#	elementMemballoonAddress = ET.Element("address", {"bus": "0x00", "domain": "0x0000", "function": "0x0", "slot": "0x06", "type": "pci"})
		#	elementMemBalloon.append(elementMemballoonAddress)
		#	elementDevices.append(elementMemBalloon)

		initNode.append(elementDevices)

		elementSecLabel = ET.Element("seclabel", {"model": "apparmor", "relabel": "yes", "type": "dynamic"})
		elementLabel = ET.Element("label")
		elementLabel.text = ("libvirt-%s" % vm_uuid)
		elementSecLabel.append(elementLabel)
		elementImageLabel = ET.Element("imagelabel")
		elementImageLabel.text = ("libvirt-%s" % vm_uuid)
		elementSecLabel.append(elementImageLabel)
		initNode.append(elementSecLabel)

		config_path = self._configPath(vmid)
		if not os.path.exists(os.path.dirname(config_path)):
			os.makedirs(os.path.dirname(config_path))

		tree = ET.ElementTree(initNode)
		tree.write(config_path)

		return tree
		"""