# -*- coding: utf-8 -*-

from django.db import models
import thread, os, shutil, stat, uuid
import config, log, fault, util, tasks
import topology_analysis, generic

class State():
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

class Topology(models.Model):
	"""
	This class represents a whole topology and offers methods to work with it
	"""
	
	id = models.AutoField(primary_key=True)
	"""
	The id of the topology, this is an assigned value
	"""
	
	name = models.CharField(max_length=30, blank=True)
	"""
	The name of the topology.
	"""
	
	state = models.CharField(max_length=10, choices=((State.CREATED, State.CREATED), (State.UPLOADED, State.UPLOADED), (State.PREPARED, State.PREPARED), (State.STARTED, State.STARTED)))
	"""
	@see TopologyState
	"""
	
	owner = models.CharField(max_length=30)

	date_created = models.DateTimeField(auto_now_add=True)
	
	date_modified = models.DateTimeField(auto_now=True)

	def init (self, dom, owner):
		"""
		Creates a new topology
		@param file the xml file to load the topology definition from
		@param owner the owner of the topology
		"""
		self.owner=owner
		self.state=State.CREATED
		self.save()
		try:
			self.load_from(dom)
		except:
			self.delete()
			raise
		if not self.name:
			self.name = "Topology %s" % self.id
		self.save()

	def analysis(self):
		return topology_analysis.analyze(self)

	def devices_all(self):
		return self.device_set.all()
	
	def devices_get(self, name):
		return self.device_set.get(name=name)

	def devices_add(self, dev):
		if self.device_set.filter(name=dev.name).exclude(id=dev.id).count() > 0:
			raise fault.new(fault.DUPLICATE_DEVICE_ID, "Duplicate device id: %s" % dev.name)
		self.device_set.add(dev)

	def devices_add_dom(self, dev):
		import openvz, kvm, dhcp
		try:
			Type = { "openvz": openvz.OpenVZDevice, "kvm": kvm.KVMDevice, "dhcpd": dhcp.DhcpdDevice }[dev.getAttribute("type")]
		except KeyError:
			raise fault.new(fault.UNKNOWN_DEVICE_TYPE, "Malformed topology description: device type unknown: %s" % dev.getAttribute("type") )
		d = Type()
		d.init(self, dev)
		self.devices_add ( d )		

	def connectors_all(self):
		return self.connector_set.all()
	
	def connectors_get(self, name):
		return self.connector_set.get(name=name)

	def connectors_add(self, con):
		if self.connector_set.filter(name=con.name).exclude(id=con.id).count() > 0:
			raise fault.new(fault.DUPLICATE_CONNECTOR_ID, "Duplicate connector id: %s" % con.name)
		self.connector_set.add(con)

	def connectors_add_dom(self, con):
		import tinc, internet
		try:
			Type = { "hub": tinc.TincConnector, "switch": tinc.TincConnector, "router": tinc.TincConnector, "real": internet.InternetConnector }[con.getAttribute("type")]
		except KeyError:
			raise fault.new(fault.UNKNOWN_CONNECTOR_TYPE, "Malformed topology description: connector type unknown: %s" % con.getAttribute("type") )
		c = Type()
		c.init(self, con)
		self.connectors_add ( c )		

	def affected_hosts (self):
		"""
		The set of all hosts that this topology has devices on.
		"""
		import hosts
		return hosts.Host.objects.filter(device__topology=self).distinct()

	def load_from(self, dom):
		"""
		Loads this topology from a file
		@param dom the xml dom to load the topology definition from
		"""
		if dom.hasAttribute("name"):
			self.name = dom.getAttribute("name")
		for dev in dom.getElementsByTagName ( "device" ):
			self.devices_add_dom(dev)
		for con in dom.getElementsByTagName ( "connector" ):
			self.connectors_add_dom(con)
	
	def save_to ( self, dom, doc, internal ):
		"""
		Creates an xml dom object containing the xml representation of this topology
		@param internal whether to store or ignore assigned ids int the dom
		"""
		if internal:
			dom.setAttribute("id", self.id)
			dom.setAttribute("state", self.state)
			dom.setAttribute("owner", self.owner)
		dom.setAttribute("name", self.name)
		for dev in self.devices_all():
			x_dev = doc.createElement ( "device" )
			dev.upcast().encode_xml ( x_dev, doc, internal )
			dom.appendChild ( x_dev )
		for con in self.connectors_all():
			x_con = doc.createElement ( "connector" )
			con.upcast().encode_xml ( x_con, doc, internal )
			dom.appendChild ( x_con )
		return dom

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
		This will upload the topology to the testbed in the following steps:
		1. Fill all unassigned resource slots
		2. Create the control scripts
		3. Upload the control scripts
		Note: this can be done even if the topology is already uploaded or even running
		"""
		if not self.id:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not registered")
		if len(self.analysis()["problems"]) > 0:
			raise fault.new(fault.TOPOLOGY_HAS_PROBLEMS, "topology has problems")
		task = tasks.TaskStatus()
		thread.start_new_thread(self.upload_run,(task,))
		#self.upload_run(task) 
		return task.id
	
	def upload_run(self, task):
		task.subtasks_total = len(self.affected_hosts()) + len(self.devices_all()) + len(self.connectors_all())
		self.write_control_scripts(task)
		self.upload_control_scripts(task)
		if self.state == State.CREATED:
			self.state = State.UPLOADED
		self.save()
		self._log("upload", task.output.getvalue())
		task.done()
	
	def write_control_scripts(self, task):
		"""
		Creates all control scripts and stores them in a local directory.
		"""
		task.output.write("creating scripts ...\n")
		if config.local_control_dir and os.path.exists(config.local_control_dir):
			shutil.rmtree(config.local_control_dir)
		for dev in self.devices_all():
			task.output.write("\tcreating aux files for %s ...\n" % dev)
			dev.upcast().write_aux_files()
			task.subtasks_done = task.subtasks_done+1
		for con in self.connectors_all():
			task.output.write("\tcreating aux files for %s ...\n" % con)
			con.upcast().write_aux_files()
			task.subtasks_done = task.subtasks_done+1
		for host in self.affected_hosts():
			dir=self.get_control_dir(host.name)
			if not os.path.exists(dir):
				os.makedirs(dir)
			for script in ("prepare", "destroy", "start", "stop"):
				script_fd = open(self.get_control_script(host.name,script), "w")
				script_fd.write("#!/bin/bash\ncd %s\n\n" % self.get_remote_control_dir())
				for dev in self.devices_all():
					if dev.host == host:
						script_fd.write("\n# commands for %s\n" % dev)
						dev.upcast().write_control_script(host, script, script_fd)
				for con in self.connectors_all():
					script_fd.write("\n# commands for %s\n" % con)
					con.upcast().write_control_script(host, script, script_fd)
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
			task.output.write(util.run_shell ( ["ssh",  "root@%s" % host.name, "mkdir -p %s/%s" % ( config.remote_control_dir, self.id ) ], config.remote_dry_run ))
			task.output.write(util.run_shell (["ssh",  "root@%s" % host.name, "rm -r %s/%s" % ( config.remote_control_dir, self.id ) ], config.remote_dry_run ))
			task.output.write(util.run_shell (["rsync",  "-a",  "%s/" % src, dst], config.remote_dry_run))
			task.output.write("\n")
			task.subtasks_done = task.subtasks_done+1
			
	def exec_script(self, script, task, newstate):
		"""
		Executes a control script.
		@param script the script to execute
		"""
		if not self.id:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not registered")
		task.subtasks_total = len(self.affected_hosts())
		task.output.write("executing %s ...\n" % script)
		script = "%s/%s/%s.sh" % ( config.remote_control_dir, self.id, script )
		for host in self.affected_hosts():
			task.output.write("%s ...\n" % host.name)
			task.output.write(util.run_shell(["ssh",  "root@%s" % host.name, script ], config.remote_dry_run ))
			task.output.write("\n")
			task.subtasks_done = task.subtasks_done + 1
		self.state=newstate
		self.save()
		self._log("execute %s" % script, task.output.getvalue())
		task.done()

	def start(self):
		"""
		Starts the topology.
		This will fail if the topology has not been uploaded or prepared yet or is already started.
		"""
		if len(self.analysis()["problems"]) > 0:
			raise fault.new(fault.TOPOLOGY_HAS_PROBLEMS, "topology has problems")
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not uploaded")
		if self.state == State.UPLOADED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not prepared")
		if self.state == State.PREPARED:
			pass
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "already started")
		task = tasks.TaskStatus()
		thread.start_new_thread(self.exec_script,("start", task, State.STARTED))
		return task.id

	def stop(self):
		"""
		Stops the topology.
		This will fail if the topology has not been uploaded or prepared yet.
		"""
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not uploaded")
		if self.state == State.UPLOADED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not prepared")
		if self.state == State.PREPARED:
			pass
		if self.state == State.STARTED:
			pass
		task = tasks.TaskStatus()
		thread.start_new_thread(self.exec_script,("stop", task, State.PREPARED))
		return task.id

	def prepare(self):
		"""
		Prepares the topology.
		This will fail if the topology has not been uploaded yet or is already prepared or started.
		"""
		if len(self.analysis()["problems"]) > 0:
			raise fault.new(fault.TOPOLOGY_HAS_PROBLEMS, "topology has problems")
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not uploaded")
		if self.state == State.UPLOADED:
			pass
		if self.state == State.PREPARED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "already prepared")
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "already started")
		task = tasks.TaskStatus()
		thread.start_new_thread(self.exec_script,("prepare", task, State.PREPARED))
		return task.id

	def destroy(self):
		"""
		Destroys the topology.
		This will fail if the topology has not been uploaded yet or is already started.
		"""
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "not uploaded")
		if self.state == State.UPLOADED:
			pass
		if self.state == State.PREPARED:
			pass
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "already started")
		task = tasks.TaskStatus()
		thread.start_new_thread(self.exec_script,("destroy", task, State.UPLOADED))
		return task.id

	def change_run(self, dom, task):
		dir = config.local_control_dir + "/tmp"
		change_id = uuid.uuid1()
		if not os.path.exists(dir):
			os.makedirs(dir)
		host_scripts={}
		def get_host_script(host):
			if host_scripts.has_key(host.name):
				return host_scripts[host.name]
			else:
				script_fd = open("%s/%s_%s.sh" % (dir, host.name, change_id), "a")
				script_fd.write("#!/bin/bash\ncd %s\n\n" % self.get_remote_control_dir())
				host_scripts[host.name] = script_fd
				return script_fd
			
		devices=set()
		for x_dev in dom.getElementsByTagName("device"):
			name = x_dev.getAttribute("id")
			devices.add(name)
			try:
				dev = self.devices_get(name)
				# changed device
				dev.upcast().change_run(x_dev, task, get_host_script(dev.host))
			except generic.Device.DoesNotExist:
				# new device
				self.devices_add_dom(x_dev)
				dev = self.devices_get(name)
				if self.state == State.PREPARED or self.state == State.STARTED:
					dev.write_control_script(dev.host, "prepare", get_host_script(dev.host))
				if self.state == State.STARTED:
					dev.write_control_script(dev.host, "start", get_host_script(dev.host))
		for dev in self.devices_all():
			if not dev.name in devices:
				#removed device
				if self.state == State.STARTED:
					dev.upcast().write_control_script(dev.host, "stop", get_host_script(dev.host))
				if self.state == State.PREPARED or self.state == State.STARTED:
					dev.upcast().write_control_script(dev.host, "destroy", get_host_script(dev.host))
				dev.delete()
				
		connectors=set()	
		for x_con in dom.getElementsByTagName("connector"):
			name = x_con.getAttribute("id")
			connectors.add(name)
			try:
				con = self.connectors_get(name)
				con.upcast().change_run(x_con, task)
				for host in con.affected_hosts():
					if self.state == State.STARTED:
						con.upcast().write_control_script(host, "stop", get_host_script(host))
					if self.state == State.PREPARED or self.state == State.STARTED:
						con.upcast().write_control_script(host, "destroy", get_host_script(host))
			except generic.Connector.DoesNotExist:
				self.connectors_add_dom(x_con)
				con = self.connectors_get(name)				
			for host in con.affected_hosts():
				if self.state == State.PREPARED or self.state == State.STARTED:
					con.upcast().write_control_script(host, "prepare", get_host_script(host))
				if self.state == State.STARTED:
					con.upcast().write_control_script(host, "start", get_host_script(host))
		for con in self.connectors_all():
			if not con.name in connectors:
				for host in con.affected_hosts():
					if self.state == State.STARTED:
						con.upcast().write_control_script(host, "stop", get_host_script(host))
					if self.state == State.PREPARED or self.state == State.STARTED:
						con.upcast().write_control_script(host, "destroy", get_host_script(host))
				con.delete()				

		#finalize and execute scripts
		self.upload_control_scripts(task)
		for (host_name, script_fd) in host_scripts.items():
			script_fd.close()
			src = "%s/%s_%s.sh" % (dir, host_name, change_id)
			os.chmod(src, stat.S_IRWXU)
			dst = "root@%s:%s" % ( host.name, self.get_remote_control_dir() )
			task.output.write(util.run_shell (["rsync",  "-a",  "%s/" % src, dst], config.remote_dry_run))
			script = "%s/%s_%s.sh" % ( config.remote_control_dir, host_name, change_id )
			task.output.write(util.run_shell(["ssh",  "root@%s" % host.name, script ], config.remote_dry_run ))

	def change_possible(self, dom):
		for x_dev in dom.getElementsByTagName("device"):
			name = x_dev.getAttribute("id")
			try:
				dev = self.devices_get(name)
				dev.upcast().change_possible(x_dev)
			except generic.Device.DoesNotExist:
				pass
		for x_con in dom.getElementsByTagName("connector"):
			name = x_con.getAttribute("id")
			try:
				con = self.connectors_get(name)
				con.upcast().change_possible(x_con)
			except generic.Connector.DoesNotExist:
				pass
				
	def change(self, newtop):
		self.change_possible(newtop)
		task = tasks.TaskStatus()
		thread.start_new_thread(self.change_run,(newtop, task))
		#self.change_run(newtop, task)
		return task.id
		
	def _log(self, task, output):
		logger = log.Logger(config.log_dir+"/top_%s.log" % self.id)
		logger.log(task, bigmessage=output)
		
	def upload_image(self, device_id, filename):
		device = self.devices_get(device_id)
		if not device:
			os.remove(filename)
			raise fault.new(fault.NO_SUCH_DEVICE, "No such device: %s" % device_id)
		if not device.upcast().upload_supported():
			os.remove(filename)
			raise fault.new(fault.UPLOAD_NOT_SUPPORTED, "Device does not support image upload: %s" % device_id)
		if self.state == State.STARTED:
			os.remove(filename)
			raise fault.new(fault.INVALID_TOPOLOGY_STATE, "Cannot upload an image to a running topology")
		task = tasks.TaskStatus()
		thread.start_new_thread(device.upcast().upload_image, (filename, task))
		return task.id
	
	def download_image(self, device_id):
		device = self.devices_get(device_id)
		if not device:
			raise fault.new(fault.NO_SUCH_DEVICE, "No such device: %s" % device_id)
		if not device.upcast().download_supported():
			raise fault.new(fault.DOWNLOAD_NOT_SUPPORTED, "Device does not support image download: %s" % device_id)
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE, "Cannot download an image of a running topology")
		return device.upcast().download_image()

def get(id):
	return Topology.objects.get(id=id)

def all():
	return Topology.objects.all()

def create(dom, owner):
	top = Topology()
	top.init(dom, owner)
	return top