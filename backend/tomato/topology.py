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

	resources = models.ForeignKey(generic.ResourceSet, null=True)

	STOP_TIMEOUT = datetime.timedelta(weeks=config.timeout_stop_weeks)
	DESTROY_TIMEOUT = datetime.timedelta(weeks=config.timeout_destroy_weeks)
	REMOVE_TIMEOUT = datetime.timedelta(weeks=config.timeout_remove_weeks)

	def logger(self):
		if not os.path.exists(config.log_dir + "/top"):
			os.makedirs(config.log_dir + "/top")
		return log.get_logger(config.log_dir + "/top/%s"%self.id)

	def init (self, owner):
		"""
		Creates a new topology
		@param owner the owner of the topology
		"""
		self.owner=owner
		self.date_usage = datetime.datetime.now()
		self.save()
		self.name = "Topology_%s" % self.id
		self.save()

	def renew(self):
		self.date_usage = datetime.datetime.now()
		self.save()

	def max_state(self):
		max_state = generic.State.CREATED
		for con in self.connectors_all():
			if not con.is_special():
				if con.state == generic.State.PREPARED and max_state == generic.State.CREATED:
					max_state = generic.State.PREPARED
				if con.state == generic.State.STARTED and (max_state == generic.State.CREATED or max_state == generic.State.PREPARED):
					max_state = generic.State.STARTED
		for dev in self.devices_all():
			if dev.state == generic.State.PREPARED and max_state == generic.State.CREATED:
				max_state = generic.State.PREPARED
			if dev.state == generic.State.STARTED and (max_state == generic.State.CREATED or max_state == generic.State.PREPARED):
				max_state = generic.State.STARTED
		return max_state

	def check_timeout(self):
		now = datetime.datetime.now()
		if now > self.date_usage + self.REMOVE_TIMEOUT:
			self.logger().log("timeout: removing topology")
			self.remove()
		elif now > self.date_usage + self.DESTROY_TIMEOUT:
			self.logger().log("timeout: destroying topology")
			max_state = self.max_state()
			if max_state == generic.State.PREPARED or max_state == generic.State.STARTED:
				self.destroy(False)
		elif now > self.date_usage + self.STOP_TIMEOUT:
			self.logger().log("timeout: stopping topology")
			if self.max_state() == generic.State.STARTED:
				self.stop(False)
		
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
		return self.device_set.all() # pylint: disable-msg=E1101
	
	def devices_get(self, name):
		return self.device_set.get(name=name).upcast() # pylint: disable-msg=E1101

	def interfaces_get(self, iface_name):
		iface_name = iface_name.split(".")
		return self.devices_get(iface_name[0]).interfaces_get(iface_name[1])

	def devices_add(self, dev):
		if self.device_set.filter(name=dev.name).exclude(id=dev.id).count() > 0: # pylint: disable-msg=E1101
			raise fault.new(fault.DUPLICATE_DEVICE_ID, "Duplicate device id: %s" % dev.name)
		self.device_set.add(dev) # pylint: disable-msg=E1101

	def connectors_all(self):
		return self.connector_set.all() # pylint: disable-msg=E1101
	
	def connectors_get(self, name):
		return self.connector_set.get(name=name).upcast() # pylint: disable-msg=E1101

	def connectors_add(self, con):
		if self.connector_set.filter(name=con.name).exclude(id=con.id).count() > 0: # pylint: disable-msg=E1101
			raise fault.new(fault.DUPLICATE_CONNECTOR_ID, "Duplicate connector id: %s" % con.name)
		self.connector_set.add(con) # pylint: disable-msg=E1101

	def affected_hosts (self):
		"""
		The set of all hosts that this topology has devices on.
		"""
		import hosts
		return hosts.Host.objects.filter(device__topology=self).distinct() # pylint: disable-msg=E1101
	
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

	def stop(self, renew=True):
		"""
		Stops the topology.
		This will fail if the topology has not been prepared yet.
		"""
		if renew:
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

	def destroy(self, renew=True):
		"""
		Destroys the topology.
		This will fail if the topology has not been uploaded yet or is already started.
		"""
		if renew:
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
			
	def _log(self, task, output):
		logger = log.get_logger(config.log_dir+"/top_%s.log" % self.id)
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

	def download_capture(self, connector_id, device_id, interface_id):
		self.renew()
		if self.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		device = self.devices_get(device_id)
		if not device:
			raise fault.new(fault.NO_SUCH_DEVICE, "No such device: %s" % device_id)
		interface = device.interfaces_get(interface_id)
		if not interface:
			raise fault.new(fault.NO_SUCH_DEVICE, "No such interface: %s.%s" % (device_id, interface_id))
		con = interface.connection
		if not con.upcast().download_supported():
			raise fault.new(fault.DOWNLOAD_NOT_SUPPORTED, "Connection does not support capture download: %s" % con)
		return con.upcast().download_capture()

	def permissions_add(self, user_name, role):
		self.renew()
		self.permission_set.add(Permission(user=user_name, role=role)) # pylint: disable-msg=E1101
		self.save()
	
	def permissions_all(self):
		return self.permission_set.all() # pylint: disable-msg=E1101
	
	def permissions_remove(self, user_name):
		self.renew()
		self.permission_set.filter(user=user_name).delete() # pylint: disable-msg=E1101
		self.save()
		
	def permissions_get(self, user_name):
		set = self.permission_set.filter(user=user_name) # pylint: disable-msg=E1101
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

	def update_resource_usage(self):
		if not self.resources:
			r = generic.ResourceSet()
			r.save()
			self.resources = r 
			self.save()
		self.resources.clean()
		for dev in self.devices_all():
			self.resources.add(dev.update_resource_usage())
		for con in self.connectors_all():
			self.resources.add(con.update_resource_usage())
		self.resources.save()

	def to_dict(self, auth, detail):
		"""
		Prepares a topology for serialization.
		
		@type auth: boolean
		@param auth: Whether to include confidential information
		@type detail: boolean
		@param detail: Whether to include details of topology elements  
		@return: a dict containing information about the topology
		@rtype: dict
		"""
		res = {"id": self.id, "name": self.name, "state": self.max_state(), "owner": str(self.owner),
			"device_count": len(self.devices_all()), "connector_count": len(self.connectors_all()),
			"date_created": self.date_created, "date_modified": self.date_modified, "date_usage": self.date_usage
			}
		if detail:
			try:
				analysis = self.analysis()
			except Exception, exc:
				analysis = "Error in analysis: %s" % exc
				import traceback
				fault.errors_add('%s:%s' % (exc.__class__.__name__, exc), traceback.format_exc())
			res.update({"analysis": analysis, 
				"devices": [(v.name, v.to_dict(auth)) for v in self.devices_all()],
				"connectors": [(v.name, v.to_dict(auth)) for v in self.connectors_all()]
				})
			if auth:
				task = self.get_task()
				if self.resources:
					res.update(resources=self.resources.encode())
				if task:
					if task.is_active():
						res.update(running_task=task.id)
					else:
						res.update(finished_task=task.id)
				res.update(permissions=[p.to_dict() for p in self.permissions_all()])
				captures = []
				for con in self.connectors_all():
					for c in con.connections_all():
						c = c.upcast()
						if hasattr(c, "download_supported") and c.download_supported():
							captures.append({"connector":con.name, "device": c.interface.device.name, "interface": c.interface.name})
				res.update(captures=captures)
		return res

						
class Permission(models.Model):
	ROLE_USER="user"
	ROLE_MANAGER="manager"
	topology = models.ForeignKey(Topology)
	user = models.CharField(max_length=30)
	role = models.CharField(max_length=10, choices=((ROLE_USER, 'User'), (ROLE_MANAGER, 'Manager')))
	def to_dict(self):
		return {"user": self.user, "role": self.role}

def get(id):
	try:
		return Topology.objects.get(id=id) # pylint: disable-msg=E1101
	except Topology.DoesNotExist: # pylint: disable-msg=E1101
		raise fault.new(fault.NO_SUCH_TOPOLOGY, "No such topology: %s" % id)

def all():
	return Topology.objects.all() # pylint: disable-msg=E1101

def create(owner):
	top = Topology()
	top.init(owner)
	return top

def cleanup():
	for top in all():
		top.check_timeout()

def update_resource_usage():
	for top in all():
		top.update_resource_usage()

if not config.TESTING:
	cleanup_task = util.RepeatedTimer(300, cleanup)
	cleanup_task.start()
	atexit.register(cleanup_task.stop)
	update_resource_usage_task = util.RepeatedTimer(10000, update_resource_usage)
	update_resource_usage_task.start()
	atexit.register(update_resource_usage_task.stop)
