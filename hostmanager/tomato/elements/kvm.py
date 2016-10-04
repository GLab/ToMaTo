from ..lib.constants import ActionName, StateName, TypeName
from django.db import models #@UnresolvedImport
from ..resources import template
from .. import connections, elements, resources, config
from ..lib.attributes import Attr #@UnresolvedImport
from ..lib import cmd #@UnresolvedImport
from ..lib.newcmd import virsh, qemu_img, ipspy
from ..lib.newcmd.util import io, net
from ..lib.error import UserError, InternalError


import time
import xml.etree.ElementTree as ET
import random, os, sys, re

kblang_options = {"en-us": "English (US)",
					"en-gb": "English (GB)",
					"de": "German",
					"fr": "French",
					"ja": "Japanese"
					}


class KVM(elements.Element):
	vmid_attr = Attr("vmid", type="int")
	vmid = vmid_attr.attribute()
	websocket_port_attr = Attr("websocket_port", type="int")
	websocket_port = websocket_port_attr.attribute()
	websocket_pid_attr = Attr("websocket_pid", type="int")
	websocket_pid = websocket_pid_attr.attribute()
	vncport_attr = Attr("vncport", type="int")
	vncport = vncport_attr.attribute()
	vncpid_attr = Attr("vncpid", type="int")
	vncpid = vncpid_attr.attribute()
	vncpassword_attr = Attr("vncpassword", type="str")
	vncpassword = vncpassword_attr.attribute()
	cpus_attr = Attr("cpus", desc="Number of CPUs", states=[StateName.CREATED, StateName.PREPARED], type="int", minValue=1, maxValue=4, default=1)
	cpus = cpus_attr.attribute()
	ram_attr = Attr("ram", desc="RAM", unit="MB", states=[StateName.CREATED, StateName.PREPARED], type="int", minValue=64, maxValue=8192, default=256)
	ram = ram_attr.attribute()
	kblang_attr = Attr("kblang", desc="Keyboard language", states=[StateName.CREATED, StateName.PREPARED], type="str", options=kblang_options, default=None, null=True)
	#["pt", "tr", "ja", "es", "no", "is", "fr-ca", "fr", "pt-br", "da", "fr-ch", "sl", "de-ch", "en-gb", "it", "en-us", "fr-be", "hu", "pl", "nl", "mk", "fi", "lt", "sv", "de"]
	kblang = kblang_attr.attribute()
	usbtablet_attr = Attr("usbtablet", desc="USB tablet mouse mode", states=[StateName.CREATED, StateName.PREPARED], type="bool", default=True)
	usbtablet = usbtablet_attr.attribute()
	template_attr = Attr("template", desc="Template", states=[StateName.CREATED, StateName.PREPARED], type="str", null=True)
	template = models.ForeignKey(template.Template, null=True)

	#vmid = "bob"
	state = StateName.CREATED
	tree = None
	imagepath = ""
	original_image = ""
	vir = virsh.virsh(TypeName.KVM)
	cpu = 1
	ram = 1048576
	kblang = "en-us"
	usbtablet = True

	TYPE = TypeName.KVM
	CAP_ACTIONS = {
		ActionName.PREPARE: [StateName.CREATED],
		ActionName.DESTROY: [StateName.PREPARED],
		ActionName.START: [StateName.PREPARED],
		ActionName.STOP: [StateName.STARTED],
		ActionName.UPLOAD_GRANT: [StateName.PREPARED],
		ActionName.REXTFV_UPLOAD_GRANT: [StateName.PREPARED],
		ActionName.UPLOAD_USE: [StateName.PREPARED],
		ActionName.REXTFV_UPLOAD_USE: [StateName.PREPARED],
		"download_grant": [StateName.PREPARED],
		"rextfv_download_grant": [StateName.PREPARED, StateName.STARTED],
		elements.REMOVE_ACTION: [StateName.CREATED],
	}

	CAP_NEXT_STATE = {
		ActionName.PREPARE: StateName.PREPARED,
		ActionName.DESTROY: StateName.CREATED,
		ActionName.START: StateName.STARTED,
		ActionName.STOP: StateName.PREPARED,
	}

	def __init__(self):
		current_vms = self.vir.getVMs()
		vmid_valid = False
		while not vmid_valid:
			self.vmid = int(random.random()*10000)
			if not self.vmid in current_vms:
				vmid_valid = True
		self.state = StateName.CREATED

	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = StateName.CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		self.vmid = self.getResource("vmid")
		self.vncport = self.getResource("port")
		self.websocket_port = self.getResource("port", config.WEBSOCKIFY_PORT_BLACKLIST)
		self.vncpassword = cmd.randomPassword()
		#template: None, default template

	def _configure(self):
		assert self.state == StateName.PREPARED
		kblang = self.kblang
		if kblang is None:
			kblang = self._template().kblang
		self.vir.setAttributes(self.vmid, cores=self.cpus, memory=self.ram, keyboard=kblang, tablet=self.usbtablet,
			hda=self._imagePath(), fda=self._nlxtp_floppy_filename(), hdb=self._nlxtp_device_filename())

	def action_start(self):
		self._checkState()
		self.vir.start(self.vmid)
		self.setState(StateName.STARTED, True)
		for interface in self.getChildren():
			con = interface.getConnection()
			if con:
				con.connectInterface(self.vir.getNicName(self.vmid, interface.num))
			interface._start()
		if not self.websocket_port:
			self.websocket_port = self.getResource("port")
		self.vncpid, self.websocket_pid = self.vir.startVnc(self.vmid, self.vncpassword, self.vncport, self.websocket_port, '/etc/tomato/server.pem')

	def action_stop(self):
		self._checkState()
		for interface in self.getChildren():
			con = interface.getConnection()
			if con:
				con.disconnectInterface(self.vir.getNicName(self.vmid, interface.num))
			interface._stop()
		if self.vncpid:
			self.vir.stopVnc(self.vncpid, self.websocket_pid)
			del self.vncpid
			del self.websocket_pid
		self.vir.stop(self.vmid)
		self.setState(StateName.PREPARED, True)

	def action_prepare(self):
		self._checkState()
		self.vir.writeInitialConfig(TypeName.KVM, self.vmid, self._imagePathDir())
		self._configure()
		self.vir.create(self.vmid)
		self.setState(StateName.PREPARED, True)
		templ = self._template()
		templ.fetch()
		self._useImage(templ.getPath(), backing=True)
		self._nlxtp_create_device_and_mountpoint()
		# add all interfaces
		for interface in self.getChildren():
			self._addInterface(interface)

	def action_destroy(self):
		self._checkState()
		self.vir.destroy(self.vmid, self._imagePathDir())
		self.setState(StateName.CREATED, True)


	def _addInterface(self, interface):
		assert self.state == StateName.PREPARED
		self.vir.addNic(self.vmid, interface.num)

	def modify_cpus(self, cpus):
		if self.state == StateName.CREATED or self.state == StateName.PREPARED:
			self.cpus = cpus
		if self.state == StateName.PREPARED:
			self.vir.setAttributes(self.vmid,{"cpu": self.cpus})

	def modify_ram(self, ram):
		if self.state == StateName.CREATED or self.state == StateName.PREPARED:
			self.ram = ram
		if self.state == StateName.PREPARED:
			self.vir.setAttributes(self.vmid,{"ram": self.ram})

	def modify_kblang(self, kblang):
		if self.state == StateName.CREATED or self.state == StateName.PREPARED:
			self.kblang = kblang
		if self.state == StateName.PREPARED:
			self.vir.setAttributes(self.vmid,{"kblang": self.kblang})

	def modify_usbtablet(self, usbtablet):
		if self.state == StateName.CREATED or self.state == StateName.PREPARED:
			self.usbtablet = usbtablet
		if self.state == StateName.PREPARED:
			self.vir.setAttributes(self.vmid,{"usbtablet": self.usbtablet})

	def modify_template(self, tmplName):
		self._checkState()
		self.template = resources.template.get(self.TYPE, tmplName)
		if tmplName:
			UserError.check(self.template, code=UserError.ENTITY_DOES_NOT_EXIST, message="The selected template does not exist on this host.")
		if self.state == StateName.PREPARED:
			templ = self._template()
			templ.fetch()
			self._useImage(templ.getPath(), backing=True)

	def _useImage(self, path_, backing=False):
		assert self.state == StateName.PREPARED
		if backing:
			if os.path.exists(self._imagePath()):
				os.unlink(self._imagePath())
			qemu_img.create(self._imagePath(), backingImage=path_)
		else:
			io.copy(path_, self._imagePath())

	def _checkState(self):
		savedState = self.state
		realState = self.vir.getState(self.vmid)
		if savedState != realState:
			self.setState(realState, True)
		InternalError.check(savedState == realState, InternalError.WRONG_DATA, "Saved state is wrong",
			data={"type": self.type, "id": self.id, "saved_state": savedState, "real_state": realState})

	def _imagePathDir(self):
		return "/var/lib/vz/images/%d" % self.vmid

	def _imagePath(self, file="disk.qcow2"): #@ReservedAssignment
		return os.path.join(self._imagePathDir(), file)

def register():  # pragma: no cover
		print "register KVM"
		if not os.path.exists("/dev/kvm"):
			print "Nope os path"
			print >> sys.stderr, "Warning: KVM needs /dev/kvm, disabled"
			return
		if not virshVersion:
			print "Nope virsh"
			print >> sys.stderr, "Warning: KVM needs virsh, disabled"
			return
		if not ([0, 3] <= virshVersion < [2, 3]):
			print "Nope virsh Version"
			print >> sys.stderr, "Warning: KVM not supported on pve-qemu-kvm version %s, disabled" % virshVersion
			return
		if not socatVersion:
			print >> sys.stderr, "Warning: KVM needs socat, disabled"
			return
		if not tcpserverVersion:
			print >> sys.stderr, "Warning: KVM needs ucspi-tcp, disabled"
			return
		if not dosfstoolsVersion:
			print >> sys.stderr, "Warning: KVM needs dosfstools, disabled"
			return
		if not ipspyVersion:
			print >> sys.stderr, "Warning: ipspy not available"
		elements.TYPES[KVM.TYPE] = KVM

if not config.MAINTENANCE:
	tcpserverVersion = cmd.getDpkgVersion("ucspi-tcp")
	websockifyVersion = cmd.getDpkgVersion("websockify")
	socatVersion = cmd.getDpkgVersion("socat")
	virshVersion = cmd.getVirshVersion()
	dosfstoolsVersion = cmd.getDpkgVersion("dosfstools")
	ipspyVersion = cmd.getDpkgVersion("ipspy")
	register()


DOC_IFACE = """
Element type: ``kvm_interface``

Description:
	This element type represents a network interface of kvmqm element type. Its
	state is managed by and synchronized with the parent element.

Possible parents: ``kvmqm``

Possible children: None

Default state: *created*

Removable in states: *created* and *prepared*

Connection concepts: *interface*

States:
	*created*: In this state the interface is known of but qm does not know about
		it.
	*prepared*: In this state the interface is present in the qm configuration
		but not running.
	*started*: In this state the interface is running.

Attributes: None

Actions: None
"""


class KVM_Interface(elements.Element):
	num_attr = Attr("num", type="int")
	num = num_attr.attribute()
	name_attr = Attr("name", desc="Name", type="str", regExp="^eth[0-9]+$", states=[StateName.CREATED])
	mac_attr = Attr("mac", desc="MAC Address", type="str")
	mac = mac_attr.attribute()
	ipspy_pid_attr = Attr("ipspy_pid", type="int")
	ipspy_pid = ipspy_pid_attr.attribute()
	used_addresses_attr = Attr("used_addresses", type=list, default=[])
	used_addresses = used_addresses_attr.attribute()

	TYPE = TypeName.KVM_INTERFACE
	CAP_ACTIONS = {
		elements.REMOVE_ACTION: [StateName.CREATED, StateName.PREPARED]
	}
	CAP_NEXT_STATE = {}
	CAP_ATTRS = {
		"name": name_attr,
		"timeout": elements.Element.timeout_attr
	}
	CAP_CHILDREN = {}
	CAP_PARENT = [KVM.TYPE]
	CAP_CON_CONCEPTS = [connections.CONCEPT_INTERFACE]
	DOC = DOC_IFACE
	__doc__ = DOC_IFACE  # @ReservedAssignment

	class Meta:
		db_table = "tomato_kvm_interface"
		app_label = 'tomato'

	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = StateName.CREATED
		elements.Element.init(self, *args, **kwargs)  # no id and no attrs before this line
		assert isinstance(self.getParent(), KVM)
		self.num = self.getParent()._nextIfaceNum()
		self.mac = net.randomMac()

	def modify_name(self, val):
		self.num = int(re.match("^eth([0-9]+)$", val).groups()[0])

	def interfaceName(self):
		if self.state != StateName.CREATED:
			try:
				return virsh.getNicName(self.getParent().vmid, self.num)
			except virsh.QMError as err:
				if err.code == virsh.QMError.CODE_NO_SUCH_NIC:
					return
				raise
		else:
			return None

	def upcast(self):
		return self

	def _start(self):
		self.ipspy_pid = ipspy.start(self.interfaceName(), self.dataPath("ipspy.json"))
		self.save()

	def _stop(self):
		if self.ipspy_pid:
			ipspy.stop(self.ipspy_pid)
			del self.ipspy_pid
		self.save()

	def info(self):
		path = self.dataPath("ipspy.json")
		if self.state == StateName.STARTED and os.path.exists(path):
			self.used_addresses = ipspy.read(path)
		else:
			self.used_addresses = []
		info = elements.Element.info(self)
		info["attrs"]["name"] = "eth%d" % (self.num or 0)
		return info

	def updateUsage(self, usage, data):
		if self.state == StateName.STARTED:
			ifname = self.interfaceName()
			if net.ifaceExists(ifname):
				traffic = sum(net.trafficInfo(ifname))
				usage.updateContinuous("traffic", traffic, data)


KVM_Interface.__doc__ = DOC_IFACE
