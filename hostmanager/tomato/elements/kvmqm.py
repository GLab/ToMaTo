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

import os, sys, json
from django.db import models
from tomato import connections, elements, resources, config, host, fault
from tomato.lib.attributes import attribute
from tomato.lib import decorators, util

class KVMQM(elements.Element):
	path = attribute("path", str)
	vmid = attribute("vmid", int)
	vncport = attribute("vncport", int)
	vncpid = attribute("vncpid", int)
	cpus = attribute("cpus", int)
	ram = attribute("ram", int)
	kblang = attribute("kblang", str)
	usbtablet = attribute("usbtablet", bool)
	vncpassword = attribute("vncpassword", str)
	template = models.ForeignKey(resources.Resource, null=True)

	ST_CREATED = "created"
	ST_PREPARED = "prepared"
	ST_STARTED = "started"
	TYPE = "kvmqm"
	CAP_ACTIONS = {
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		"start": [ST_PREPARED],
		"stop": [ST_STARTED],
		"__remove__": [ST_CREATED],
	}
	CAP_ATTRS = {
		"cpus": [ST_CREATED, ST_PREPARED],
		"ram": [ST_CREATED, ST_PREPARED],
		"kblang": [ST_CREATED, ST_PREPARED],
		"usbtablet": [ST_CREATED, ST_PREPARED],
		"template": [ST_CREATED, ST_PREPARED],
	}
	CAP_CHILDREN = {
		"kvmqm_interface": [ST_CREATED, ST_PREPARED],
	}
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {"cpus": 1, "ram": 256, "kblang": "de", "usbtablet": True}
	
	class Meta:
		db_table = "tomato_kvmqm"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = self.ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		self.path = os.path.join(config.DATA_DIR, "kvmqm", str(self.id))
		if not os.path.exists(self.path):
			os.makedirs(self.path)
		self.vmid = self.getResource("vmid")
		self.vncport = self.getResource("port")
		self.vncpassword = host.randomPassword()
		#template: None, default template
				
	def _controlPath(self):
		return "/var/run/qemu-server/%d.qmp" % self.vmid
				
	def _vncPath(self):
		return "/var/run/qemu-server/%d.vnc" % self.vmid

	def _vncPidfile(self):
		return os.path.join(self.path, "vnc.pid")

	def _imagePathDir(self):
		return "/var/lib/vz/images/%d" % self.vmid

	def _imagePath(self):
		return self._imagePathDir() + "/disk.qcow2"

	def _interfaceName(self, num):
		if qmVersion == [1, 1, 22]:
			return "vmtab%di%d" % (self.vmid, num)
		if qmVersion == [1, 1, 25]:
			return "vmtab%di%dd0" % (self.vmid, num)
		return "tap%di%d" % (self.vmid, num)

	@decorators.retryOnError(errorFilter=lambda x: isinstance(x, host.CommandError) and x.errorCode==4 and "lock" in x.errorMessage and "timeout" in x.errorMessage)
	def _qm(self, cmd, params=[]):
		return host.run(["qm", cmd, str(self.vmid)] + map(str, params))
		#fileutil.delete(host, "/var/lock/qemu-server/lock-%d.conf" % vmid)

	def _getState(self):
		try:
			res = self._qm("status")
			if "running" in res:
				return self.ST_STARTED
			if "stopped" in res:
				return self.ST_PREPARED
			if "unknown" in res:
				return self.ST_CREATED
			fault.raise_("Unable to determine kvm state", fault.INTERNAL_ERROR)
		except host.CommandError, err:
			if err.errorCode == 2:
				return self.ST_CREATED

	def _control(self, cmds, timeout=60):
		assert self.state == self.ST_STARTED, "VM must be running"
		controlPath = self._controlPath()
		fault.check(os.path.exists(controlPath), "Control path does not exist")
		cmd = "".join([host.escape(json.dumps(cmd))+"'\n'" for cmd in cmds])
		return host.runShell("echo -e %(cmd)s'\n' | socat -T %(timeout)d - unix-connect:%(monitor)s; socat -T %(timeout)d -u unix-connect:%(monitor)s - 2>&1 | dd count=0 2>/dev/null; echo" % {"cmd": cmd, "monitor": controlPath, "timeout": timeout})
			
	def _template(self):
		if self.template:
			return self.template
		pref = resources.template.get(self.TYPE, resources.template.getPreferred(self.TYPE))
		fault.check(pref, "Failed to find template for %s", self.TYPE, fault.INTERNAL_ERROR)
		return pref
				
	def _nextIfaceNum(self):
		ifaces = self.getChildren()
		num = 0
		while num in [iface.num for iface in ifaces]:
			num += 1
		return num

	def onChildAdded(self, interface):
		if self.state == self.ST_PREPARED:
			self._qm("set", ["-net%d" % interface.num, "e1000,bridge=dummy"])

	def onChildRemoved(self, interface):
		if self.state == self.ST_PREPARED:
			self._qm("set", ["-delete", "net%d" % interface.num])

	def modify_cpus(self, cpus):
		self.cpus = cpus
		self._qm("set", ["-cores", self.cpus])

	def modify_ram(self, ram):
		self.ram = ram
		self._qm("set", ["-memory", self.ram])
		
	def modify_kblang(self, kblang):
		self.kblang = kblang
		self._qm("set", ["-keyboard", self.kblang])
		
	def modify_usbtablet(self, usbtablet):
		self.usbtablet = usbtablet
		self._qm("set", ["-tablet", int(self.usbtablet)])
		
	def modify_template(self, tmplName):
		self.template = resources.template.get(self.TYPE, tmplName)
		#FIXME: use template

	def action_prepare(self):
		self._qm("create", ["-cores", self.cpus, "-memory", self.ram, "-keyboard", self.kblang, "-tablet", int(self.usbtablet)])
		self._qm("set", ["-args", "-vnc unix:%s,password" % self._vncPath()])
		# add all interfaces
		for interface in self.getChildren():
			self._qm("set", ["-net%d" % interface.num, "e1000,bridge=dummy"])
		# use template
		tpl = self._template()
		img = host.Path(tpl.getPath())
		img.copyTo(self._imagePath())
		self._qm("set", ["-ide0", "local:%d/disk.qcow2" % self.vmid])
		self.setState(self.ST_PREPARED, True)
		
	def action_destroy(self):
		self._qm("destroy")
		self.setState(self.ST_CREATED, True)

	def action_start(self):
		self._qm("start")
		self.setState(self.ST_STARTED, True)
		for interface in self.getChildren():
			ifObj = host.Interface(self._interfaceName(interface.num))
			util.waitFor(ifObj.exists)
			con = interface.getConnection()
			if con:
				con.connectInterface(self._interfaceName(interface.num))
		util.waitFor(lambda :os.path.exists(self._controlPath()))
		self._control([{'execute': 'qmp_capabilities'}, {'execute': 'set_password', 'arguments': {"protocol": "vnc", "password": self.vncpassword}}])
		self.vncpid = host.spawn(["tcpserver", "-qHRl", "0",  "0", str(self.vncport), "qm", "vncproxy", str(self.vmid)])

	def action_stop(self):
		for interface in self.getChildren():
			con = interface.getConnection()
			if con:
				con.disconnectInterface(self._interfaceName(interface.num))
		if self.vncpid:
			host.kill(self.vncpid)
			del self.vncpid
		self._qm("shutdown", ["-timeout", 10, "-forceStop"])
		self.setState(self.ST_PREPARED, True)
		
	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["template"] = self.template.name if self.template else None
		return info


class KVMQM_Interface(elements.Element):
	num = attribute("num", int)

	TYPE = "kvmqm_interface"
	CAP_ACTIONS = {
		"__remove__": [KVMQM.ST_CREATED, KVMQM.ST_PREPARED]
	}
	CAP_ATTRS = {
		"name": [KVMQM.ST_CREATED, KVMQM.ST_PREPARED]
	}
	CAP_CHILDREN = {}
	CAP_PARENT = [KVMQM.TYPE]
	CAP_CON_PARADIGMS = [connections.PARADIGM_INTERFACE]
	
	class Meta:
		db_table = "tomato_kvm_interface"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = KVMQM.ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		assert isinstance(self.parent, KVMQM)
		self.num = self.parent._nextIfaceNum()
		
	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["num"] = self.num
		return info


tcpserverVersion = host.getDpkgVersion("ucspi-tcp")
socatVersion = host.getDpkgVersion("socat")
qmVersion = host.getDpkgVersion("pve-qemu-kvm")

def register():
	if not qmVersion:
		print >>sys.stderr, "Warning: KVMQM needs a Proxmox VE host, disabled"
		return
	if not ([0, 15, 0] <= qmVersion < [1, 2]):
		print >>sys.stderr, "Warning: KVMQM not supported on pve-qemu-kvm version %s, disabled" % qmVersion
		return
	if not socatVersion:
		print >>sys.stderr, "Warning: KVMQM needs socat, disabled"
		return
	if not tcpserverVersion:
		print >>sys.stderr, "Warning: KVMQM needs ucspi-tcp, disabled"
		return
	elements.TYPES[KVMQM.TYPE] = KVMQM
	elements.TYPES[KVMQM_Interface.TYPE] = KVMQM_Interface

register()
