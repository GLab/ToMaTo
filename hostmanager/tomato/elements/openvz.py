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

import os.path, sys
from django.db import models
from .. import connections, elements, config
from ..resources import template
from ..lib.attributes import Attr #@UnresolvedImport
from ..lib import decorators, util, cmd #@UnresolvedImport
from ..lib.cmd import fileserver, process, net, path, CommandError #@UnresolvedImport
from ..lib.util import joinDicts #@UnresolvedImport
from ..lib.error import UserError, InternalError

DHCP_CMDS = ["[ -e /sbin/dhclient ] && /sbin/dhclient -nw %s",
			 "[ -e /sbin/dhcpcd ] && /sbin/dhcpcd %s"]

DOC="""
Element type: ``openvz``

Description:
	This element type provides container virtualization by using the OpenVZ 
	virtualization technology. The proxmox frontend vzctl is used to control
	OpenVZ.

Possible parents: None

Possible children:
	``openvz_interface`` (can be added in states *created* and *prepared*)

Default state: *created*

Removable in states: *created*

Connection concepts: None

States:
	*created*: In this state the VM is known of but vzctl does not know about it.
		No state is stored and no resources are consumed in this state.
	*prepared*: In this state the VM is present in the vzctl configuration and 
		the disk image exists but the VM is not running. The disk image stores 
		some state information. The VM is not consuming any resources except 
		for the	disk image.
	*started*: In this state the VM is running and can be accessed by the user.
		The VM holds a disk state and a memory state. It consumes disk storage
		memory, cpu power, io and networking resources.
		
Attributes:
	*ram*: int, changeable in all states, default: ``256``
		The amount of memory the VM should have in megabytes. The virtual
		machine will only be able to access this much virtual memory. The RAM
		used by the VM will match the RAM usage inside the VM.
	*diskspace*: int, changeable in all states, default: ``10240``
		The amount of disk space, the VM should have in megabytes. The virtual
		machine will only be able to access this much disk space. The disk 
		space used by the VM will match the disk usage inside the VM.
	*rootpassword*: str, changeable in all states
		The password of the user 'root' inside the VM.
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux.
	*hostname*, str, changeable in all states
		The hostname as seen inside the VM.
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux.
	*gateway4*, str, changeable in all states
		The IPv4 default route to be used inside the VM. The route must be a 
		valid IPv4 address.
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux.
	*gateway6*, str, changeable in all states
		The IPv6 default route to be used inside the VM. The route must be a 
		valid IPv6 address.
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux.
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
		Creates a vzctl configuration entry for this VM and uses a copy of
		the	template as disk image.
	*destroy*, callable in state *prepared*, next state: *created*
		 Removes the vzctl configuration entry and deletes the disk image.
	*start*, callable in state *prepared*, next state: *started*
		 Starts the VM and initiates a boot of the contained OS. This action
		 also starts a VNC server for the VM and connects all the interfaces
		 of the device.
	*stop*, callable in state *started*, next state: *prepared*
		 Stops the VNC server, disconnects all the interfaces of the VM and
		 then initiates an OS shutdown using the runlevel system.
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

ST_CREATED = "created"
ST_PREPARED = "prepared"
ST_STARTED = "started"

class OpenVZ(elements.RexTFVElement,elements.Element):
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
	ram_attr = Attr("ram", desc="RAM", unit="MB", type="int", minValue=64, maxValue=4096, default=256)
	ram = ram_attr.attribute()
	cpus_attr = Attr("cpus", desc="Number of CPUs", type="float", minValue=0.1, maxValue=4.0, default=1.0)
	cpus = cpus_attr.attribute()
	diskspace_attr = Attr("diskspace", desc="Disk space", unit="MB", type="int", minValue=512, maxValue=102400, default=10240)
	diskspace = diskspace_attr.attribute()
	rootpassword_attr = Attr("rootpassword", desc="Root password", type="str")
	rootpassword = rootpassword_attr.attribute()
	hostname_attr = Attr("hostname", desc="Hostname", type="str")
	hostname = hostname_attr.attribute()
	gateway4_attr = Attr("gateway4", desc="IPv4 gateway", type="str")
	gateway4 = gateway4_attr.attribute()	
	gateway6_attr = Attr("gateway6", desc="IPv6 gateway", type="str")
	gateway6 = gateway6_attr.attribute()		
	template_attr = Attr("template", desc="Template", states=[ST_CREATED, ST_PREPARED], type="str", null=True)
	template = models.ForeignKey(template.Template, null=True)

	TYPE = "openvz"
	CAP_ACTIONS = {
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		"start": [ST_PREPARED],
		"stop": [ST_STARTED],
		"upload_grant": [ST_PREPARED],
		"rextfv_upload_grant": [ST_PREPARED,ST_STARTED],
		"upload_use": [ST_PREPARED],
		"rextfv_upload_use": [ST_PREPARED,ST_STARTED],
		"download_grant": [ST_PREPARED],
		"rextfv_download_grant": [ST_PREPARED,ST_STARTED],
		"execute": [ST_STARTED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CAP_NEXT_STATE = {
		"prepare": ST_PREPARED,
		"destroy": ST_CREATED,
		"start": ST_STARTED,
		"stop": ST_PREPARED,
	}	
	CAP_ATTRS = {
		"cpus": cpus_attr,
		"ram": ram_attr,
		"diskspace": diskspace_attr,
		"rootpassword": rootpassword_attr,
		"hostname": hostname_attr,
		"gateway4": gateway4_attr,
		"gateway6": gateway6_attr,
		"template": template_attr,
		"timeout": elements.Element.timeout_attr
	}
	CAP_CHILDREN = {
		"openvz_interface": [ST_CREATED, ST_PREPARED],
	}
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {"ram": 256, "diskspace": 10240}
	DOC = DOC
	__doc__ = DOC #@ReservedAssignment
	
	class Meta:
		db_table = "tomato_openvz"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		self.vmid = self.getResource("vmid")
		self.vncport = self.getResource("port")
		self.websocket_port = self.getResource("port", config.WEBSOCKIFY_PORT_BLACKLIST)
		self.vncpassword = cmd.randomPassword()
		#template: None, default template
	
	def _imagePath(self):
		return "/var/lib/vz/private/%d" % self.vmid

	# 9: locked
	# [51] Can't umount /var/lib/vz/root/...: Device or resource busy
	@decorators.retryOnError(errorFilter=lambda x: isinstance(x, cmd.CommandError) and x.errorCode in [9, 51])
	def _vzctl(self, cmd_, args=None, timeout=None):
		if not args: args = []
		cmd_ = ["vzctl", cmd_, str(self.vmid)] + args
		if timeout:
			cmd_ = ["perl", "-e", "alarm %d; exec @ARGV" % timeout] + cmd_
		out = cmd.run(cmd_)
		return out
			
	def _execute(self, cmd_, timeout=60):
		assert self.state == ST_STARTED
		out = self._vzctl("exec", [cmd_], timeout=timeout)
		return out
			
	def _getState(self):
		if not self.vmid:
			return ST_CREATED
		res = self._vzctl("status")
		if "exist" in res and "running" in res:
			return ST_STARTED
		if "exist" in res and "down" in res:
			return ST_PREPARED
		if "deleted" in res:
			return ST_CREATED
		raise InternalError(message="Unable to determine openvz state", code=InternalError.INVALID_STATE,
			data={"state": res})

	def _checkState(self):
		savedState = self.state
		realState = self._getState()
		if savedState != realState:
			self.setState(realState, True) #pragma: no cover
		InternalError.check(savedState == realState, InternalError.WRONG_DATA, "Saved state is wrong",
			data={"type": self.type, "id": self.id, "saved_state": savedState, "real_state": realState})

	def _template(self):
		if self.template:
			return self.template.upcast()
		pref = template.getPreferred(self.TYPE)
		InternalError.check(pref, InternalError.CONFIGURATION_ERROR, "Failed to find template", data={"type": self.TYPE})
		return pref

	def _nextIfaceName(self):
		ifaces = self.getChildren()
		num = 0
		while "eth%d" % num in [iface.name for iface in ifaces]:
			num += 1
		return "eth%d" % num
	
	def _interfaceName(self, ifname):
		return "veth%s.%s" % (self.vmid, ifname)
	
	def _addInterface(self, interface):
		assert self.state != ST_CREATED
		self._vzctl("set", ["--netif_add", interface.name, "--save"])
		self._vzctl("set", ["--ifname", interface.name, "--bridge", "dummy", "--mac", interface.mac, "--host_ifname", self._interfaceName(interface.name), "--mac_filter",  "off", "--save"])
		
	def _removeInterface(self, interface):
		assert self.state != ST_CREATED
		self._vzctl("set", ["--netif_del", interface.name, "--save"])
		
	def _setCpus(self):
		assert self.state != ST_CREATED
		self._vzctl("set", ["--cpulimit", str(int(self.cpus * 100)), "--cpus", str(int(self.cpus)), "--save"])

	def _setRam(self):
		assert self.state != ST_CREATED
		val = "%dM" % int(self.ram)
		self._vzctl("set", ["--ram", val, "--swap", val, "--save"])
	
	def _setDiskspace(self):
		assert self.state != ST_CREATED
		val = "%dM" % int(self.diskspace)
		self._vzctl("set", ["--diskspace", val, "--save"])

	def _setRootpassword(self):
		assert self.state != ST_CREATED
		if self.rootpassword:
			self._vzctl("set", ["--userpasswd", "root:%s" % self.rootpassword, "--save"])

	def _setHostname(self):
		assert self.state != ST_CREATED
		if self.hostname:
			self._vzctl("set", ["--hostname", self.hostname, "--save"])
			if self.state == ST_STARTED:
				try:
					self._execute("hostname '%s'" % self.hostname)
				except cmd.CommandError:
					pass

	def _setGateways(self):
		assert self.state == ST_STARTED
		if self.gateway4:
			try:
				while True:
					self._execute("ip -4 route del default")
			except cmd.CommandError:
				pass
			try:
				self._execute("ip -4 route replace default via %s" % self.gateway4)
			except cmd.CommandError as exc:
				if exc.errorCode == 8:
					raise UserError(code=UserError.INVALID_VALUE, message="Invalid IPv4 gateway", data={"gateway": self.gateway4})
				raise
		if self.gateway6:
			try:
				while True:
					self._execute("ip -6 route del default")
			except cmd.CommandError:
				pass
			try:
				self._execute("ip -6 route replace default via %s" % self.gateway6)
			except cmd.CommandError as exc:
				if exc.errorCode == 8:
					raise UserError(code=UserError.INVALID_VALUE, message="Invalid IPv6 gateway", data={"gateway": self.gateway6})
				raise

	def _useImage(self, path_):
		assert self.state != ST_CREATED
		imgPath = self._imagePath()
		path.remove(imgPath, recursive=True)
		path.createDir(imgPath)
		path.extractArchive(path_, imgPath)

	def _checkImage(self, path_):
		res = cmd.run(["tar", "-tzvf", path_, "./sbin/init"])
		UserError.check("0/0" in res, UserError.INVALID_VALUE, "Image contents not owned by root")

	#The nlXTP directory
	def _nlxtp_path(self,filename):
		if self.state != ST_CREATED:
			return os.path.join(self._imagePath(),"mnt","nlXTP",filename)
		else:
			return None

	def _nlxtp_make_readable(self): #if directory does not exist: create it
		if not os.path.exists(self._nlxtp_path("")):
			os.makedirs(self._nlxtp_path(""))
	def _nlxtp_make_writeable(self):
		if not os.path.exists(self._nlxtp_path("")):
			os.makedirs(self._nlxtp_path(""))





	def onChildAdded(self, interface):
		self._checkState()
		if self.state == ST_PREPARED:
			self._addInterface(interface)
		interface.setState(self.state)

	def onChildRemoved(self, interface):
		self._checkState()
		if self.state == ST_PREPARED:
			self._removeInterface(interface)
		interface.setState(self.state)

	def modify_cpus(self, val):
		self.cpus = val
		if self.state != ST_CREATED:
			self._setCpus()
		
	def modify_ram(self, val):
		self.ram = val
		if self.state != ST_CREATED:
			self._setRam()
		
	def modify_diskspace(self, val):
		self.diskspace = val
		if self.state != ST_CREATED:
			self._setDiskspace()

	def modify_rootpassword(self, val):
		self.rootpassword = val
		if self.state != ST_CREATED:
			self._setRootpassword()
	
	def modify_hostname(self, val):
		self.hostname = val
		if self.state != ST_CREATED:
			self._setHostname()

	def modify_gateway4(self, val):
		self.gateway4 = val
		if self.state == ST_STARTED:
			self._setGateways()

	def modify_gateway6(self, val):
		self.gateway6 = val
		if self.state == ST_STARTED:
			self._setGateways()
	
	def modify_template(self, tmplName):
		self.template = template.get(self.TYPE, tmplName)
		if self.state == ST_PREPARED:
			self._useImage(self._template().getPath())

	def action_prepare(self):
		self._checkState()
		tplPath = self._template().getPath()
		if tplPath.endswith(".tar.gz"):
			tplPath = tplPath[:-len(".tar.gz")]
		tplPath = os.path.relpath(tplPath, "/var/lib/vz/template/cache") #calculate relative path to trick openvz
		imgPath = self._imagePath()
		if path.exists(imgPath):
			path.remove(imgPath, recursive=True)
		self._vzctl("create", ["--ostemplate", tplPath, "--config", "default"])
		self._vzctl("set", ["--devices", "c:10:200:rw", "--capability", "net_admin:on", "--save"])
		self.setState(ST_PREPARED, True) #must be here or the set commands fail
		self._setRam()
		self._setDiskspace()
		self._setRootpassword()
		self._setHostname()
		# add all interfaces
		for interface in self.getChildren():
			self._addInterface(interface)
		
	def action_destroy(self):
		self._checkState()
		self._vzctl("set", ["--hostname", "workaround", "--save"]) #Workaround for fault in vzctl 4.0-1pve6
		try:
			self._vzctl("destroy")
			self._vzctl("set", ["--hostname", self.hostname, "--save"]) #Workaround for fault in vzctl 4.0-1pve6
		except cmd.CommandError, exc:
			if exc.errorCode == 41: # [41] Container is currently mounted (umount first)
				self._vzctl("umount")
				self._vzctl("destroy")
			else:
				raise
		self.setState(ST_CREATED, True)

	def action_start(self):
		self._checkState()
		if not net.bridgeExists("dummy"):
			net.bridgeCreate("dummy")
		net.ifUp("dummy")
		self._vzctl("start") #not using --wait since this might hang
		self.setState(ST_STARTED, True)
		self._execute("while fgrep -q boot /proc/1/cmdline; do sleep 1; done")
		for interface in self.getChildren():
			ifName = self._interfaceName(interface.name)
			InternalError.check(util.waitFor(lambda :net.ifaceExists(ifName)), "Interface did not start properly",
				InternalError.ASSERTION, data={"interface": ifName})
			con = interface.getConnection()
			if con:
				con.connectInterface(self._interfaceName(interface.name))
			interface._start() #configure after connecting to allow dhcp, etc.
		self._setGateways()
		net.freeTcpPort(self.vncport)
		self.vncpid = cmd.spawnShell("while true; do vncterm -timeout 0 -rfbport %d -passwd %s -c bash -c 'while true; do vzctl enter %d; sleep 1; done'; sleep 1; done" % (self.vncport, self.vncpassword, self.vmid), useExec=False)
		InternalError.check(util.waitFor(lambda :net.tcpPortUsed(self.vncport)), InternalError.ASSERTION,
			"VNC server did not start")
		if not self.websocket_port:
			self.websocket_port = self.getResource("port")
		if websockifyVersion:
			net.freeTcpPort(self.websocket_port)
			self.websocket_pid = cmd.spawn(["websockify", "0.0.0.0:%d" % self.websocket_port, "localhost:%d" % self.vncport, '--cert=/etc/tomato/server.pem'])
			InternalError.check(util.waitFor(lambda :net.tcpPortUsed(self.websocket_port)),
				InternalError.ASSERTION, "Websocket VNC wrapper did not start")
				
	def action_stop(self):
		self._checkState()
		for interface in self.getChildren():
			con = interface.getConnection()
			if con:
				con.disconnectInterface(self._interfaceName(interface.name))
			interface._stop()
		if self.vncpid:
			process.killTree(self.vncpid)
			del self.vncpid
		if self.websocket_pid:
			process.killTree(self.websocket_pid)
			del self.websocket_pid
		self._vzctl("set", ["--hostname", "workaround", "--save"]) #Workaround for fault in vzctl 4.0-1pve6
		self._vzctl("stop")
		self._vzctl("set", ["--hostname", self.hostname, "--save"]) #Workaround for fault in vzctl 4.0-1pve6
		self.setState(ST_PREPARED, True)

	def action_upload_grant(self):
		return fileserver.addGrant(self.dataPath("uploaded.tar.gz"), fileserver.ACTION_UPLOAD)
	
	def action_rextfv_upload_grant(self):
		return fileserver.addGrant(self.dataPath("rextfv_up.tar.gz"), fileserver.ACTION_UPLOAD)
		
	def action_upload_use(self):
		UserError.check(os.path.exists(self.dataPath("uploaded.tar.gz")), UserError.NO_DATA_AVAILABLE, "No file has been uploaded")
		self._checkImage(self.dataPath("uploaded.tar.gz"))
		self._useImage(self.dataPath("uploaded.tar.gz"))
		
	def action_rextfv_upload_use(self):
		UserError.check(os.path.exists(self.dataPath("rextfv_up.tar.gz")), UserError.NO_DATA_AVAILABLE, "No file has been uploaded")
		self._use_rextfv_archive(self.dataPath("rextfv_up.tar.gz"))
		if self.state == ST_STARTED:
			try:
				self._execute("nlXTP_mon --background")
			except cmd.CommandError:
				return "Error executing nlXTP_mon"
		
	def action_download_grant(self):
		if os.path.exists(self.dataPath("download.tar.gz")):
			os.remove(self.dataPath("download.tar.gz"))
		cmd.run(["tar", "--numeric-owner", "-czvf", self.dataPath("download.tar.gz"), "-C", self._imagePath(), "."])
		return fileserver.addGrant(self.dataPath("download.tar.gz"), fileserver.ACTION_DOWNLOAD, removeFn=fileserver.deleteGrantFile)
	
	def action_rextfv_download_grant(self):
		self._create_rextfv_archive(self.dataPath("rextfv.tar.gz"))
		return fileserver.addGrant(self.dataPath("rextfv.tar.gz"), fileserver.ACTION_DOWNLOAD, removeFn=fileserver.deleteGrantFile)

	def action_execute(self, cmd):
		try:
			return self._execute(cmd)
		except CommandError, err:
			raise UserError(code=UserError.COMMAND_FAILED, message="Command failed", data={"code": err.errorCode, "message": err.errorMessage})

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info = joinDicts(info, elements.RexTFVElement.info(self))
		info["attrs"]["template"] = self.template.upcast().name if self.template else None
		return info

	def _cputime(self):
		if self.state != ST_STARTED:
			return None
		with open("/proc/vz/vestat") as fp:
			for line in fp:
				parts = line.split()
				if len(parts) < 4:
					continue
				veid, user, _, system = line.strip().split()[:4]
				if veid == str(self.vmid):
					break
		if veid == str(self.vmid):
			cputime = (int(user) + int(system))/process.jiffiesPerSecond()
		else: #pragma: no cover
			return None
		if self.vncpid and process.exists(self.vncpid):
			cputime += process.cputime(self.vncpid)
		return cputime
		
	def _memory(self):
		if self.state != ST_STARTED:
			return None
		with open("/proc/user_beancounters") as fp:
			for line in fp:
				if line.strip().startswith(str(self.vmid)):
					break
			if not line.strip().startswith(str(self.vmid)): #pragma: no cover
				return None
			for line in fp:
				key, val = line.split()[:2]
				if key == "privvmpages":
					memory = int(val) * 4096
					break
			if key != "privvmpages": #pragma: no cover
				return None
		if self.vncpid and process.exists(self.vncpid):
			memory += process.memory(self.vncpid)
		return memory
		
	def _diskspace(self):
		if self.state == ST_STARTED:
			with open("/proc/vz/vzquota") as fp:
				while True:
					line = fp.readline()
					if line.startswith(str(self.vmid)):
						break
				if not line.startswith(str(self.vmid)): #pragma: no cover
					return None
				return int(fp.readline().split()[1]) * 1024
		else:
			path.diskspace(self._imagePath())
		
	def updateUsage(self, usage, data):
		self._checkState()
		if self.state == ST_CREATED:
			return
		cputime = self._cputime()
		if cputime:
			usage.updateContinuous("cputime", cputime, data)
		memory = self._memory()
		if memory:
			usage.memory = memory
		diskspace = self._diskspace()
		if diskspace:
			usage.diskspace = diskspace
			
OpenVZ.__doc__ = DOC			


DOC_IFACE="""
Element type: ``openvz_interface``

Description:
	This element type represents a network interface of openvz element type. 
	Its	state is managed by and synchronized with the parent element.

Possible parents: ``openvz``

Possible children: None

Default state: *created*

Removable in states: *created* and *prepared* 

Connection concepts: *interface*

States:
	*created*: In this state the interface is known of but vzctl does not know
		about it.
	*prepared*: In this state the interface is present in the vzctl configuration
		but not running.
	*started*: In this state the interface is running.
		
Attributes:
	*ip4address*, str, changeable in all states
		The IPv4 address and prefix length to configure the interface with. The
		address must be in the format address/prefix_length where address is a
		valid IPv4 address and prefix_length is a number from 0 to 32.
		(Example: 10.0.0.1/24)
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux.
	*ip6address*, str, changeable in all states
		The IPv6 address and prefix length to configure the interface with. The
		address must be in the format address/prefix_length where address is a
		valid IPv6 address and prefix_length is a number from 0 to 128.
		(Example: fd1a:8807:b8ad:ebbe::/64)
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux.
	*use_dhcp*, bool, changeable in all states
		Whether to start a dhcp client to configure the interface. If use_dhcp
		is set to True, a dhcp configuration will be attempted AFTER 
		configuring the interface with the given addresses.
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux. This means that the operating system must
		either provide /sbin/dhclient or /sbin/dhcpcd.

Actions: None
"""

class OpenVZ_Interface(elements.Element):
	name_attr = Attr("name", desc="Name", type="str", regExp="^eth[0-9]+$", states=[ST_CREATED])
	name = name_attr.attribute()
	ip4address_attr = Attr("ip4address", desc="IPv4 address", type="str")
	ip4address = ip4address_attr.attribute()	
	ip6address_attr = Attr("ip6address", desc="IPv6 address", type="str")
	ip6address = ip6address_attr.attribute()		
	use_dhcp_attr = Attr("use_dhcp", desc="Use DHCP", type="bool", default=False)
	use_dhcp = use_dhcp_attr.attribute()		
	mac_attr = Attr("mac", desc="MAC Address", type="str")
	mac = mac_attr.attribute()
	ipspy_pid_attr = Attr("ipspy_pid", type="int")
	ipspy_pid = ipspy_pid_attr.attribute()
	used_addresses_attr = Attr("used_addresses", type=list, default=[])
	used_addresses = used_addresses_attr.attribute()

	TYPE = "openvz_interface"
	CAP_ACTIONS = {
		elements.REMOVE_ACTION: [ST_CREATED, ST_PREPARED]
	}
	CAP_NEXT_STATE = {}	
	CAP_ATTRS = {
		"name": name_attr,
		"ip4address": ip4address_attr,
		"ip6address": ip6address_attr,
		"use_dhcp": use_dhcp_attr,
		"timeout": elements.Element.timeout_attr
	}
	CAP_CHILDREN = {}
	CAP_PARENT = [OpenVZ.TYPE]
	CAP_CON_CONCEPTS = [connections.CONCEPT_INTERFACE]
	DOC = DOC_IFACE
	__doc__ = DOC_IFACE #@ReservedAssignment
	
	class Meta:
		db_table = "tomato_openvz_interface"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		assert isinstance(self.getParent(), OpenVZ)
		if not self.name:
			self.name = self.getParent()._nextIfaceName()
		self.mac = net.randomMac()
		
	def _execute(self, cmd):
		return self.getParent()._execute(cmd)
		
	def _setAddresses(self):
		assert self.state == ST_STARTED
		if not self.use_dhcp:
			self._execute("ip addr flush dev %s" % self.name)
		if self.ip4address:
			self._execute("ip addr add %s dev %s" % (self.ip4address, self.name))		
		if self.ip6address:
			self._execute("ip addr add %s dev %s" % (self.ip6address, self.name))

	def _setUseDhcp(self):
		assert self.state == ST_STARTED
		if not self.use_dhcp:
			return
		for cmd_ in DHCP_CMDS:
			try:
				return self._execute(cmd_ % self.name)
			except cmd.CommandError, err:
				if err.errorCode != 8:
					return

	def modify_ip4address(self, val):
		self.ip4address = val
		if self.state == ST_STARTED:
			self._setAddresses()

	def modify_ip6address(self, val):
		self.ip6address = val
		if self.state == ST_STARTED:
			self._setAddresses()

	def modify_use_dhcp(self, val):
		self.use_dhcp = val
		if self.state == ST_STARTED:
			self._setUseDhcp()
	
	def modify_name(self, val):
		self.name = val
	
	def _start(self):
		self.ipspy_pid = net.ipspy_start(self.interfaceName(), self.dataPath("ipspy.json"))
		self.save()
		self._setAddresses()
		self._setUseDhcp()
		self._execute("ip link set up %s" % self.name)			
	
	def _stop(self):
		if self.ipspy_pid:
			process.kill(self.ipspy_pid)
			del self.ipspy_pid
		self.save()
	
	def interfaceName(self):
		if self.state != ST_CREATED:
			return self.getParent()._interfaceName(self.name)
		else:
			return None		
		
	def upcast(self):
		return self

	def info(self):
		if self.state == ST_STARTED:
			self.used_addresses = net.ipspy_read(self.dataPath("ipspy.json"))
		else:
			self.used_addresses = []
		info = elements.Element.info(self)
		return info

	def updateUsage(self, usage, data):
		ifname = self.interfaceName()
		if net.ifaceExists(ifname):
			traffic = sum(net.trafficInfo(ifname))
			usage.updateContinuous("traffic", traffic, data)
			
OpenVZ_Interface.__doc__ = DOC_IFACE

def register(): #pragma: no cover
	if not os.path.exists("/dev/vzctl"):
		print >>sys.stderr, "Warning: OpenVZ needs /dev/vzctl, disabled"
		return	
	if not vzctlVersion:
		print >>sys.stderr, "Warning: OpenVZ needs a Proxmox VE host, disabled"
		return
	if not ([3, 0, 30] <= vzctlVersion < [4, 1]):
		print >>sys.stderr, "Warning: OpenVZ not supported on vzctl version %s, disabled" % vzctlVersion
		return
	if not vnctermVersion:
		print >>sys.stderr, "Warning: OpenVZ needs vncterm, disabled"
		return
	if not perlVersion:
		print >>sys.stderr, "Warning: OpenVZ needs perl, disabled"
		return
	if not ipspyVersion:
		print >>sys.stderr, "Warning: ipspy not available"
	elements.TYPES[OpenVZ.TYPE] = OpenVZ
	elements.TYPES[OpenVZ_Interface.TYPE] = OpenVZ_Interface


if not config.MAINTENANCE:
	perlVersion = cmd.getDpkgVersion("perl")
	vzctlVersion = cmd.getDpkgVersion("vzctl")
	vnctermVersion = cmd.getDpkgVersion("vncterm")
	websockifyVersion = cmd.getDpkgVersion("websockify")
	ipspyVersion = cmd.getDpkgVersion("ipspy")
	register()
