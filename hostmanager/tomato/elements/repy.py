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

import os, sys, shutil
from ..db import *
from ..generic import *
from .. import connections, elements, config
from ..resources import template
from ..lib.attributes import Attr #@UnresolvedImport
from ..lib import util, cmd #@UnresolvedImport
from ..lib.cmd import fileserver, process, net, path #@UnresolvedImport
from ..lib.error import UserError, InternalError
from ..lib.constants import ActionName, StateName, TypeName

DOC="""
Element type: ``repy``

Description:
	This element type provides programming language virtualization by using the
	Repy python sandbox. An adapted version of the original Seattle Repy that
	can read and write ethernet packets is used. See :doc:`/docs/repy` for more
	information about Repy.

Possible parents: None

Possible children:
	``repy_interface`` (can be added in state *created*)

Default state: *prepared*

Removable in states: *prepared*

Connection concepts: None

States:
	*prepared*: In this state the program is known of and the script exists.
		Only the script is stored and no othe resources are consumed in this
		state.
	*started*: In this state the program is running and can be accessed by the
		user. The program holds a memory state but no disk state. It consumes
		memory, cpu power, io and networking resources.
		
Attributes:
	*args*: list, changeable in state *created*, default: ``[]``
		The arguments to pass to the program when it is started.
	*cpus*: float, changeable in state *created*, default: ``0.25``
		The number of processors that the program can use. This can be set to a
		fraction to limit the program to that fraction of the processor. If 
		this value is greater than 1.0 the program is allowed to use the 
		resources of more than one processor using several threads.
	*ram*: int, changeable in state *created*, default: ``25``
		The amount of memory the program should have in megabytes. The program
		will only be able to use this much memory for its data structures. If
		the program tries to use more, this will result in exceptions and/or
		the program being terminated.
	*bandwidth*: int, changeable in state *created*, default: ``1000000``
		The amount of traffic that the program is allowed to cause in bytes per
		second. All the incoming and the outgoing traffic of all interface is
		counted against this value but the limit is applied seperately for 
		incoming and outgoing traffic. The limit is only applied on a per 
		second basis, i.e. short bursts can go over this limit.
	*template*: str, changeable in state *created*
		The name of a template of matching virtualization technology to be used
		for this program. A copy of this template will be used as the script 
		for this program. If no template with the given name exists (esp. for
		template=None), a default template is chosen instead.
	*vncport*: int, read-only
		The port on this host on which the VM can be accessed via VNC when it
		is running. 
	*vncpassword*: int, read-only
		The random password that has to be used to connect to this VM using 
		VNC. This password should be kept secret.

Actions:
	*start*, callable in state *created*, next state: *started*
	 	Starts the program and runs the script, and starts a VNC server that
	 	displays the output of the script. This action also connects all the
	 	interfaces of the device.
	*stop*, callable in state *started*, next state: *created*
	 	Stops the VNC server and then stops the program.
	*upload_grant*, callable in state *created*
	 	Create/update a grant to upload an image for the VM. The created grant
	 	will be available as an attribute called upload_grant. The grant allows
	 	the user to upload a file for a certain time. The url where the file 
	 	must be uploaded has the form http://server:port/grant/upload where
	 	server is the address of this host, port is the fileserver port of this
	 	server (can be requested via host_info) and grant is the grant.
	 	The uploaded file can be used as the VM image with the upload_use 
	 	action. 
	*upload_use*, callable in state *created*
		Uses a previously uploaded file as the image of the VM. 
	*download_grant*, callable in state *created*
	 	Create/update a grant to download the image for the VM. The created 
	 	grant will be available as an attribute called download_grant. The
	 	grant allows the user to download the VM image once for a certain time.
	 	The url where the file can be downloaded from has the form 
	 	http://server:port/grant/download where server is the address of this
	 	host, port is the fileserver port of this server (can be requested via
	 	host_info) and grant is the grant.
	*download_log_grant*, callable in state *prepared* or *created*
	    Create/update a grant to download the program log for the Repy device.
	    Works like download_grant.
"""

class Repy(elements.Element):

	pid = IntField()
	websocket_port = IntField()
	websocket_pid = IntField()
	vncport = IntField()
	vncpid = IntField()
	vncpassword =StringField()
	args = ListField()
	cpus = IntField(default=1)
	ram = IntField(default=256)
	bandwidth = IntField(min_value=1024, max_value=10000000000, default=1000000)
	template = ReferenceField(template.Template, null=True)
	templateId = ReferenceFieldId(template)

	ATTRIBUTES = elements.Element.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"args": Attribute(field=args, description="Arguments", schema = schema.List(), default=[]),
		"cpus": Attribute(field=cpus, description="Number of CPUs", schema=schema.Int(minValue=1,maxValue=4), default=1),
		"ram": Attribute(field=ram, description="RAM", schema=schema.Int(minValue=64, maxValue=8192), default=256),
		"bandwidth": Attribute(field=bandwidth, description="Bandwidth in bytes/s", schema=schema.Int(minValue=1024, maxValue=10000000000), default=1000000),
		"template": Attribute(field=templateId, description="Template", schema=schema.Identifier()),
	})

	TYPE = TypeName.REPY


	CAP_CHILDREN = {
		TypeName.REPY_INTERFACE: [StateName.PREPARED],
	}
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {"args": [], "cpus": 0.25, "ram": 25, "bandwidth": 1000000}
	DOC = DOC
	__doc__ = DOC #@ReservedAssignment

	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = StateName.PREPARED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		self.vmid = self.getResource("vmid")
		self.vncport = self.getResource("port")
		self.websocket_port = self.getResource("port", config.WEBSOCKIFY_PORT_BLACKLIST)
		self.vncpassword = cmd.randomPassword()
		if not self.template:
			self.modify_template("") #use default template
		self._setProfile()

	def _getState(self):
		if self.pid and process.exists(self.pid):
			return StateName.STARTED
		return StateName.PREPARED
		
	def _checkState(self):
		savedState = self.state
		realState = self._getState()
		if savedState != realState:
			self.setState(realState, True) #pragma: no cover
		InternalError.check(savedState == realState, InternalError.WRONG_DATA, "Saved state of element was wrong",
			data={"type": self.type, "id": self.id, "saved_state": savedState, "real_State": realState})

	def _interfaceName(self, name):
		return TypeName.REPY + "%d%s" % (self.id, name)

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

	def _useImage(self, path_):
		if path.exists(self.dataPath("program.repy")):
			path.remove(self.dataPath("program.repy"), recursive=True)
		path.copy(path_, self.dataPath("program.repy"))

	def _setProfile(self):
		res = {"diskused": 1000000, "lograte": 10000, "events": 10000, "random": 10000}
		res.update({"cpu": self.cpus, "memory": self.ram*1000000, "netrecv": self.bandwidth, "netsend": self.bandwidth})
		with open(self.dataPath("resources"), "w") as fp:
			for key, value in res.iteritems():
				fp.write("resource %s %s\n" % (key, value))

	def _checkImage(self, path):
		res = cmd.run(["repy-check", path]).strip()
		if res != "None":
			import re
			res = re.match("<(type|class) '([^']*)'> (.*)", res)
			raise UserError(message="Repy script error", code=UserError.INVALID_CONFIGURATION, data={"error_type": res.group(2), "error_message": res.group(3)})

	def modify_cpus(self, val):
		self.cpus = val
		self._setProfile()
	
	def modify_ram(self, val):
		self.ram = val
		self._setProfile()

	def modify_bandwidth(self, val):
		self.bandwidth = val
		self._setProfile()

	def modify_args(self, val):
		self.args = val
		if not isinstance(val, list):
			self.args = val.split()

	def modify_template(self, tmplName):
		self.template = template.get(self.TYPE, tmplName)
		if tmplName:
			UserError.check(self.template, code=UserError.ENTITY_DOES_NOT_EXIST, message="The selected template does not exist on this host.")
		templ = self._template()
		templ.fetch()
		self._useImage(templ.getPath())

	def action_start(self):
		iargs = sum((["-i", "%s,alias=%s" % (self._interfaceName(iface.name), iface.name)] for iface in self.getChildren()), [])
		stdout = open(self.dataPath("program.log"), "w")
		self.pid = cmd.spawn(["tomato-repy", "-p", self.dataPath("program.repy"), "-r", self.dataPath("resources"), "-v"] + iargs + self.args, stdout=stdout)
		self.setState(StateName.STARTED, True)
		for interface in self.getChildren():
			ifName = self._interfaceName(interface.name)
			InternalError.check(util.waitFor(lambda :net.ifaceExists(ifName)), InternalError.ASSERTION,
				"Interface did not start properly", data={"interface": ifName})
			net.ifUp(ifName)
			con = interface.getConnection()
			if con:
				con.connectInterface(self._interfaceName(interface.name))
			interface._start()
		net.freeTcpPort(self.vncport)				
		self.vncpid = cmd.spawnShell("while true; do vncterm -timeout 0 -rfbport %d -passwd %s -c bash -c 'while true; do tail -n +1 -f %s; sleep 1; done'; sleep 1; done" % (self.vncport, self.vncpassword, self.dataPath("program.log")), useExec=False)				
		InternalError.check(util.waitFor(lambda :net.tcpPortUsed(self.vncport)), InternalError.ASSERTION,
			"VNC server did not start")
		if not self.websocket_port:
			self.websocket_port = self.getResource("port")
		if websockifyVersion:
			net.freeTcpPort(self.websocket_port)
			self.websocket_pid = cmd.spawn(["websockify", "0.0.0.0:%d" % self.websocket_port, "localhost:%d" % self.vncport, '--cert=/etc/tomato/server.pem'])
			InternalError.check(util.waitFor(lambda :net.tcpPortUsed(self.websocket_port)), InternalError.ASSERTION,
				"Websocket VNC wrapper did not start")

	def action_stop(self):
		for interface in self.getChildren():
			con = interface.getConnection()
			if con:
				con.disconnectInterface(self._interfaceName(interface.name))
			interface._stop()
		if self.vncpid:
			process.killTree(self.vncpid)
			del self.vncpid
		if self.pid:
			process.kill(self.pid)
			del self.pid
		if self.websocket_pid:
			process.killTree(self.websocket_pid)
			del self.websocket_pid
		self.setState(StateName.PREPARED, True)
		
	def action_upload_grant(self):
		return fileserver.addGrant(self.dataPath("uploaded.repy"), fileserver.ACTION_UPLOAD)
		
	def action_upload_use(self):
		UserError.check(os.path.exists(self.dataPath("uploaded.repy")), UserError.NO_DATA_AVAILABLE,
			"No file has been uploaded")
		self._checkImage(self.dataPath("uploaded.repy"))
		os.rename(self.dataPath("uploaded.repy"), self.dataPath("program.repy"))
		
	def action_download_grant(self):
		#no need to copy file first
		return fileserver.addGrant(self.dataPath("program.repy"), fileserver.ACTION_DOWNLOAD)

	def action_download_log_grant(self):
		# make sure there is no leftover log from last download
		if os.path.exists(self.dataPath("download.log")):
			os.remove(self.dataPath("download.log"))

		# if a log exists, use this. if not, create an empty file for the user to download
		if os.path.exists(self.dataPath("program.log")):
			shutil.copyfile(self.dataPath("program.log"),self.dataPath("download.log"))
		else:
			open(self.dataPath("download.log"), 'a').close()

		# now, return a grant to download this.
		return fileserver.addGrant(self.dataPath("download.log"), fileserver.ACTION_DOWNLOAD)
		
	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["template"] = self.template.upcast().name if self.template else None
		return info

	def updateUsage(self, usage, data):
		self._checkState()
		usage.diskspace = path.diskspace(self.dataPath())
		if self.state == StateName.STARTED:
			usage.memory = process.memory(self.pid)
			cputime = process.cputime(self.pid)
			if self.vncpid:
				usage.memory += process.memory(self.vncpid)
				cputime += process.cputime(self.vncpid)
			usage.updateContinuous("cputime", cputime, data)

	ACTIONS = elements.Element.ACTIONS.copy()
	ACTIONS.update({
		Entity.REMOVE_ACTION: StatefulAction(elements.Element.remove, check=elements.Element.checkRemove,
											 allowedStates=[StateName.CREATED]),
		ActionName.START: StatefulAction(action_start, allowedStates=[StateName.PREPARED],
										 stateChange=StateName.STARTED),
		ActionName.STOP: StatefulAction(action_stop, allowedStates=[StateName.STARTED],
										stateChange=StateName.PREPARED),
		ActionName.UPLOAD_GRANT: StatefulAction(action_upload_grant, allowedStates=[StateName.PREPARED]),
		ActionName.UPLOAD_USE: StatefulAction(action_upload_use, allowedStates=[StateName.PREPARED]),
		"download_grant": StatefulAction(action_download_grant, allowedStates=[StateName.PREPARED]),
		"download_log_grant": StatefulAction(action_download_log_grant,
												allowedStates=[StateName.PREPARED, StateName.STARTED]),
	})
Repy.__doc__ = DOC

DOC_IFACE="""
Element type: ``repy_interface``

Description:
	This element type represents a network interface of repy element type. Its
	state is managed by and synchronized with the parent element.

Possible parents: ``repy``

Possible children: None

Default state: *prepared*

Removable in states: *prepared*
	
Connection concepts: *interface*

States:
	*prepared*: In this state the interface is known of.
	*started*: In this state the interface is running.
		
Attributes: None

Actions: None
"""

class Repy_Interface(elements.Element):

	name = StringField(regex="^eth[0-9]+$")
	ipspy_pid = IntField()
	used_addresses = ListField(default=[])

	ATTRIBUTES = elements.Element.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"name": Attribute(field=name, description="Name", schema=schema.String(regex="^eth[0-9]+$")),
		"ipspy_pid": Attribute(field=ipspy_pid, schema=schema.Int()),
		"used_addresses": Attribute(field=used_addresses, schema=schema.List(), default=[])
	})

	ACTIONS = elements.Element.ACTIONS.copy()
	ACTIONS.update({
		Entity.REMOVE_ACTION: StatefulAction(elements.Element.remove, check=elements.Element.checkRemove,
											 allowedStates=[StateName.CREATED]),
	})

	TYPE = TypeName.REPY_INTERFACE
	CAP_ACTIONS = {
		elements.REMOVE_ACTION: [StateName.PREPARED]
	}
	CAP_ATTRS = {
		"timeout": elements.Element.timeout
	}

	CAP_NEXT_STATE = {}
	CAP_CHILDREN = {}
	CAP_PARENT = [Repy.TYPE]
	CAP_CON_CONCEPTS = [connections.CONCEPT_INTERFACE]
	DOC = DOC_IFACE

	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = StateName.PREPARED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		assert isinstance(self.getParent(), Repy)
		self.name = self.getParent()._nextIfaceName()
		
	def interfaceName(self):
		return self.getParent()._interfaceName(self.name)
		
	def upcast(self):
		return self

	def _start(self):
		self.ipspy_pid = net.ipspy_start(self.interfaceName(), self.dataPath("ipspy.json"))
		self.save()
	
	def _stop(self):
		if self.ipspy_pid:
			process.kill(self.ipspy_pid)
			del self.ipspy_pid
		self.save()

	def info(self):
		if self.state == StateName.STARTED:
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
	
			
Repy_Interface.__doc__ = DOC_IFACE

def register(): #pragma: no cover
	if not repyVersion:
		print >>sys.stderr, "Warning: Repy needs tomato-repy, disabled"
		return
	if not ([0, 5] <= repyVersion):
		print >>sys.stderr, "Warning: Repy not supported on tomato-repy version %s, disabled" % repyVersion
		return
	if not vnctermVersion:
		print >>sys.stderr, "Warning: Repy needs vncterm, disabled"
		return
	if not ipspyVersion:
		print >>sys.stderr, "Warning: ipspy not available"
	elements.TYPES[Repy.TYPE] = Repy
	elements.TYPES[Repy_Interface.TYPE] = Repy_Interface

if not config.MAINTENANCE:
	repyVersion = cmd.getDpkgVersion("tomato-repy")
	vnctermVersion = cmd.getDpkgVersion("vncterm")
	websockifyVersion = cmd.getDpkgVersion("websockify")
	ipspyVersion = cmd.getDpkgVersion("ipspy")
	register()