# -*- coding: utf-8 -*-

from django.db import models
import os, datetime, util, atexit
import config, log, fault, tasks
import topology_analysis, generic

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
		
	owner = models.CharField(max_length=30)

	date_created = models.DateTimeField(auto_now_add=True)
	
	date_modified = models.DateTimeField(auto_now=True)

	date_usage = models.DateTimeField()

	task = models.CharField(max_length=100, blank=True, null=True)

	STOP_TIMEOUT = datetime.timedelta(weeks=config.timeout_stop_weeks)
	DESTROY_TIMEOUT = datetime.timedelta(weeks=config.timeout_destroy_weeks)
	REMOVE_TIMEOUT = datetime.timedelta(weeks=config.timeout_remove_weeks)

	def logger(self):
		if not hasattr(self, "_logger"):
			if not os.path.exists(config.log_dir + "/top"):
				os.makedirs(config.log_dir + "/top")
			self._logger = log.Logger(config.log_dir + "/top/%s"%self.id)
		return self._logger

	def init (self, dom, owner):
		"""
		Creates a new topology
		@param file the xml file to load the topology definition from
		@param owner the owner of the topology
		"""
		self.owner=owner
		self.date_usage = datetime.datetime.now()
		self.save()
		try:
			self.load_from(dom)
		except:
			self.delete()
			raise
		if not self.name:
			self.name = "Topology_%s" % self.id
		self.save()

	def renew(self):
		self.date_usage = datetime.datetime.now()
		self.save()

	def check_timeout(self):
		now = datetime.datetime.now()
		if now > self.date_usage + self.REMOVE_TIMEOUT:
			self.logger().log("timeout: removing topology")
			self.remove()
		elif now > self.date_usage + self.DESTROY_TIMEOUT:
			self.logger().log("timeout: destroying topology")
			self.destroy()
		elif now > self.date_usage + self.STOP_TIMEOUT:
			self.logger().log("timeout: stopping topology")
			self.stop()

	def get_task(self):
		if not self.task:
			return None
		if not tasks.TaskStatus.tasks.has_key(self.task):
			return None
		return tasks.TaskStatus.tasks[self.task]

	def is_busy(self):
		t = self.get_task()
		if not t:
			return False
		return t.is_active()

	def start_task(self, func, *args, **kwargs):
		if self.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		task = tasks.TaskStatus(func, *args, **kwargs)
		task.start()
		self.task = task.id
		self.save()
		return task

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
		import openvz, kvm
		try:
			Type = { "openvz": openvz.OpenVZDevice, "kvm": kvm.KVMDevice }[dev.getAttribute("type")]
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
			dom.setAttribute("id", str(self.id))
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

	def start(self):
		"""
		Starts the topology.
		This will fail if the topology has not been prepared yet or is already started.
		"""
		self.renew()
		if len(self.analysis()["problems"]) > 0:
			raise fault.new(fault.TOPOLOGY_HAS_PROBLEMS, "topology has problems")
		task = self.start_task(self.start_run)
		return task.id

	def start_run(self, task):
		task.subtasks_total = self.devices_all().count() + self.connectors_all().count() 
		for dev in self.devices_all():
			if dev.state == generic.State.CREATED:
				task.subtasks_total = task.subtasks_total + 1
				task.output.write("\n# preparing " + dev.name + "\n") 
				dev.upcast().prepare_run(task)
		for con in self.connectors_all():
			if con.state == generic.State.CREATED:
				task.subtasks_total = task.subtasks_total + 1
				task.output.write("\n# preparing " + con.name + "\n") 
				con.upcast().prepare_run(task)
		for con in self.connectors_all():
			if con.state == generic.State.PREPARED:
				task.output.write("\n# starting " + con.name + "\n") 
				con.upcast().start_run(task)
		for dev in self.devices_all():
			if dev.state == generic.State.PREPARED:
				task.output.write("\n# starting " + dev.name + "\n") 
				dev.upcast().start_run(task)
		task.done()

	def stop(self):
		"""
		Stops the topology.
		This will fail if the topology has not been prepared yet.
		"""
		self.renew()
		task = self.start_task(self.stop_run)
		return task.id

	def stop_run(self, task):
		task.subtasks_total = self.devices_all().count() + self.connectors_all().count() 
		for dev in self.devices_all():
			if dev.state == generic.State.STARTED or dev.state == generic.State.PREPARED:
				task.output.write("\n# stopping " + dev.name + "\n") 
				dev.upcast().stop_run(task)
		for con in self.connectors_all():
			if con.state == generic.State.STARTED or con.state == generic.State.PREPARED:
				task.output.write("\n# stopping " + con.name + "\n") 
				con.upcast().stop_run(task)
		task.done()

	def prepare(self):
		"""
		Prepares the topology.
		This will fail if the topology is already prepared or started.
		"""
		self.renew()
		if len(self.analysis()["problems"]) > 0:
			raise fault.new(fault.TOPOLOGY_HAS_PROBLEMS, "topology has problems")
		task = self.start_task(self.prepare_run)
		return task.id

	def prepare_run(self, task):
		task.subtasks_total = self.devices_all().count() + self.connectors_all().count() 
		for dev in self.devices_all():
			if dev.state == generic.State.CREATED:
				task.output.write("\n# preparing " + dev.name + "\n") 
				dev.upcast().prepare_run(task)
		for con in self.connectors_all():
			if con.state == generic.State.CREATED:
				task.output.write("\n# preparing " + con.name + "\n") 
				con.upcast().prepare_run(task)
		task.done()

	def destroy(self):
		"""
		Destroys the topology.
		This will fail if the topology has not been uploaded yet or is already started.
		"""
		self.renew()
		task = self.start_task(self.destroy_run)
		return task.id

	def destroy_run(self, task):
		task.subtasks_total = self.devices_all().count() + self.connectors_all().count() 
		for con in self.connectors_all():
			if con.state == generic.State.STARTED or con.state == generic.State.PREPARED:
				task.subtasks_total = task.subtasks_total + 1
				task.output.write("\n# stopping " + con.name + "\n") 
				con.upcast().stop_run(task)
		for dev in self.devices_all():
			if dev.state == generic.State.STARTED or dev.state == generic.State.PREPARED:
				task.subtasks_total = task.subtasks_total + 1
				task.output.write("\n# stopping " + dev.name + "\n") 
				dev.upcast().stop_run(task)
		for con in self.connectors_all():
			if con.state == generic.State.PREPARED or con.state == generic.State.CREATED:
				task.output.write("\n# destroying " + con.name + "\n") 
				con.upcast().destroy_run(task)
		for dev in self.devices_all():
			if dev.state == generic.State.PREPARED or dev.state == generic.State.CREATED:
				task.output.write("\n# destroying " + dev.name + "\n") 
				dev.upcast().destroy_run(task)
		task.done()

	def remove(self):
		"""
		Removes the topology.
		"""
		task = self.start_task(self.remove_run)
		return task.id

	def remove_run(self, task):
		self.destroy_run(task)
		self.delete()
		task.done()
	
	def change_run(self, dom, task):
		devices=set()
		if dom.getAttribute("name"):
			self.name = dom.getAttribute("name")
		self.save()
		for x_dev in dom.getElementsByTagName("device"):
			name = x_dev.getAttribute("id")
			devices.add(name)
			try:
				dev = self.devices_get(name)
				# changed device
				dev.upcast().change_run(x_dev, task)
			except generic.Device.DoesNotExist:
				# new device
				self.devices_add_dom(x_dev)
		for dev in self.devices_all():
			if not dev.name in devices:
				#removed device
				if dev.state == generic.State.STARTED:
					dev.upcast().stop_run(task)
				if dev.state == generic.State.PREPARED or dev.state == generic.State.STARTED:
					dev.upcast().destroy_run(task)
				dev.delete()
		connectors=set()	
		for x_con in dom.getElementsByTagName("connector"):
			name = x_con.getAttribute("id")
			connectors.add(name)
			try:
				con = self.connectors_get(name)
				# changed device
				con.upcast().change_run(x_con, task)
			except generic.Connector.DoesNotExist:
				# new connector
				self.connectors_add_dom(x_con)
		for con in self.connectors_all():
			if not con.name in connectors:
				if con.state == generic.State.STARTED:
					con.upcast().stop_run(task)
				if con.state == generic.State.PREPARED or con.state == generic.State.STARTED:
					con.upcast().destroy_run(task)
				con.delete()				
		task.done()

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
		self.renew()
		self.change_possible(newtop)
		task = self.start_task(self.change_run,newtop)
		task.subtasks_total = 1
		return task.id
		
	def _log(self, task, output):
		logger = log.Logger(config.log_dir+"/top_%s.log" % self.id)
		logger.log(task, bigmessage=output)
		
	def upload_image(self, device_id, filename):
		self.renew()
		device = self.devices_get(device_id)
		if not device:
			os.remove(filename)
			raise fault.new(fault.NO_SUCH_DEVICE, "No such device: %s" % device_id)
		if not device.upcast().upload_supported():
			os.remove(filename)
			raise fault.new(fault.UPLOAD_NOT_SUPPORTED, "Device does not support image upload: %s" % device_id)
		task = self.start_task(device.upcast().upload_image, filename)
		return task.id
	
	def download_image(self, device_id):
		self.renew()
		if self.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		device = self.devices_get(device_id)
		if not device:
			raise fault.new(fault.NO_SUCH_DEVICE, "No such device: %s" % device_id)
		if not device.upcast().download_supported():
			raise fault.new(fault.DOWNLOAD_NOT_SUPPORTED, "Device does not support image download: %s" % device_id)
		return device.upcast().download_image()

	def permissions_add(self, user_name, role):
		self.renew()
		self.permission_set.add(Permission(user=user_name, role=role))
		self.save()
	
	def permissions_all(self):
		return self.permission_set.all()
	
	def permissions_remove(self, user_name):
		self.renew()
		self.permission_set.filter(user=user_name).delete()
		self.save()
		
	def permissions_get(self, user_name):
		set = self.permission_set.filter(user=user_name)
		if set.count() > 0:
			return set[0].role
		else:
			return None
		
	def check_access(self, type, user):
		if user.is_admin:
			return True
		if user.name == self.owner:
			return True
		if type == Permission.ROLE_MANAGER:
			return self.permissions_get(user.name) == Permission.ROLE_MANAGER
		if type == Permission.ROLE_USER:
			return self.permissions_get(user.name) in [Permission.ROLE_USER, Permission.ROLE_MANAGER]
		
class Permission(models.Model):
	ROLE_USER="user"
	ROLE_MANAGER="manager"
	topology = models.ForeignKey(Topology)
	user = models.CharField(max_length=30)
	role = models.CharField(max_length=10, choices=((ROLE_USER, 'User'), (ROLE_MANAGER, 'Manager')))
	def dict(self):
		return {"user": self.user, "role": self.role}

def get(id):
	try:
		return Topology.objects.get(id=id)
	except Topology.DoesNotExist:
		raise fault.new(fault.NO_SUCH_TOPOLOGY, "No such topology: %s" % id)

def all():
	return Topology.objects.all()

def create(dom, owner):
	top = Topology()
	top.init(dom, owner)
	return top

def cleanup():
	for top in all():
		top.check_timeout()

cleanup_task = util.RepeatedTimer(300, cleanup)
cleanup_task.start()
atexit.register(cleanup_task.stop)