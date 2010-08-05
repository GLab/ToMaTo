# -*- coding: utf-8 -*-

from xml.dom import minidom
from cStringIO import StringIO

from openvz_device import *
from dhcpd_device import *
from tinc_connector import *
from real_network_connector import *
from config import *
from resource_store import *
from topology_analysis import *

import api

import shutil, os, stat, sys, thread

class TopologyState():
	"""
	The state of the topology, this is an assigned value. The states are considered to be in order:
	created -> uploaded -> prepared -> started
	created		the topology has been created but not uploaded
	uploaded	the topology has been uploaded to the hosts but has not been prepared yet
	prepared	the topology has been uploaded and all devices have been prepared
	started		the topology has been uploaded and prepared and is currently up and running
	"""
	CREATED="created"
	UPLOADED="uploaded"
	PREPARED="prepared"
	STARTED="started"

class Topology(XmlObject):
	"""
	This class represents a whole topology and offers methods to work with it
	"""

	def __init__ (self, dom, load_ids):
		"""
		Creates a new topology
		@param file the xml file to load the topology definition from
		@param load_ids whether to load or ignore assigned ids from that file
		"""
		self.devices={}
		self.connectors={}
		self.load_from(dom, load_ids)
		self.analysis=TopologyAnalysis(self)
		if not self.state:
			self.state=TopologyState.CREATED
		
	id=property(curry(XmlObject.get_attr, "id"), curry(XmlObject.set_attr, "id"))
	"""
	The id of the topology, this is an assigned value
	"""
	
	state=property(curry(XmlObject.get_attr, "state"), curry(XmlObject.set_attr, "state"))
	"""
	@see TopologyState
	"""
	
	owner=property(curry(XmlObject.get_attr, "owner"), curry(XmlObject.set_attr, "owner"))
	"""
	@see TopologyState
	"""

	def add_device ( self, device ):
		"""
		Adds a device to the device map and sets the topology of the device
		"""
		device.topology = self
		self.devices[device.id] = device
		
	def add_connector ( self, connector ):
		"""
		Adds a connector to the connector map and sets the topology of the connector
		"""
		connector.topology = self
		self.connectors[connector.id] = connector
		
	def load_from ( self, dom, load_ids ):
		"""
		Loads this topology from a file
		@param dom the xml dom to load the topology definition from
		@param load_ids whether to load or ignore assigned ids from that file
		"""
		x_top = dom.getElementsByTagName ( "topology" )[0]
		if not load_ids:
			if x_top.hasAttribute("id"):
				x_top.removeAttribute("id")
			if x_top.hasAttribute("state"):
				x_top.removeAttribute("state")
			if x_top.hasAttribute("owner"):
				x_top.removeAttribute("owner")
		XmlObject.decode_xml(self,x_top)
		for x_dev in x_top.getElementsByTagName ( "device" ):
			Type = { "openvz": OpenVZDevice, "dhcpd": DhcpdDevice }[x_dev.getAttribute("type")]
			self.add_device ( Type ( self, x_dev, load_ids ) )
		for x_con in x_top.getElementsByTagName ( "connector" ):
			Type = { "hub": TincConnector, "switch": TincConnector, "router": TincConnector, "real": RealNetworkConnector }[x_con.getAttribute("type")]
			self.add_connector ( Type ( self, x_con, load_ids ) )
			
	def create_dom ( self, print_ids ):
		"""
		Creates an xml dom object containing the xml representation of this topology
		@param print_ids whether to store or ignore assigned ids int the dom
		"""
		dom = minidom.Document()
		x_top = dom.createElement ( "topology" )
		XmlObject.encode_xml(self,x_top)
		if not print_ids:
			if x_top.hasAttribute("id"):
				x_top.removeAttribute("id")
			if x_top.hasAttribute("state"):
				x_top.removeAttribute("state")
			if x_top.hasAttribute("owner"):
				x_top.removeAttribute("owner")
		dom.appendChild ( x_top )
		for dev in self.devices.values():
			x_dev = dom.createElement ( "device" )
			dev.encode_xml ( x_dev, dom, print_ids )
			x_top.appendChild ( x_dev )
		for con in self.connectors.values():
			x_con = dom.createElement ( "connector" )
			con.encode_xml ( x_con, dom, print_ids )
			x_top.appendChild ( x_con )
		return dom

	def save_to (self, file, print_ids):
		"""
		Saves the xml representation of this topology in a file
		@param file the file to save to
		@param print_ids whether to store or ignore assigned ids int the file
		"""
		dom = self.create_dom(print_ids)
		fd = open ( file, "w" )
		dom.writexml(fd, indent="", addindent="\t", newl="\n")
		fd.close()

	def retake_resources ( self ):
		"""
		Take all resources that this topology once had. Fields containing the ids of assigned resources control which resources will be taken.
		"""
		for dev in self.devices.values():
			dev.retake_resources()
		for con in self.connectors.values():
			con.retake_resources()

	def take_resources ( self ):
		"""
		Take free resources for all unassigned resource slots. The number of the resources will be stored in internal fields.
		"""
		for dev in self.devices.values():
			dev.take_resources()
		for con in self.connectors.values():
			con.take_resources()

	def free_resources ( self ):
		"""
		Free all resources for all resource slots.
		"""
		for dev in self.devices.values():
			dev.free_resources()
		for con in self.connectors.values():
			con.free_resources()

	def affected_hosts (self):
		"""
		The set of all hosts that this topology has devices on.
		"""
		hosts=set()
		for dev in self.devices.values():
			hosts.add(dev.host)
		return hosts

	def resource_usage(self):
		return len(self.devices) + len(self.connectors)

	def get_control_dir(self,host_name):
		"""
		The local directory where all control scripts and files are stored.
		@param host_name the name of the host for the deployment
		"""
		return Config.local_control_dir+"/"+host_name

	def get_remote_control_dir(self):
		"""
		The remote directory where all control scripts and files will be copied to.
		"""
		return Config.remote_control_dir+"/"+str(self.id)

	def get_control_script(self,host_name,script):
		"""
		The local path of a specific control script.
		@param host_name the name of the host for the deployment
		@param script the name of the script without .sh
		"""
		return self.get_control_dir(host_name)+"/"+script+".sh"

	def upload(self):
		"""
		This will upload the topology to the testbed in thwe following steps:
		1. Fill all unassigned resource slots
		2. Create the control scripts
		3. Upload the control scripts
		Note: this can be done even if the topology is already uploaded or even running
		"""
		if not self.id:
			from api import Fault
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not registered")
		task = api.TaskStatus()
		thread.start_new_thread(self.upload_run,tuple([task]))
		return task.id
	
	def upload_run(self, task):
		if not self.id:
			from api import Fault
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not registered")
		task.subtasks_total = 1 + len(self.affected_hosts()) + len(self.devices) + len(self.connectors)
		self.take_resources()
		task.subtasks_done = 1
		self.write_control_scripts(task)
		self.upload_control_scripts(task)
		if self.state == TopologyState.CREATED:
			self.state = TopologyState.UPLOADED
		task.done()
	
	def write_control_scripts(self, task):
		"""
		Creates all control scripts and stores them in a local directory.
		"""
		if not self.id:
			from api import Fault
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not registered")
		task.output.write("creating scripts ...\n")
		if Config.local_control_dir and os.path.exists(Config.local_control_dir):
			shutil.rmtree(Config.local_control_dir)
		for host in self.affected_hosts():
			dir=self.get_control_dir(host.name)
			if not os.path.exists(dir):
				os.makedirs(dir)
			for script in ("prepare", "destroy", "start", "stop"):
				script_fd = open(self.get_control_script(host.name,script), "w")
				script_fd.write("#!/bin/bash\ncd %s\n\n" % self.get_remote_control_dir())
				script_fd.close()
				os.chmod(self.get_control_script(host.name,script), stat.S_IRWXU)
		for dev in self.devices.values():
			task.output.write("\tcreating scripts for %s ...\n" % dev)
			dev.write_control_scripts()
			task.subtasks_done = task.subtasks_done+1
		for con in self.connectors.values():
			task.output.write("\tcreating scripts for %s ...\n" % con)
			con.write_control_scripts()
			task.subtasks_done = task.subtasks_done+1

	def upload_control_scripts(self, task):
		"""
		Uploads all control scripts stored in a local directory.
		"""
		if not self.id:
			from api import Fault
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not registered")
		task.output.write("uploading scripts ...\n")
		for host in self.affected_hosts():
			task.output.write("%s ...\n" % host.name)
			src = self.get_control_dir(host.name)
			dst = "root@%s:%s" % ( host.name, self.get_remote_control_dir() )
			task.output.write(run_shell ( ["ssh",  "root@%s" % host.name, "mkdir -p %s/%s" % ( Config.remote_control_dir, self.id ) ], Config.remote_dry_run ))
			task.output.write(run_shell (["ssh",  "root@%s" % host.name, "rm -r %s/%s" % ( Config.remote_control_dir, self.id ) ], Config.remote_dry_run ))
			task.output.write(run_shell (["rsync",  "-a",  "%s/" % src, dst], Config.remote_dry_run))
			task.output.write("\n")
			task.subtasks_done = task.subtasks_done+1
			
	def exec_script(self, script, task, newstate):
		"""
		Executes a control script.
		@param script the script to execute
		"""
		if not self.id:
			from api import Fault
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not registered")
		task.subtasks_total = len(self.affected_hosts())
		task.output.write("executing %s ...\n" % script)
		script = "%s/%s/%s.sh" % ( Config.remote_control_dir, self.id, script )
		for host in self.affected_hosts():
			task.output.write("%s ...\n" % host.name)
			task.output.write(run_shell(["ssh",  "root@%s" % host.name, script ], Config.remote_dry_run ))
			task.output.write("\n")
			task.subtasks_done = task.subtasks_done + 1
		self.state=newstate
		task.done()

	def start(self):
		"""
		Starts the topology.
		This will fail if the topology has not been uploaded or prepared yet or is already started.
		"""
		from api import Fault
		if self.state == TopologyState.CREATED:
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not uploaded")
		if self.state == TopologyState.UPLOADED:
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not prepared")
		if self.state == TopologyState.PREPARED:
			pass
		if self.state == TopologyState.STARTED:
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "already started")
		task = api.TaskStatus()
		thread.start_new_thread(self.exec_script,("start", task, TopologyState.STARTED))
		return task.id

	def stop(self):
		"""
		Stops the topology.
		This will fail if the topology has not been uploaded or prepared yet.
		"""
		from api import Fault
		if self.state == TopologyState.CREATED:
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not uploaded")
		if self.state == TopologyState.UPLOADED:
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not prepared")
		if self.state == TopologyState.PREPARED:
			pass
		if self.state == TopologyState.STARTED:
			pass
		task = api.TaskStatus()
		thread.start_new_thread(self.exec_script,("stop", task, TopologyState.PREPARED))
		return task.id

	def prepare(self):
		"""
		Prepares the topology.
		This will fail if the topology has not been uploaded yet or is already prepared or started.
		"""
		from api import Fault
		if self.state == TopologyState.CREATED:
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not uploaded")
		if self.state == TopologyState.UPLOADED:
			pass
		if self.state == TopologyState.PREPARED:
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "already prepared")
		if self.state == TopologyState.STARTED:
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "already started")
		task = api.TaskStatus()
		thread.start_new_thread(self.exec_script,("prepare", task, TopologyState.PREPARED))
		return task.id

	def destroy(self):
		"""
		Destroys the topology.
		This will fail if the topology has not been uploaded yet or is already started.
		"""
		from api import Fault
		if self.state == TopologyState.CREATED:
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not uploaded")
		if self.state == TopologyState.UPLOADED:
			pass
		if self.state == TopologyState.PREPARED:
			pass
		if self.state == TopologyState.STARTED:
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "already started")
		task = api.TaskStatus()
		thread.start_new_thread(self.exec_script,("destroy", task, TopologyState.UPLOADED))
		return task.id
