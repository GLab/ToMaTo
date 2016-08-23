from util import run
from constants import ActionName, StateName, TypeName
import time
import xml.etree.ElementTree as ET



class kvm:


	vmid = "bob"
	state = "init"
	tree = None
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
		self.vmid = "bob"
		self.state = "init"

		self.tree = ET.parse('%s.xml' % self.vmid)
		root = self.tree.getroot()

		for devices in root.findall('devices'):
			for disks in devices.findall('disk'):
				for original in disks.findall('source'):
					self.original_image = original.get('file')
					print self.original_image
					parts = self.original_image.split("/")
					for i in range(0, parts.__len__() - 1):
						self.imagepath += parts[i]
						self.imagepath += "/"
					self.imagepath += ("%s.qcow2" % self.vmid)
					print self.imagepath

	def action_start(self):
		run(["virsh", "start", "%s" % self.vmid])

	def action_prepare(self):
		#copy template
		run(["cp", self.original_image, self.imagepath])
		#copy xml file and adjust UUID etc.

		#define and start vm
		run(["virsh", "define", "%s.xml" % self.vmid])
		run(["virsh", "create", "%s.xml" % self.vmid])

	def action_stop(self):
		run(["virsh", "shutdown", "%s" % self.vmid])

	def action_destroy(self):
		run(["virsh", "shutdown", "%s" % self.vmid])
		while(self.state != "shut off"):
			time.sleep(1)
			self.checkState()
		time.sleep(2)
		run(["virsh", "undefine", "%s" % self.vmid]) #--remove-all-storage --managed-save --snapshots-metadata
		run(["rm", self.imagepath])

	def checkState(self):
		self.state = run(["virsh", "domstate", "%s" % self.vmid])
		self.state = self.state[:-2]
		#print self.state
		return self.state

var = kvm()
var.checkState()
#var.action_prepare()
#var.action_destroy()
