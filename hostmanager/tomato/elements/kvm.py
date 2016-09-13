from util import run
from ..lib.constants import ActionName, StateName, TypeName
from django.db import models
from ..resources import template
from .. import connections, elements, resources, config
from ..lib.attributes import Attr #@UnresolvedImport
from ..lib import cmd #@UnresolvedImport
from ..lib.newcmd import virsh, qemu_img
from ..lib.newcmd.util import io
from ..lib.error import UserError
import time
import xml.etree.ElementTree as ET
import random, os

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

	def action_start(self):
		if self.state == StateName.PREPARED:
			self.vir.vm_start(self.vmid)
			self.state = StateName.STARTED

	def action_prepare(self):
		if self.state == StateName.CREATED:
			self.vir.vm_prepare(self.vmid)
			self.state = StateName.PREPARED

	def action_stop(self):
		if self.state == StateName.STARTED:
			self.vir.vm_stop(self.vmid)
			self.state = StateName.PREPARED

	def action_destroy(self):
		self.vir.vm_destroy(self.vmid)
		self.state = StateName.CREATED

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

	def checkState(self):
		realState = self.vir.getState(self.vmid)
		#maybe add some checks if realstate differs from saved state
		self.state = realState
		#print self.state
		return self.state

	def _imagePathDir(self):
		return "/var/lib/vz/images/%d" % self.vmid

	def _imagePath(self, file="disk.qcow2"): #@ReservedAssignment
		return os.path.join(self._imagePathDir(), file)
