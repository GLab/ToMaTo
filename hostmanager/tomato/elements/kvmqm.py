# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import os, sys, re, shutil
from .. import connections, elements, resources, config
from ..resources import template
from ..lib.attributes import Attr #@UnresolvedImport
from ..lib import cmd #@UnresolvedImport
from ..lib.cmd import fileserver #@UnresolvedImport
from ..lib.util import joinDicts #@UnresolvedImport
from ..lib.error import UserError, InternalError
from ..lib.newcmd import qm, vfat, qemu_img, ipspy
from ..lib.newcmd.util import net, proc, io
from ..lib.constants import ActionName, StateName, TechName


from ..generic import *
from ..db import *

DOC="""
Element type: ``kvmqm``

Description:
	This element type provides full virtualization by using the KVM 
	virtualization technology. The proxmox frontend qm is used to control KVM,
	thus the name kvmqm.

Possible parents: None

Possible children:
	``kvmqm_interface`` (can be added in states *created* and *prepared*)

Default state: *created*

Removable in states: *created*

Connection concepts: None

States:
	*created*: In this state the VM is known of but qm does not know about it.
		No state is stored and no resources are consumed in this state.
	*prepared*: In this state the VM is present in the qm configuration and the
		disk image exists but the VM is not running. The disk image stores some
		state information. The VM is not consuming any resources except for the
		disk image.
	*started*: In this state the VM is running and can be accessed by the user.
		The VM holds a disk state and a memory state. It consumes disk storage
		memory, cpu power, io and networking resources.
		
Attributes:
	*cpus*: int, changeable in states *created* and *prepared*, default: ``1``
		The number of virtual processors that the VM should have. Each virtual
		processor can take the resources of one physical processor.
	*ram*: int, changeable in states *created* and *prepared*, default: ``256``
		The amount of memory the VM should have in megabytes. The virtual
		machine will only be able to access this much virtual memory. RAM that
		has been allocated once will stay allocated as long as the VM is
		running, so in the long run VMs tend to use the maximum amount of RAM.
	*kblang*: str, changeable in states *created* and *prepared*, default: ``de``
		The language of the emulated keyboard. This attribute defines how
		keyboard input is translated in keycodes that are handed over to the
		VM. This setting should correspond to the keyboard setting inside of 
		the VM. 
	*usbtablet*: bool, changeable in states *created* and *prepared*, default: ``True``
		Whether to emulate an USB tablet input device or a normal PS/2 mouse.
		A USB tablet input has the advantage that it uses absolute positions
		to position the mouse pointer instead of relative movements like PS/2
		does. That means that it is easier for viewers to track the mouse 
		position and to avoid offsets. On operating systems that do not support
		USB tablet devices this setting must be disabled, otherwise no mouse 
		will be available. 
	*template*: str, changeable in states *created* and *prepared*
		The name of a template of matching virtualization technology to be used
		for this VM. A copy of this template will be used as an initial disk 
		image when the device is being prepared. When this attribute is changed
		in the state prepared, the disk image will be reset to the template.
		If no template with the given name exists (esp. for template=None),
		a default template is chosen instead.
		WARNING: Setting this attribute for a prepared VM will cause the loss
		of the disk image.   
	*vncport*: int, read-only
		The port on this host on which the VM can be accessed via VNC when it
		is running. 
	*vncpassword*: int, read-only
		The random password that has to be used to connect to this VM using 
		VNC. This password should be kept secret.


Actions:
	*prepare*, callable in state *created*, next state: *prepared*
		Creates a qm configuration entry for this VM and uses a copy of the
		template as disk image.
	*destroy*, callable in state *prepared*, next state: *created*
	 	Removes the qm configuration entry and deletes the disk image.
	*start*, callable in state *prepared*, next state: *started*
	 	Starts the VM and initiates a boot of the contained OS. This action
	 	also starts a VNC server for the VM and connects all the interfaces
	 	of the device.
	*stop*, callable in state *started*, next state: *prepared*
	 	Stops the VNC server, disconnects all the interfaces of the VM and
	 	then initiates an OS shutdown using an ACPI shutdown request. The
	 	contained OS then has 10 seconds to shut down by itself. After this
	 	time, the VM is just stopped.
	 	Note: Users should make sure their VMs shut down properly to decrease
	 	stop time and to avoid data loss or damages in the virtual machine.
	*upload_grant*, callable in state *prepared*
	 	Create/update a grant to upload an image for the VM. The created grant
	 	will be available as an attribute called upload_grant. The grant allows
	 	the user to upload a file for a certain time. The url where the file 
	 	must be uploaded has the form http://server:port/grant/upload where
	 	server is the address of this host, port is the fileserver port of this
	 	server (can be requested via host_info) and grant is the grant.
	 	The uploaded file can be used as the VM image with the upload_use 
	 	action. 
	*rextfv_upload_grant*, callable in state *prepared* 
		same as upload_grant, but for use with rextfv_upload_use.
	*upload_use*, callable in state *prepared*
		Uses a previously uploaded file as the image of the VM. 
	*rextfv_upload_use*, callable in state *prepared*
		Uses a previously uploaded archive to insert into the VM's nlXTP directory.
		Deletes old content from this directory.
	*download_grant*, callable in state *prepared*
	 	Create/update a grant to download the image for the VM. The created 
	 	grant will be available as an attribute called download_grant. The
	 	grant allows the user to download the VM image once for a certain time.
	 	The url where the file can be downloaded from has the form 
	 	http://server:port/grant/download where server is the address of this
	 	host, port is the fileserver port of this server (can be requested via
	 	host_info) and grant is the grant.
	*rextfv_download_grant*, callable in state *prepared* or *started*
		same as download_grant, but only for the nlXTP folder
"""
"""
kblang_options = {"en-us": "English (US)", 
					"en-gb": "English (GB)", 
					"de": "German", 
					"fr": "French", 
					"ja": "Japanese"
					}
"""

kblang_options = ["en-us","en-gb","de", "fr", "ja"]

class KVMQM(elements.Element, elements.RexTFVElement):

	vmid = IntField()
	websocket_port = IntField()
	websocket_pid = IntField()
	vncport = IntField()
	vncpid = IntField()
	vncpassword =StringField()
	cpus = IntField(default=1)
	ram = IntField(default=256)
	kblang = StringField(default=None, choises=kblang_options)
	usbtablet = BooleanField(default=True)
	template = ReferenceField(resources.template.Template)
	templateId = ReferenceFieldId(template)


	
	rextfv_max_size = 512*1024*124 # depends on _nlxtp_create_device_and_mountpoint.

	TYPE = TechName.KVMQM

	CAP_CHILDREN = {
		TechName.KVMQM_INTERFACE: [StateName.CREATED, StateName.PREPARED],
	}
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {"cpus": 1, "ram": 256, "kblang": None, "usbtablet": True}
	__doc__ = DOC #@ReservedAssignment
	DOC = DOC

	@property
	def type(self):
		return self.TYPE

	def init(self, *args, **kwargs):
		self.state = StateName.CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		self.vmid = self.getResource("vmid")
		self.vncport = self.getResource("port")
		self.websocket_port = self.getResource("port", config.WEBSOCKIFY_PORT_BLACKLIST)
		self.vncpassword = cmd.randomPassword()
		#template: None, default template
				
	def _imagePathDir(self):
		return "/var/lib/vz/images/%d" % self.vmid

	def _imagePath(self, file="disk.qcow2"): #@ReservedAssignment
		return os.path.join(self._imagePathDir(), file)

	def _getState(self):
		if not self.vmid:
			return StateName.CREATED
		res = qm.getStatus(self.vmid)
		if res == qm.Status.Running:
			return StateName.STARTED
		if res == qm.Status.Stopped:
			return StateName.PREPARED
		if res == qm.Status.NoSuchVm:
			return StateName.CREATED

	def _checkState(self):
		savedState = self.state
		realState = self._getState()
		if savedState != realState:
			self.setState(realState, True)
		InternalError.check(savedState == realState, InternalError.WRONG_DATA, "Saved state is wrong",
			data={"type": self.type, "id": str(self.id), "saved_state": savedState, "real_state": realState})

	def _template(self):
		if self.template:
			return self.template.upcast()
		pref = resources.template.getPreferred(self.TYPE)
		InternalError.check(pref, InternalError.UNKNOWN, "Failed to find template", data={"type": self.TYPE})
		return pref
				
	def _nextIfaceNum(self):
		ifaces = self.getChildren()
		num = 0
		while num in [iface.num for iface in ifaces]:
			num += 1
		return num

	def _addInterface(self, interface):
		assert self.state == StateName.PREPARED
		qm.addNic(self.vmid, interface.num)

	def _removeInterface(self, interface):
		assert self.state == StateName.PREPARED
		try:
			qm.delNic(self.vmid, interface.num)
		except qm.QMError as err:
			if err.code == qm.QMError.CODE_NO_SUCH_NIC:
				err.dump()
				# ignore error as it is exactly what we wanted
			else:
				raise

	def _configure(self):
		assert self.state == StateName.PREPARED
		kblang = self.kblang
		if kblang is None:
			kblang = self._template().kblang
		qm.configure(self.vmid, cores=self.cpus, memory=self.ram, keyboard=kblang, tablet=self.usbtablet,
			hda=self._imagePath(), fda=self._nlxtp_floppy_filename(), hdb=self._nlxtp_device_filename())

	def _checkImage(self, path):
		try:
			qemu_img.check(path, format='qcow2')
		except qm.QMError:
			raise UserError(UserError.INVALID_VALUE, "File is not a valid qcow2 image")

	def onChildAdded(self, interface):
		self._checkState()
		if self.state == StateName.PREPARED:
			self._addInterface(interface)
		interface.setState(self.state)

	def onChildRemoved(self, interface):
		self._checkState()
		if self.state == StateName.PREPARED:
			self._removeInterface(interface)
		interface.setState(self.state)

	def modify_cpus(self, cpus):
		self._checkState()
		self.cpus = cpus
		if self.state == StateName.PREPARED:
			self._configure()

	def modify_ram(self, ram):
		self._checkState()
		self.ram = ram
		if self.state == StateName.PREPARED:
			self._configure()
		
	def modify_kblang(self, kblang):
		self._checkState()
		self.kblang = kblang
		if self.state == StateName.PREPARED:
			self._configure()
		
	def modify_usbtablet(self, usbtablet):
		self._checkState()
		self.usbtablet = usbtablet
		if self.state == StateName.PREPARED:
			self._configure()
		
	def modify_template(self, tmplName):
		self._checkState()
		self.template = resources.template.get(self.TYPE, tmplName)
		if tmplName:
			UserError.check(self.template, code=UserError.ENTITY_DOES_NOT_EXIST, message="The selected template does not exist on this host.")
		if self.state == StateName.PREPARED:
			templ = self._template()
			templ.fetch(detached=False, init=self.INITIALIZING)
			self._useImage(templ.getPath(), backing=True)

	def _useImage(self, path_, backing=False):
		assert self.state == StateName.PREPARED
		if backing:
			if os.path.exists(self._imagePath()):
				os.unlink(self._imagePath())
			qemu_img.create(self._imagePath(), backingImage=path_)
		else:
			io.copy(path_, self._imagePath())


	def action_prepare(self):
		self._checkState()
		qm.create(self.vmid)
		self.setState(StateName.PREPARED, True)
		templ = self._template()
		templ.fetch()
		self._useImage(templ.getPath(), backing=True)
		self._nlxtp_create_device_and_mountpoint()
		self._configure()
		# add all interfaces
		for interface in self.getChildren():
			self._addInterface(interface)

	def action_destroy(self):
		self._checkState()
		qm.destroy(self.vmid)
		self.setState(StateName.CREATED, True)

	def action_start(self):
		self._checkState()
		qm.start(self.vmid)
		self.setState(StateName.STARTED, True)
		for interface in self.getChildren():
			con = interface.getConnection()
			if con:
				con.connectInterface(qm.getNicName(self.vmid, interface.num))
			interface._start()
		if not self.websocket_port:
			self.websocket_port = self.getResource("port")
		self.vncpid, self.websocket_pid = qm.startVnc(self.vmid, self.vncpassword, self.vncport, self.websocket_port, '/etc/tomato/server.pem')

	def action_stop(self):
		self._checkState()
		for interface in self.getChildren():
			con = interface.getConnection()
			if con:
				con.disconnectInterface(qm.getNicName(self.vmid, interface.num))
			interface._stop()
		if self.vncpid:
			qm.stopVnc(self.vncpid, self.websocket_pid)
			del self.vncpid
			del self.websocket_pid
		qm.stop(self.vmid)
		self.setState(StateName.PREPARED, True)
		
	def action_upload_grant(self):
		return fileserver.addGrant(self._imagePath("uploaded.qcow2"), fileserver.ACTION_UPLOAD)
	
	def action_rextfv_upload_grant(self):
		return fileserver.addGrant(self.dataPath("rextfv_up.tar.gz"), fileserver.ACTION_UPLOAD)
		
	def action_upload_use(self):
		UserError.check(os.path.exists(self._imagePath("uploaded.qcow2")), UserError.NO_DATA_AVAILABLE, "No file has been uploaded")
		self._checkImage(self._imagePath("uploaded.qcow2"))
		os.rename(self._imagePath("uploaded.qcow2"), self._imagePath())
		
	def action_rextfv_upload_use(self):
		UserError.check(os.path.exists(self.dataPath("rextfv_up.tar.gz")), UserError.NO_DATA_AVAILABLE, "No file has been uploaded")
		self._use_rextfv_archive(self.dataPath("rextfv_up.tar.gz"))
		shutil.copy(config.DUMMY_FLOPPY, self._nlxtp_floppy_filename())

	def action_download_grant(self):
		qemu_img.export(self._imagePath(), self._imagePath("download.qcow2"))
		return fileserver.addGrant(self._imagePath("download.qcow2"), fileserver.ACTION_DOWNLOAD, removeFn=fileserver.deleteGrantFile)
	
	def action_rextfv_download_grant(self):
		self._create_rextfv_archive(self.dataPath("rextfv.tar.gz"))
		return fileserver.addGrant(self.dataPath("rextfv.tar.gz"), fileserver.ACTION_DOWNLOAD, removeFn=fileserver.deleteGrantFile)
	
	
	

	#The nlXTP directory
	def _nlxtp_path(self,filename):
		return self.dataPath(os.path.join("nlxtp", "mountpoint", filename))
		
	#The nlXTP device
	def _nlxtp_device_filename(self):
		return self.dataPath(os.path.join("nlxtp", "bigdevice"))
		
	#The nlXTP device
	def _nlxtp_floppy_filename(self):
		return self.dataPath(os.path.join("nlxtp", "device"))

	def _nlxtp_make_readable(self): #mount device file readonly
		self._nlxtp_create_device_and_mountpoint()
		vfat.unmount(self._nlxtp_path(""), ignoreUnmounted=True)
		vfat.mount(self._nlxtp_device_filename(), self._nlxtp_path(""), readOnly=True, partition=1)
	
	def _nlxtp_make_writeable(self): #mount device file r/w
		self._nlxtp_create_device_and_mountpoint()
		vfat.unmount(self._nlxtp_path(""), ignoreUnmounted=True)
		vfat.mount(self._nlxtp_device_filename(), self._nlxtp_path(""), sync=True, partition=1)
	
	def _nlxtp_close(self): #unmount device file
		vfat.unmount(self._nlxtp_path(""))
		
	def _nlxtp_create_device_and_mountpoint(self): #if device file or mount point do not exist: create
		if not os.path.exists(self._nlxtp_path("")):
			os.makedirs(self._nlxtp_path(""))
		shutil.copy(config.DUMMY_FLOPPY, self._nlxtp_floppy_filename())
		if not os.path.exists(self._nlxtp_device_filename()):
			vfat.create(self._nlxtp_device_filename(), KVMQM.rextfv_max_size/1024, nested=True) # size (last argument) depends on nlxtp_max_size
	
	
		
	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info = joinDicts(info, elements.RexTFVElement.info(self))
		info["attrs"]["template"] = self.template.upcast().name if self.template else None
		return info

	def updateUsage(self, usage, data):
		self._checkState()
		if self.state == StateName.CREATED:
			return
		if self.state == StateName.STARTED:
			memory = 0
			cputime = 0
			stats = qm.getStatistics(self.vmid)
			memory += stats.memory_used
			cputime += stats.cputime_total
			if self.vncpid and proc.isAlive(self.vncpid):
				stats = proc.getStatistics(self.vncpid)
				memory += stats.memory_used
				cputime += stats.cputime_total
			if self.websocket_pid and proc.isAlive(self.websocket_pid):
				stats = proc.getStatistics(self.websocket_pid)
				memory += stats.memory_used
				cputime += stats.cputime_total
			usage.memory = memory
			usage.updateContinuous("cputime", cputime, data)
		usage.diskspace = io.getSize(self._imagePathDir())

	ATTRIBUTES = elements.Element.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"vmid": Attribute(field=vmid, readOnly=True, schema=schema.Int()),
		"websocket_port": Attribute(field=websocket_port, readOnly=True, schema=schema.Int()),
		"websocket_pid": Attribute(field=websocket_pid, readOnly=True, schema=schema.Int()),
		"vncport": Attribute(field=vncport, readOnly=True, schema=schema.Int()),
		"vncpid": Attribute(field=vncpid, readOnly=True, schema=schema.Int()),
		"vncpassword": Attribute(field=vncpassword, readOnly=True, schema=schema.String()),
		"cpus": Attribute(field=cpus, description="Number of CPUs", set=modify_cpus, schema=schema.Number(minValue=1,maxValue=4), default=1),
		"ram": Attribute(field=ram, description="RAM", set=modify_ram, schema=schema.Int(minValue=64, maxValue=8192), default=256),
		"kblang": Attribute(field=kblang, description="Keyboard language", set=modify_kblang, schema=schema.String(options=kblang_options), default=None),
		"usbtablet": Attribute(field=usbtablet, description="USB tablet mouse mode", set=modify_usbtablet, schema=schema.Bool(), default=True),
		"template": Attribute(field=templateId, description="Template", set=modify_template, schema=schema.Identifier()),
	})

	ACTIONS = elements.Element.ACTIONS.copy()
	ACTIONS.update({
		Entity.REMOVE_ACTION: StatefulAction(elements.Element.remove, check=elements.Element.checkRemove, allowedStates=[StateName.CREATED]),
		ActionName.START: StatefulAction(action_start, allowedStates=[StateName.CREATED, StateName.PREPARED], stateChange=StateName.STARTED),
		ActionName.STOP: StatefulAction(action_stop, allowedStates=[StateName.STARTED], stateChange=StateName.PREPARED),
		ActionName.PREPARE: StatefulAction(action_prepare, allowedStates=[StateName.CREATED], stateChange=StateName.PREPARED),
		ActionName.DESTROY: StatefulAction(action_destroy, allowedStates=[StateName.PREPARED, StateName.STARTED],
										   stateChange=StateName.CREATED),
		ActionName.UPLOAD_GRANT: StatefulAction(action_upload_grant, allowedStates=[StateName.PREPARED]),
		ActionName.REXTFV_UPLOAD_GRANT: StatefulAction(action_rextfv_upload_grant, allowedStates=[StateName.PREPARED]),
		ActionName.UPLOAD_USE: StatefulAction(action_upload_use, allowedStates=[StateName.PREPARED]),
		ActionName.REXTFV_UPLOAD_USE: StatefulAction(action_rextfv_upload_use, allowedStates=[StateName.PREPARED]),
		"download_grant": StatefulAction(action_download_grant, allowedStates=[StateName.PREPARED]),
		"rextfv_download_grant": StatefulAction(action_rextfv_download_grant, allowedStates=[StateName.PREPARED, StateName.STARTED]),
	})

KVMQM.__doc__ = DOC


DOC_IFACE="""
Element type: ``kvmqm_interface``

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

class KVMQM_Interface(elements.Element):


	num = IntField()
	name = StringField()
	mac = StringField()
	ipspy_pid = IntField()
	used_addresses = ListField(default=[])
	
	TYPE = TechName.KVMQM_INTERFACE

	CAP_CHILDREN = {}
	CAP_PARENT = [KVMQM.TYPE]
	CAP_CON_CONCEPTS = [connections.CONCEPT_INTERFACE]
	DOC = DOC_IFACE
	__doc__ = DOC_IFACE #@ReservedAssignment
	

	@property
	def type(self):
		return self.TYPE

	def init(self, *args, **kwargs):
		self.state = StateName.CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		assert isinstance(self.getParent(), KVMQM)
		self.num = self.getParent()._nextIfaceNum()
		self.mac = net.randomMac()

	def modify_name(self, val):
		self.num = int(re.match("^eth([0-9]+)$", val).groups()[0])
			
	def interfaceName(self):
		if self.state != StateName.CREATED:
			try:
				return qm.getNicName(self.getParent().vmid, self.num)
			except qm.QMError as err:
				if err.code == qm.QMError.CODE_NO_SUCH_NIC:
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

	ATTRIBUTES = elements.Element.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"num": Attribute(field=num, schema=schema.Int(), readOnly=True),
		"mac": Attribute(field=mac, description="Mac Address", schema=schema.String(), readOnly=True),
		"ipspy_id": Attribute(field=ipspy_pid, schema=schema.Int(), readOnly=True),
		"name": Attribute(field=name, description="Name", schema=schema.String(regex="^eth[0-9]+$")),
		"used_addresses": Attribute(field=used_addresses, schema=schema.List(), default=[], readOnly=True),
	})

	ACTIONS = elements.Element.ACTIONS.copy()
	ACTIONS.update({Entity.REMOVE_ACTION: StatefulAction(elements.Element.remove, check=elements.Element.checkRemove, allowedStates=[StateName.CREATED]),
		})

KVMQM_Interface.__doc__ = DOC_IFACE

def register(): #pragma: no cover
	if not os.path.exists("/dev/kvm"):
		print >>sys.stderr, "Warning: KVMQM needs /dev/kvm, disabled"
		return
	if not qmVersion:
		print >>sys.stderr, "Warning: KVMQM needs a Proxmox VE host, disabled"
		return
	if not ([1, 4] <= qmVersion < [2, 3]):
		print >>sys.stderr, "Warning: KVMQM not supported on pve-qemu-kvm version %s, disabled" % qmVersion
		return
	if not socatVersion:
		print >>sys.stderr, "Warning: KVMQM needs socat, disabled"
		return
	if not tcpserverVersion:
		print >>sys.stderr, "Warning: KVMQM needs ucspi-tcp, disabled"
		return
	if not dosfstoolsVersion:
		print >>sys.stderr, "Warning: KVMQM needs dosfstools, disabled"
		return
	if not ipspyVersion:
		print >>sys.stderr, "Warning: ipspy not available"
	elements.TYPES[KVMQM.TYPE] = KVMQM
	elements.TYPES[KVMQM_Interface.TYPE] = KVMQM_Interface

if not config.MAINTENANCE:
	tcpserverVersion = cmd.getDpkgVersion("ucspi-tcp")
	websockifyVersion = cmd.getDpkgVersion("websockify")
	socatVersion = cmd.getDpkgVersion("socat")
	qmVersion = cmd.getDpkgVersion("pve-qemu-kvm")
	dosfstoolsVersion = cmd.getDpkgVersion("dosfstools")
	ipspyVersion = cmd.getDpkgVersion("ipspy")
	register()
