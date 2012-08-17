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

import os, sys
from django.db import models
from tomato import connections, elements, resources, host, fault
from tomato.lib.attributes import attribute
from tomato.lib import decorators, util
from tomato.host import fileserver

DOC="""
Element type: openvz

Description:
	This element type provides container virtualization by using the OpenVZ 
	virtualization technology. The proxmox frontend vzctl is used to control
	OpenVZ.

Possible parents: None

Possible children:
	openvz_interface (can be added in states created and prepared)

Default state: created

Removable in states: created

Connection paradigms: None

States:
	created: In this state the VM is known of but vzctl does not know about it.
		No state is stored and no resources are consumed in this state.
	prepared: In this state the VM is present in the vzctl configuration and 
		the disk image exists but the VM is not running. The disk image stores 
		some state information. The VM is not consuming any resources except 
		for the	disk image.
	started: In this state the VM is running and can be accessed by the user.
		The VM holds a disk state and a memory state. It consumes disk storage
		memory, cpu power, io and networking resources.
		
Attributes:
	ram: int, changeable in all states, default: 256
		The amount of memory the VM should have in megabytes. The virtual
		machine will only be able to access this much virtual memory. The RAM
		used by the VM will match the RAM usage inside the VM.
	diskspace: int, changeable in all states, default: 10240
		The amount of disk space, the VM should have in megabytes. The virtual
		machine will only be able to access this much disk space. The disk 
		space used by the VM will match the disk usage inside the VM.
	rootpassword: str, changeable in all states
		The password of the user 'root' inside the VM.
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux.
	hostname, str, changeable in all states
		The hostname as seen inside the VM.
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux.
	gateway4, str, changeable in all states
		The IPv4 default route to be used inside the VM. The route must be a 
		valid IPv4 address.
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux.
	gateway6, str, changeable in all states
		The IPv6 default route to be used inside the VM. The route must be a 
		valid IPv6 address.
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux.
	template: str, changeable in states created and prepared
		The name of a template of matching virtualization technology to be used
		for this VM. A copy of this template will be used as an initial disk 
		image when the device is being prepared. When this attribute is changed
		in the state prepared, the disk image will be reset to the template.
		If no template with the given name exists (esp. for template=None),
		a default template is chosen instead.
		WARNING: Setting this attribute for a prepared VM will cause the loss
		of the disk image.
	vncport: int, read-only
		The port on this host on which the VM can be accessed via VNC when it
		is running. 
	vncpassword: int, read-only
		The random password that has to be used to connect to this VM using 
		VNC. This password should be kept secret.

Actions:
	prepare, callable in state created, next state: prepared
		Creates a vzctl configuration entry for this VM and uses a copy of
		the	template as disk image.
	destroy, callable in state prepared, next state: created
	 	Removes the vzctl configuration entry and deletes the disk image.
	start, callable in state prepared, next state: started
	 	Starts the VM and initiates a boot of the contained OS. This action
	 	also starts a VNC server for the VM and connects all the interfaces
	 	of the device.
	stop, callable in state started, next state: prepared
	 	Stops the VNC server, disconnects all the interfaces of the VM and
	 	then initiates an OS shutdown using the runlevel system.
	upload_grant, callable in state prepared
	 	Create/update a grant to upload an image for the VM. The created grant
	 	will be available as an attribute called upload_grant. The grant allows
	 	the user to upload a file for a certain time. The url where the file 
	 	must be uploaded has the form http://server:port/grant/upload where
	 	server is the address of this host, port is the fileserver port of this
	 	server (can be requested via host_info) and grant is the grant.
	 	The uploaded file can be used as the VM image with the upload_use 
	 	action. 
	upload_use, callable in state prepared
		Uses a previously uploaded file as the image of the VM. 
	download_grant, callable in state prepared
	 	Create/update a grant to download the image for the VM. The created 
	 	grant will be available as an attribute called download_grant. The
	 	grant allows the user to download the VM image once for a certain time.
	 	The url where the file can be downloaded from has the form 
	 	http://server:port/grant/download where server is the address of this
	 	host, port is the fileserver port of this server (can be requested via
	 	host_info) and grant is the grant.
"""

class OpenVZ(elements.Element):
	vmid = attribute("vmid", int)
	vncport = attribute("vncport", int)
	vncpid = attribute("vncpid", int)
	vncpassword = attribute("vncpassword", str)	
	ram = attribute("ram", int)
	diskspace = attribute("diskspace", int)
	rootpassword = attribute("rootpassword", str)	
	hostname = attribute("hostname", str)	
	gateway4 = attribute("gateway4", str)	
	gateway6 = attribute("gateway6", str)	
	upload_grant = attribute("upload_grant", str)
	download_grant = attribute("download_grant", str)	
	template = models.ForeignKey(resources.Resource, null=True)

	ST_CREATED = "created"
	ST_PREPARED = "prepared"
	ST_STARTED = "started"
	TYPE = "openvz"
	CAP_ACTIONS = {
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		"start": [ST_PREPARED],
		"stop": [ST_STARTED],
		"upload_grant": [ST_PREPARED],
		"upload_use": [ST_PREPARED],
		"download_grant": [ST_PREPARED],
		"__remove__": [ST_CREATED],
	}
	CAP_NEXT_STATE = {
		"prepare": ST_PREPARED,
		"destroy": ST_CREATED,
		"start": ST_STARTED,
		"stop": ST_PREPARED,
	}	
	CAP_ATTRS = {
		"ram": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"diskspace": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"rootpassword": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"hostname": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"gateway4": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"gateway6": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"template": [ST_CREATED, ST_PREPARED],
	}
	CAP_CHILDREN = {
		"openvz_interface": [ST_CREATED, ST_PREPARED],
	}
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {"ram": 256, "diskspace": 10240}
	
	class Meta:
		db_table = "tomato_openvz"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = self.ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		self.vmid = self.getResource("vmid")
		self.vncport = self.getResource("port")
		self.vncpassword = host.randomPassword()
		#template: None, default template
	
	def _imagePath(self):
		return "/var/lib/vz/private/%d" % self.vmid

	@decorators.retryOnError(errorFilter=lambda x: isinstance(x, host.CommandError) and x.errorCode==9 and "Container already locked" in x.errorMessage)
	def _vzctl(self, cmd, args=[], timeout=None):
		cmd = ["vzctl", cmd, str(self.vmid)] + args
		if timeout:
			cmd = ["perl", "-e", "'alarm %d; exec @ARGV'" % timeout] + cmd
		return host.run(cmd)
			
	def _execute(self, cmd, timeout=60):
		assert self.state == self.ST_STARTED
		self._vzctl("exec", [cmd], timeout=timeout)
			
	def _getState(self):
		res = self._vzctl("status")
		if "exist" in res and "running" in res:
			return self.ST_STARTED
		if "exist" in res and "down" in res:
			return self.ST_PREPARED
		if "deleted" in res:
			return self.ST_CREATED
		fault.raise_("Unable to determine openvz state", fault.INTERNAL_ERROR)

	def _checkState(self):
		savedState = self.state
		realState = self._getState()
		if savedState != realState:
			self.setState(realState, True)
		fault.check(savedState == realState, "Saved state of %s element #%d was wrong, saved: %s, was: %s", (self.type, self.id, savedState, realState), fault.INTERNAL_ERROR)

	def _template(self):
		if self.template:
			return self.template
		pref = resources.template.getPreferred(self.TYPE)
		fault.check(pref, "Failed to find template for %s", self.TYPE, fault.INTERNAL_ERROR)
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
		assert self.state != self.ST_CREATED
		self._vzctl("set", ["--netif_add", interface.name, "--save"])
		self._vzctl("set", ["--ifname", interface.name, "--host_ifname", self._interfaceName(interface.name), "--save"])
		
	def _removeInterface(self, interface):
		assert self.state != self.ST_CREATED
		self._vzctl("set", ["--netif_del", interface.name, "--save"])
		
	def _setRam(self):
		assert self.state != self.ST_CREATED
		val = "%dM" % int(self.ram)
		self._vzctl("set", ["--vmguarpages", val, "--privvmpages", val, "--save"])
	
	def _setDiskspace(self):
		assert self.state != self.ST_CREATED
		val = "%dM" % int(self.ram)
		self._vzctl("set", ["--diskspace", val, "--save"])

	def _setRootpassword(self):
		assert self.state != self.ST_CREATED
		if self.rootpassword:
			self._vzctl("set", ["--userpasswd", "root:%s" % self.rootpassword, "--save"])

	def _setHostname(self):
		assert self.state != self.ST_CREATED
		if self.hostname:
			self._vzctl("set", ["--hostname", self.hostname, "--save"])

	def _setGateways(self):
		assert self.state == self.ST_STARTED
		self._execute("ip route del default")
		if self.gateway4:
			self._execute("ip route add default via %s" % self.gateway4)
		if self.gateway6:
			self._execute("ip route add default via %s" % self.gateway6)

	def _useImage(self, path):
		assert self.state != self.ST_CREATED
		imgPath = host.Path(self._imagePath())
		archive = host.Archive(path)
		imgPath.remove(recursive=True)
		imgPath.createDir()
		archive.extractTo(imgPath)

	def _checkImage(self, path):
		res = host.run(["tar", "-tzvf", path, "./sbin/init"])
		fault.check("0/0" in res, "Image contents not owned by root")

	def onChildAdded(self, interface):
		self._checkState()
		if self.state == self.ST_PREPARED:
			self._addInterface(interface)

	def onChildRemoved(self, interface):
		self._checkState()
		if self.state == self.ST_PREPARED:
			self._removeInterface(interface)

	def modify_ram(self, val):
		self.ram = val
		if self.state != self.ST_CREATED:
			self._setRam()
		
	def modify_diskspace(self, val):
		self.diskspace = val
		if self.state != self.ST_CREATED:
			self._setDiskspace()

	def modify_rootpassword(self, val):
		self.rootpassword = val
		if self.state != self.ST_CREATED:
			self._setRootpassword()
	
	def modify_hostname(self, val):
		self.hostname = val
		if self.state != self.ST_CREATED:
			self._setHostname()

	def modify_gateway4(self, val):
		self.gateway4 = val
		if self.state == self.ST_STARTED:
			self._setGateways()

	def modify_gateway6(self, val):
		self.gateway6 = val
		if self.state == self.ST_STARTED:
			self._setGateways()
	
	def modify_template(self, tmplName):
		self.template = resources.template.get(self.TYPE, tmplName)
		self._useImage(self._template().getPath())

	def action_prepare(self):
		self._checkState()
		self._vzctl("create", ["--ostemplate", self._template().name, "--config", "default"])
		self._vzctl("set", ["--devices", "c:10:200:rw", "--capability", "net_admin:on", "--save"])
		self.setState(self.ST_PREPARED, True) #must be here or the set commands fail
		self._setRam()
		self._setDiskspace()
		self._setRootpassword()
		self._setHostname()
		# add all interfaces
		for interface in self.getChildren():
			self._addInterface(interface)
		
	def action_destroy(self):
		self._checkState()
		self._vzctl("destroy")
		self.setState(self.ST_CREATED, True)

	def action_start(self):
		self._checkState()
		self._vzctl("start") #not using --wait since this might hang
		self.setState(self.ST_STARTED, True)
		self._execute("while fgrep -q boot /proc/1/cmdline; do sleep 1; done")
		for interface in self.getChildren():
			ifObj = host.Interface(self._interfaceName(interface.name))
			util.waitFor(ifObj.exists)
			con = interface.getConnection()
			if con:
				con.connectInterface(self._interfaceName(interface.name))
			interface._configure() #configure after connecting to allow dhcp, etc.
		self._setGateways()
		self.vncpid = host.spawnShell("vncterm -timeout 0 -rfbport %d -passwd %s -c bash -c 'while true; do vzctl enter %d; done'" % (self.vncport, self.vncpassword, self.vmid))
				
	def action_stop(self):
		self._checkState()
		for interface in self.getChildren():
			con = interface.getConnection()
			if con:
				con.disconnectInterface(self._interfaceName(interface.name))
		if self.vncpid:
			host.kill(self.vncpid)
			del self.vncpid
		self._vzctl("stop")
		self.setState(self.ST_PREPARED, True)

	def action_upload_grant(self):
		self.upload_grant = fileserver.addGrant(self.dataPath("uploaded.tar.gz"), fileserver.ACTION_UPLOAD)
		
	def action_upload_use(self):
		fault.check(os.path.exists(self.dataPath("uploaded.tar.gz")), "No file has been uploaded")
		self._checkImage(self.dataPath("uploaded.tar.gz"))
		arch = host.Archive(self.dataPath("uploaded.tar.gz"))
		imgDir = host.Path(self._imagePath())
		imgDir.remove(recursive=True)
		imgDir.createDir() 
		arch.extractTo(imgDir)
		
	def action_download_grant(self):
		if os.path.exists(self.dataPath("download.tar.gz")):
			os.remove(self.dataPath("download.tar.gz"))
		host.run(["tar", "--numeric-owner", "-czvf", self.dataPath("download.tar.gz"), "-C", self._imagePath(), "."])
		self.download_grant = fileserver.addGrant(self.dataPath("download.tar.gz"), fileserver.ACTION_DOWNLOAD, removeFn=fileserver.deleteGrantFile)

	def _relPath(self, file_):
		assert self.path
		return os.path.join(self.path, file_)

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["template"] = self.template.name if self.template else None
		return info


DOC_IFACE="""
Element type: openvz_interface

Description:
	This element type represents a network interface of openvz element type. 
	Its	state is managed by and synchronized with the parent element.

Possible parents: openvz

Possible children: None

Default state: created

Removable in states: created and prepared 

Connection paradigms: interface

States:
	created: In this state the interface is known of but vzctl does not know
		about it.
	prepared: In this state the interface is present in the vzctl configuration
		but not running.
	started: In this state the interface is running.
		
Attributes:
	ip4address, str, changeable in all states
		The IPv4 address and prefix length to configure the interface with. The
		address must be in the format address/prefix_length where address is a
		valid IPv4 address and prefix_length is a number from 0 to 32.
		(Example: 10.0.0.1/24)
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux.
	ip6address, str, changeable in all states
		The IPv6 address and prefix length to configure the interface with. The
		address must be in the format address/prefix_length where address is a
		valid IPv6 address and prefix_length is a number from 0 to 128.
		(Example: fd1a:8807:b8ad:ebbe::/64)
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux.
	use_dhcp, bool, changeable in all states
		Whether to start a dhcp client to configure the interface. If use_dhcp
		is set to True, a dhcp configuration will be attempted AFTER 
		configuring the interface with the given addresses.
		Note: This setting can only be changed if the operating system inside
		the VM is a standard linux. This means that the operating system must
		either provide /sbin/dhclient or /sbin/dhcpcd.

Actions: None
"""

class OpenVZ_Interface(elements.Element):
	name = attribute("name", str)
	ip4address = attribute("ip4address", str)
	ip6address = attribute("ip6address", str)
	use_dhcp = attribute("use_dhcp", bool)

	TYPE = "openvz_interface"
	CAP_ACTIONS = {
		"__remove__": [OpenVZ.ST_CREATED, OpenVZ.ST_PREPARED]
	}
	CAP_NEXT_STATE = {}	
	CAP_ATTRS = {
		"ip4address": [OpenVZ.ST_CREATED, OpenVZ.ST_PREPARED, OpenVZ.ST_STARTED],
		"ip6address": [OpenVZ.ST_CREATED, OpenVZ.ST_PREPARED, OpenVZ.ST_STARTED],
		"use_dhcp": [OpenVZ.ST_CREATED, OpenVZ.ST_PREPARED, OpenVZ.ST_STARTED],
	}
	CAP_CHILDREN = {}
	CAP_PARENT = [OpenVZ.TYPE]
	CAP_CON_PARADIGMS = [connections.PARADIGM_INTERFACE]
	
	class Meta:
		db_table = "tomato_openvz_interface"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = OpenVZ.ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		assert isinstance(self.getParent(), OpenVZ)
		if not self.name:
			self.name = self.getParent()._nextIfaceName()
		
	def _execute(self, cmd):
		return self.getParent()._execute(cmd)
		
	def _setIp4Address(self):
		assert self.state == OpenVZ.ST_STARTED
		if self.ip4address:
			self._execute("ip addr add %s dev %s" % (self.ip4address, self.name))
		
	def _setIp6Address(self):
		assert self.state == OpenVZ.ST_STARTED
		if self.ip6address:
			self._execute("ip addr add %s dev %s" % (self.ip6address, self.name))

	def _setUseDhcp(self):
		assert self.state == OpenVZ.ST_STARTED
		if not self.use_dhcp:
			return
		for cmd in ["/sbin/dhclient", "/sbin/dhcpcd"]:
			try:
				return self._execute("[ -e %s ] && %s %s" % (cmd, cmd, self.name))
			except host.CommandError, err:
				if err.errorCode != 8:
					return

	def modify_ip4address(self, val):
		self.ip4address = val
		if self.state == OpenVZ.ST_STARTED:
			self._setIp4Address()

	def modify_ip6address(self, val):
		self.ip6address = val
		if self.state == OpenVZ.ST_STARTED:
			self._setIp6Address()

	def modify_use_dhcp(self, val):
		self.use_dhcp = val
		if self.state == OpenVZ.ST_STARTED:
			self._setUseDhcp()
	
	def _configure(self):
		self._setIp4Address()
		self._setIp6Address()
		self._setUseDhcp()
	
	def interfaceName(self):
		if self.state == OpenVZ.ST_STARTED:
			return self.getParent()._interfaceName(self.name)
		else:
			return None		
		
	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		return info


perlVersion = host.getDpkgVersion("perl")
vzctlVersion = host.getDpkgVersion("vzctl")
vnctermVersion = host.getDpkgVersion("vncterm")

def register():
	if not vzctlVersion:
		print >>sys.stderr, "Warning: OpenVZ needs a Proxmox VE host, disabled"
		return
	if not ([3] <= vzctlVersion < [4]):
		print >>sys.stderr, "Warning: OpenVZ not supported on vzctl version %s, disabled" % vzctlVersion
		return
	if not vnctermVersion:
		print >>sys.stderr, "Warning: OpenVZ needs vncterm, disabled"
		return
	if not perlVersion:
		print >>sys.stderr, "Warning: OpenVZ needs perl, disabled"
		return
	elements.TYPES[OpenVZ.TYPE] = OpenVZ
	elements.TYPES[OpenVZ_Interface.TYPE] = OpenVZ_Interface

register()