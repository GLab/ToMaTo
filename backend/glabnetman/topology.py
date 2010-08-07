# -*- coding: utf-8 -*-

from xml.dom import minidom

from task import TaskStatus

from util import *
from log import Logger

import api, config, openvz, dhcp, tinc, real_network, topology_analysis, resource

import shutil, os, stat, sys, thread, uuid

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
		self.analysis=topology_analysis.analyze(self)
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
		try:
			x_top = dom.getElementsByTagName ( "topology" )[0]
		except IndexError, err:
			raise api.Fault(api.Fault.MALFORMED_TOPOLOGY_DESCRIPTION, "Malformed topology description: topology must contain a <topology> tag")
		if not load_ids:
			if x_top.hasAttribute("id"):
				x_top.removeAttribute("id")
			if x_top.hasAttribute("state"):
				x_top.removeAttribute("state")
			if x_top.hasAttribute("owner"):
				x_top.removeAttribute("owner")
		XmlObject.decode_xml(self,x_top)
		for x_dev in x_top.getElementsByTagName ( "device" ):
			try:
				Type = { "openvz": openvz.OpenVZDevice, "dhcpd": dhcp.DhcpdDevice }[x_dev.getAttribute("type")]
			except KeyError, err:
				raise api.Fault(api.Fault.MALFORMED_TOPOLOGY_DESCRIPTION, "Malformed topology description: device type unknown: %s" % x_dev.getAttribute("type") )
			self.add_device ( Type ( self, x_dev, load_ids ) )
		for x_con in x_top.getElementsByTagName ( "connector" ):
			try:
				Type = { "hub": tinc.TincConnector, "switch": tinc.TincConnector, "router": tinc.TincConnector, "real": real_network.RealNetworkConnector }[x_con.getAttribute("type")]
			except KeyError, err:
				raise api.Fault(api.Fault.MALFORMED_TOPOLOGY_DESCRIPTION, "Malformed topology description: connector type unknown: %s" % x_con.getAttribute("type") )
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

	def get_control_dir(self,host_name):
		"""
		The local directory where all control scripts and files are stored.
		@param host_name the name of the host for the deployment
		"""
		return config.local_control_dir+"/"+host_name

	def get_remote_control_dir(self):
		"""
		The remote directory where all control scripts and files will be copied to.
		"""
		return config.remote_control_dir+"/"+str(self.id)

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
			raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not registered")
		if len(self.analysis.problems) > 0:
			raise api.Fault (api.Fault.TOPOLOGY_HAS_PROBLEMS, "topology has problems")
		task = api.TaskStatus()
		thread.start_new_thread(self.upload_run,tuple([task]))
		return task.id
	
	def upload_run(self, task):
		task.subtasks_total = 1 + len(self.affected_hosts()) + len(self.devices) + len(self.connectors)
		self.take_resources()
		task.subtasks_done = 1
		self.write_control_scripts(task)
		self.upload_control_scripts(task)
		if self.state == TopologyState.CREATED:
			self.state = TopologyState.UPLOADED
		self._log("upload", task.output.getvalue())
		task.done()
	
	def write_control_scripts(self, task):
		"""
		Creates all control scripts and stores them in a local directory.
		"""
		task.output.write("creating scripts ...\n")
		if config.local_control_dir and os.path.exists(config.local_control_dir):
			shutil.rmtree(config.local_control_dir)
		for dev in self.devices.values():
			task.output.write("\tcreating aux files for %s ...\n" % dev)
			dev.write_aux_files()
			task.subtasks_done = task.subtasks_done+1
		for con in self.connectors.values():
			task.output.write("\tcreating aux files for %s ...\n" % con)
			con.write_aux_files()
			task.subtasks_done = task.subtasks_done+1
		for host in self.affected_hosts():
			dir=self.get_control_dir(host.name)
			if not os.path.exists(dir):
				os.makedirs(dir)
			for script in ("prepare", "destroy", "start", "stop"):
				script_fd = open(self.get_control_script(host.name,script), "w")
				script_fd.write("#!/bin/bash\ncd %s\n\n" % self.get_remote_control_dir())
				for dev in self.devices.values():
					script_fd.write("\n# commands for %s\n" % dev)
					dev.write_control_script(host, script, script_fd)
				for con in self.connectors.values():
					script_fd.write("\n# commands for %s\n" % con)
					con.write_control_script(host, script, script_fd)
				script_fd.close()
				os.chmod(self.get_control_script(host.name,script), stat.S_IRWXU)

	def upload_control_scripts(self, task):
		"""
		Uploads all control scripts stored in a local directory.
		"""
		task.output.write("uploading scripts ...\n")
		for host in self.affected_hosts():
			task.output.write("%s ...\n" % host.name)
			src = self.get_control_dir(host.name)
			dst = "root@%s:%s" % ( host.name, self.get_remote_control_dir() )
			task.output.write(run_shell ( ["ssh",  "root@%s" % host.name, "mkdir -p %s/%s" % ( config.remote_control_dir, self.id ) ], config.remote_dry_run ))
			task.output.write(run_shell (["ssh",  "root@%s" % host.name, "rm -r %s/%s" % ( config.remote_control_dir, self.id ) ], config.remote_dry_run ))
			task.output.write(run_shell (["rsync",  "-a",  "%s/" % src, dst], config.remote_dry_run))
			task.output.write("\n")
			task.subtasks_done = task.subtasks_done+1
			
	def exec_script(self, script, task, newstate):
		"""
		Executes a control script.
		@param script the script to execute
		"""
		if not self.id:
			raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not registered")
		task.subtasks_total = len(self.affected_hosts())
		task.output.write("executing %s ...\n" % script)
		script = "%s/%s/%s.sh" % ( config.remote_control_dir, self.id, script )
		for host in self.affected_hosts():
			task.output.write("%s ...\n" % host.name)
			task.output.write(run_shell(["ssh",  "root@%s" % host.name, script ], config.remote_dry_run ))
			task.output.write("\n")
			task.subtasks_done = task.subtasks_done + 1
		self.state=newstate
		self._log("execute %s" % script, task.output.getvalue())
		task.done()

	def start(self):
		"""
		Starts the topology.
		This will fail if the topology has not been uploaded or prepared yet or is already started.
		"""
		if len(self.analysis.problems) > 0:
			raise api.Fault (api.Fault.TOPOLOGY_HAS_PROBLEMS, "topology has problems")
		if self.state == TopologyState.CREATED:
			raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not uploaded")
		if self.state == TopologyState.UPLOADED:
			raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not prepared")
		if self.state == TopologyState.PREPARED:
			pass
		if self.state == TopologyState.STARTED:
			raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "already started")
		task = api.TaskStatus()
		thread.start_new_thread(self.exec_script,("start", task, TopologyState.STARTED))
		return task.id

	def stop(self):
		"""
		Stops the topology.
		This will fail if the topology has not been uploaded or prepared yet.
		"""
		if self.state == TopologyState.CREATED:
			raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not uploaded")
		if self.state == TopologyState.UPLOADED:
			raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not prepared")
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
		if len(self.analysis.problems) > 0:
			raise api.Fault (api.Fault.TOPOLOGY_HAS_PROBLEMS, "topology has problems")
		if self.state == TopologyState.CREATED:
			raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not uploaded")
		if self.state == TopologyState.UPLOADED:
			pass
		if self.state == TopologyState.PREPARED:
			raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "already prepared")
		if self.state == TopologyState.STARTED:
			raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "already started")
		task = api.TaskStatus()
		thread.start_new_thread(self.exec_script,("prepare", task, TopologyState.PREPARED))
		return task.id

	def destroy(self):
		"""
		Destroys the topology.
		This will fail if the topology has not been uploaded yet or is already started.
		"""
		if self.state == TopologyState.CREATED:
			raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not uploaded")
		if self.state == TopologyState.UPLOADED:
			pass
		if self.state == TopologyState.PREPARED:
			pass
		if self.state == TopologyState.STARTED:
			raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "already started")
		task = api.TaskStatus()
		thread.start_new_thread(self.exec_script,("destroy", task, TopologyState.UPLOADED))
		return task.id
	
	def _change_created(self, newtop, task):
		# easy case: simply exchange definition, no change to deployed components needed
		self.free_resources()
		self.devices = {}
		self.connectors = {}
		for dev in newtop.devices.values():
			self.add_device(dev)
		for con in newtop.connectors.values():
			self.add_connector(con)
		self.take_resources()
		self.analysis = topology_analysis.analyze(self)
		task.done()

	def _change_prepared(self, newtop, task):
		# difficult case: deployed components already exist
		changeid=str(uuid.uuid1())
		task.subtasks_total = 1 + len(self.affected_hosts())*2 + len(self.devices) + len(self.connectors)
		newdevs=set()
		changeddevs={}
		removeddevs=set()
		for dev in self.devices.values():
			if dev.id in newtop.devices.keys():
				newdev=newtop.devices[dev.id]
				changeddevs[dev]=newdev
			else:
				removeddevs.add(dev)
		for dev in newtop.devices.values():
			if not dev.id in self.devices.keys():
				newdevs.add(dev)
		#delete removed devices
		for dev in removeddevs:
			dev.free_resources()
			del self.devices[dev.id]
		#add new devices
		for dev in newdevs:
			self.add_device(dev)
			dev.take_resources()
		for host in self.affected_hosts():
			script = "change_%s" % changeid
			src = self.get_control_script(host.name,script)
			script_fd = open(src, "w")
			for dev in removeddevs:
				if dev.host_name == host.name:
					dev.write_control_script(host,"destroy",script_fd)
			for dev in newdevs:
				if dev.host_name == host.name:
					dev.write_control_script(host,"prepare",script_fd)
			for dev in changeddevs.keys():
				if dev.host_name == host.name:
					dev.change(changeddevs[dev],script_fd)
			script_fd.close()
			os.chmod(src, stat.S_IRWXU)
			dst = "root@%s:%s" % ( host.name, self.get_remote_control_dir() )
			remote_script = "%s/%s/%s.sh" % ( config.remote_control_dir, self.id, script )
			task.output.write(run_shell(["rsync",  "-a", src, dst], config.remote_dry_run))
			task.output.write(run_shell(["ssh",  "root@%s" % host.name, remote_script ], config.remote_dry_run))
			task.subtasks_done = task.subtasks_done + 1
		newcons=set()
		removedcons=set()
		for con in self.connectors.values():
			removedcons.add(con)
			if con.id in newtop.connectors.keys():
				newcons.add(newtop.connectors[con.id])
		for con in newtop.connectors.values():
			if not con.id in self.connectors.keys():
				newcons.add(con)
		#delete removed connectors
		for con in removedcons:
			con.free_resources()
			del self.connectors[con.id]
		#add new connectors
		for con in newcons:
			self.add_connector(con)
			con.take_resources()
		self.write_control_scripts(task)
		self.upload_control_scripts(task)
		self.analysis = topology_analysis.analyze(self)
		self._log("change", task.output.getvalue())
		task.done()

	def check_change_possible(self, newtop):
		for dev in self.devices.values():
			if dev.id in newtop.devices.keys():
				newdev=newtop.devices[dev.id]
				dev.check_change_possible(newdev)
				
	def change(self, newtop):
		if self.state == TopologyState.UPLOADED:
			self.state = TopologyState.CREATED
		if self.state == TopologyState.CREATED:
			task = api.TaskStatus()
			thread.start_new_thread(self._change_created,(newtop, task))
			return task.id
		if self.state == TopologyState.PREPARED:
			self.check_change_possible(newtop)
			task = api.TaskStatus()
			thread.start_new_thread(self._change_prepared,(newtop, task))
			return task.id
		if self.state == TopologyState.STARTED:
			raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "already started")
		
	def _log(self, task, output):
		logger = Logger(config.log_dir+"/top_%s.log" % self.id)
		logger.log(task, bigmessage=output)