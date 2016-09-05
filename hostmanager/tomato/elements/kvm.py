from util import run
from ..lib.constants import ActionName, StateName, TypeName
from ..lib.newcmd import virsh
import time
import xml.etree.ElementTree as ET
import random

class KVM:

	vmid = "bob"
	state = StateName.CREATED
	tree = None
	imagepath = ""
	original_image = ""
	vir = vir = virsh.virsh(TypeName.KVM)
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

	def checkState(self):
		realState = self.vir.getState(self.vmid)
		#maybe add some checks if realstate differs from saved state
		self.state = realState
		#print self.state
		return self.state
