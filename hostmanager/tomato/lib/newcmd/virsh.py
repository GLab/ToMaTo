from util import run, CommandError, cmd, proc
from ..constants import ActionName, StateName, TechName
from ..error import UserError, InternalError
import time
from util import LockMatrix, params, spawnDaemon, wait, net
import xml.etree.ElementTree as ET
import uuid, random, collections, re
from . import websockify, Error, brctl
from threading import Lock
import os

locks = LockMatrix()

DOC="""
Element type: ``virsh``

Description:
	This element type provides access to different virtualization technologies
	by using virsh as interface. The element should be instantiated to define
	the technologie which should be accessed. ``Virsh`` is part of the libvirt package.


Possible parents: None
"""

class VirshError(Error):
	CODE_UNKNOWN="virsh.unknown"
	CODE_UNKNOWN_STATUS="virsh.unknown_status"
	CODE_INVALID_STATUS="virsh.invalid_status"
	CODE_INVALID_PARAMETER="virsh.invalid_parameter"
	CODE_PARAMETER_NOT_SET="virsh.parameter_not_set"
	CODE_PARAMETER_STILL_SET="virsh.parameter_still_set"
	CODE_UNSUPPORTED="virsh.unsupported"
	CODE_NOT_INITIALIZED="virsh.not_initialized"
	CODE_CONTROL="virsh.control_socket"
	CODE_NO_SUCH_NIC="virsh.no_such_nic"
	CODE_NIC_ALREADY_EXISTS="virsh.nix_already_exists"
	CODE_COMMAND="virsh.command"
	CODE_STILL_RUNNING="virsh.still_running"

class virsh:

	vm_list = []
	imagepath = ""
	original_image = ""

	TYPE = TechName.KVM

	HYPERVISOR_MAPPING = {
		TechName.LXC: "LXC://",
		TechName.KVM: "qemu:///session"
	}
	DRIVER_MAPPING = {
		TechName.KVMQM: "qcow2",
		TechName.KVM: "qcow2",
		TechName.LXC: "raw",
		TechName.OPENVZ: "raw",
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

	def _virsh(self, cmd_, args=None, timeout=None):
		if not args: args = []
		cmd_ = ["virsh", "-c", self.HYPERVISOR_MAPPING[self.TYPE], cmd_] + args
		if timeout:
			cmd_ = ["perl", "-e", "alarm %d; exec @ARGV" % timeout] + cmd_
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

	def prepare(self, vmid, imagepath, nlxtp_floppy_filename=None, nlxtp_device_filename=None,ram=512,cpus=1, vncport=None, vncpassword=None,keyboard="en-us"):
		self._checkStatus(vmid,[StateName.CREATED])
		driver_type = self.DRIVER_MAPPING[self.TYPE]
		cmd_ = ["virt-install",
				"--connect", self.HYPERVISOR_MAPPING[self.TYPE],
				"--name", "vm_%d" % vmid,
				"--ram",  str(ram),
				"--vcpus", str(cpus),
				#"--os-type", ostype,
				"--import", #Use the image given to install a guest os
				"--disk", "path=%s,driver_type=%s" % (imagepath, driver_type), # VDA ,device=disk,driver_type=%s,bus=virtio, % driver_type
				("--disk" if nlxtp_device_filename else ""),("path=%s" % nlxtp_device_filename #,device=disk,bus=virtio
															 if nlxtp_device_filename else ""), # Virtual 'big' device for nlxtp
				("--disk" if nlxtp_floppy_filename else ""), # Floppy device for nlXTP
				("path=%s,device=floppy,cache=writethrough" % nlxtp_floppy_filename if nlxtp_floppy_filename else ""),
				"--graphics", "vnc%s%s,keymap=%s" % (
					(",port=%s" % vncport if vncpassword else ""),
					(",password=%s" % vncpassword if vncpassword else ""),
					keyboard),
				"--nonetworks", #Don't create automatically a bridge
				"--noautoconsole", # Don't enter a console on the device after install
				"--noreboot"] #Don't boot the device after install
		cmd.run(cmd_)
		self.writeInitialConfig(self.TYPE, vmid)


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

		return StateName.CREATED


	def _checkStatus(self,vmid, statuses):
		if not isinstance(statuses, collections.Iterable):
			statuses = [statuses]
		status = self.getState(vmid)
		VirshError.check(status in statuses, VirshError.CODE_INVALID_STATUS, "VM is in invalid status", {"vmid: ": vmid, "status: ": status, "allowed: ": statuses})

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
			interfacename = iface.find("target").get("dev")
			vmNicNameList.append((number, interfacename))

		return dict((int(num), name) for num, name in vmNicNameList)

	def getNicName(self, vmid, num):
		with locks[vmid]:
			self._checkStatus(vmid, [StateName.PREPARED, StateName.STARTED])
			names = self._getNicNames(vmid)
		VirshError.check(num in names, VirshError.CODE_NO_SUCH_NIC, "No such nic exists", {"vmid: ": vmid, "num: ": num})

		return names[num]

	def	addNic(self, vmid, num, bridge="dummy", model="e1000", mac=None):
		vmid = params.convert(vmid, convert=int, gte=1)
		num = params.convert(num, convert=int, gte=0, lte=31)
		bridge = params.convert(bridge, convert=str)
		model = params.convert(model, convert=str, oneOf=["e1000", "i82551", "rtl8139"])
		mac = params.convert(mac, convert=str, regExp="^([0-9A-F]{2}[:-]){5}([0-9A-F]{2})$", null=True)
		with locks[vmid]:
			self._checkStatus(vmid, [StateName.CREATED, StateName.PREPARED])
			VirshError.check(num not in self.getNicList(vmid), VirshError.CODE_NIC_ALREADY_EXISTS, "Nic already exists", {"vmid: ": vmid, "num: ": num})
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
			VirshError.check(num in self.getNicList(vmid), VirshError.CODE_NO_SUCH_NIC, "No such nic exists", {"vmid: ": vmid, "num: ": num})
			mac = ET.fromstring(self._virsh(vmid, "dumpxml")).find("interface/alias[@name='net%d']/../mac" % num).get("address")

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
			VirshError.check(not proc.isAlive(pid), VirshError.CODE_STILL_RUNNING, "Failed to stop socat")
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
			raise VirshError(VirshError.INVALID_STATE, "Pid file does not exist", {"vmid": vmid})

	def setAttributes(self, vmid, cores=None, memory=None, keyboard=None, tablet=None,
			hda=None, fda=None, hdb=None, vncpassword=None, vncport=None):
		self.update_vm_list()
		VirshError.check(self.vm_list.__contains__(vmid), VirshError.CODE_INVALID_PARAMETER, "VM %s does not exist on this host" % vmid, data={"type": self.TYPE})

		#reading xml file of vm:
		self.tree = ET.parse(self._configPath(vmid))
		self.root = self.tree.getroot()

		if hda:
			if type == TechName.KVM:
				self.root.find("./devices/disk/target[@dev='vda']/../source").set("file",hda)
			if type == TechName.LXC:
				self.root.find("./devices/filesystem/target[@dir='/']/../source").set("dir",hda)
		#if fda:
		#if hdb:


		if cores:
			VirshError.check(self.getState(vmid) == StateName.PREPARED, VirshError.CODE_INVALID_STATUS, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})
			self.root.find("vcpu").text = str(cores)
		if memory:
			VirshError.check(self.getState(vmid) == StateName.PREPARED, VirshError.CODE_INVALID_STATUS, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})
			self.root.find("memory").text = str(memory)
			self.root.find("currentMemory").text = str(memory)
		if keyboard:
			VirshError.check(self.getState(vmid) == StateName.PREPARED, VirshError.CODE_INVALID_STATUS, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})
			self.root.find("devices").find("graphics").set("keymap",str(keyboard))

		if vncpassword:
			self.root.find("devices").find("graphics").set("passwd", vncpassword)
		if vncport:
			self.root.find("devices").find("graphics").set("port", vncport)

		if tablet:
			VirshError.check(self.getState(vmid) == StateName.PREPARED, VirshError.CODE_INVALID_STATUS, "VM %s is in an invalid state" % vmid, data={"type": self.TYPE})

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

		configXML=ET.fromstring(self._virsh("dumpxml", ["vm_%s" % vmid, "--security-info"]))

		tree = ET.ElementTree(configXML)
		tree.write(config_path)

		return tree