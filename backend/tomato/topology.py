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
import generic, attributes

class Topology(models.Model):
	"""
	This class represents a whole topology and offers methods to work with it
	"""
	
	id = models.AutoField(primary_key=True)
	# The id of the topology, this is an assigned value
	
	name = models.CharField(max_length=30, blank=True)
	# The name of the topology.

	owner = models.CharField(max_length=30)

	attributes = models.ForeignKey(attributes.AttributeSet, default=attributes.create)
		
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
		self.renew()
		self.name = "Topology_%s" % self.id
		self.save()

	def renew(self):
		self.attributes["date_usage"] = datetime.datetime.now()
		self.save()

	def max_state(self):
		max_state = generic.State.CREATED
		for con in self.connector_set_all():
			if not con.is_external():
				if con.state == generic.State.PREPARED and max_state == generic.State.CREATED:
					max_state = generic.State.PREPARED
				if con.state == generic.State.STARTED and (max_state == generic.State.CREATED or max_state == generic.State.PREPARED):
					max_state = generic.State.STARTED
		for dev in self.device_set_all():
			if dev.state == generic.State.PREPARED and max_state == generic.State.CREATED:
				max_state = generic.State.PREPARED
			if dev.state == generic.State.STARTED and (max_state == generic.State.CREATED or max_state == generic.State.PREPARED):
				max_state = generic.State.STARTED
		return max_state

	def check_timeout(self):
		now = datetime.datetime.now()
		date = datetime.datetime.strptime(self.attributes["date_usage"], "%Y-%m-%d %H:%M:%S.%f")
		if not date:
			return
		if now > date + self.REMOVE_TIMEOUT:
			self.logger().log("timeout: removing topology")
			self.remove(True)
		elif now > date + self.DESTROY_TIMEOUT:
			self.logger().log("timeout: destroying topology")
			max_state = self.max_state()
			if max_state == generic.State.PREPARED or max_state == generic.State.STARTED:
				self.destroy(False)
		elif now > date + self.STOP_TIMEOUT:
			self.logger().log("timeout: stopping topology")
			if self.max_state() == generic.State.STARTED:
				self.stop(False)
		
	def get_task(self):
		if not self.attributes["task"]:
			return None
		if not tasks.TaskStatus.tasks.has_key(self.attributes["task"]):
			return None
		return tasks.TaskStatus.tasks[self.attributes["task"]]

	def is_busy(self):
		t = self.get_task()
		if not t:
			return False
		return t.is_active()

	def start_task(self, func, direct=False, *args, **kwargs):
		if self.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		task = tasks.TaskStatus(func, *args, **kwargs)
		self.attributes["task"] = task.id
		self.save()
		if direct:
			task._run()
		else:
			task.start()
		return task

	def device_set_all(self):
		return self.device_set.all() # pylint: disable-msg=E1101
	
	def device_set_get(self, name):
		return self.device_set.get(name=name).upcast() # pylint: disable-msg=E1101
	
	def interfaces_get(self, iface_name):
		iface_name = iface_name.split(".")
		return self.device_set_get(iface_name[0]).interface_set_get(iface_name[1])

	def device_set_add(self, dev):
		if self.device_set.filter(name=dev.name).exclude(id=dev.id).count() > 0: # pylint: disable-msg=E1101
			raise fault.new(fault.DUPLICATE_DEVICE_ID, "Duplicate device id: %s" % dev.name)
		self.device_set.add(dev) # pylint: disable-msg=E1101

	def connector_set_all(self):
		return self.connector_set.all() # pylint: disable-msg=E1101
	
	def connector_set_get(self, name):
		return self.connector_set.get(name=name).upcast() # pylint: disable-msg=E1101

	def connector_set_add(self, con):
		if self.connector_set.filter(name=con.name).exclude(id=con.id).count() > 0: # pylint: disable-msg=E1101
			raise fault.new(fault.DUPLICATE_CONNECTOR_ID, "Duplicate connector id: %s" % con.name)
		self.connector_set.add(con) # pylint: disable-msg=E1101

	def affected_hosts (self):
		"""
		The set of all hosts that this topology has devices on.
		"""
		import hosts
		return hosts.Host.objects.filter(device__topology=self).distinct() # pylint: disable-msg=E1101
	
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

	def start(self, direct):
		"""
		Starts the topology.
		This will fail if the topology has not been prepared yet or is already started.
		"""
		self.renew()
		task = self.start_task(self.start_run, direct)
		return task.id

	def start_run(self):
		task = tasks.get_current_task()
		task.subtasks_total = self.device_set_all().count() + self.connector_set_all().count() 
		for dev in self.device_set_all():
			if dev.state == generic.State.CREATED:
				task.subtasks_total = task.subtasks_total + 1
				task.output.write("\n# preparing " + dev.name + "\n") 
				dev.upcast().prepare_run()
		for con in self.connector_set_all():
			if con.state == generic.State.CREATED:
				task.subtasks_total = task.subtasks_total + 1
				task.output.write("\n# preparing " + con.name + "\n") 
				con.upcast().prepare_run()
		for con in self.connector_set_all():
			if con.state == generic.State.PREPARED:
				task.output.write("\n# starting " + con.name + "\n") 
				con.upcast().start_run()
		for dev in self.device_set_all():
			if dev.state == generic.State.PREPARED:
				task.output.write("\n# starting " + dev.name + "\n") 
				dev.upcast().start_run()

	def stop(self, direct, renew=True):
		"""
		Stops the topology.
		This will fail if the topology has not been prepared yet.
		"""
		if renew:
			self.renew()
		task = self.start_task(self.stop_run, direct)
		return task.id

	def stop_run(self):
		task = tasks.get_current_task()
		task.subtasks_total = self.device_set_all().count() + self.connector_set_all().count() 
		for dev in self.device_set_all():
			if dev.state == generic.State.STARTED or dev.state == generic.State.PREPARED:
				task.output.write("\n# stopping " + dev.name + "\n") 
				dev.upcast().stop_run()
		for con in self.connector_set_all():
			if con.state == generic.State.STARTED or con.state == generic.State.PREPARED:
				task.output.write("\n# stopping " + con.name + "\n") 
				con.upcast().stop_run()

	def prepare(self, direct):
		"""
		Prepares the topology.
		This will fail if the topology is already prepared or started.
		"""
		self.renew()
		task = self.start_task(self.prepare_run, direct)
		return task.id

	def prepare_run(self):
		task = tasks.get_current_task()
		task.subtasks_total = self.device_set_all().count() + self.connector_set_all().count() 
		for dev in self.device_set_all():
			if dev.state == generic.State.CREATED:
				task.output.write("\n# preparing " + dev.name + "\n") 
				dev.upcast().prepare_run()
		for con in self.connector_set_all():
			if con.state == generic.State.CREATED:
				task.output.write("\n# preparing " + con.name + "\n") 
				con.upcast().prepare_run()

	def destroy(self, direct, renew=True):
		"""
		Destroys the topology.
		This will fail if the topology has not been uploaded yet or is already started.
		"""
		if renew:
			self.renew()
		task = self.start_task(self.destroy_run, direct)
		return task.id

	def destroy_run(self):
		task = tasks.get_current_task()
		task.subtasks_total = self.device_set_all().count() + self.connector_set_all().count() 
		for con in self.connector_set_all():
			if con.state == generic.State.STARTED or con.state == generic.State.PREPARED:
				task.subtasks_total = task.subtasks_total + 1
				task.output.write("\n# stopping " + con.name + "\n") 
				con.upcast().stop_run()
		for dev in self.device_set_all():
			if dev.state == generic.State.STARTED or dev.state == generic.State.PREPARED:
				task.subtasks_total = task.subtasks_total + 1
				task.output.write("\n# stopping " + dev.name + "\n") 
				dev.upcast().stop_run()
		for con in self.connector_set_all():
			if con.state == generic.State.PREPARED or con.state == generic.State.CREATED:
				task.output.write("\n# destroying " + con.name + "\n") 
				con.upcast().destroy_run()
		for dev in self.device_set_all():
			if dev.state == generic.State.PREPARED or dev.state == generic.State.CREATED:
				task.output.write("\n# destroying " + dev.name + "\n") 
				dev.upcast().destroy_run()
		task.done()

	def remove(self, direct):
		"""
		Removes the topology.
		"""
		task = self.start_task(self.remove_run, direct)
		return task.id

	def remove_run(self):
		self.destroy_run()
		self.delete()
			
	def _log(self, task, output):
		logger = log.get_logger(config.log_dir+"/top_%s.log" % self.id)
		logger.log(task, bigmessage=output)
		
	def download_image_uri(self, device_id):
		self.renew()
		if self.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		device = self.device_set_get(device_id)
		if not device:
			raise fault.new(fault.NO_SUCH_DEVICE, "No such device: %s" % device_id)
		if not device.upcast().download_supported():
			raise fault.new(fault.DOWNLOAD_NOT_SUPPORTED, "Device does not support image download: %s" % device_id)
		return device.upcast().download_image_uri()

	def download_capture_uri(self, connector_id, ifname): #@UnusedVariable, pylint: disable-msg=W0613
		self.renew()
		if self.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		device_id, interface_id = ifname.split(".")
		device = self.device_set_get(device_id)
		if not device:
			raise fault.new(fault.NO_SUCH_DEVICE, "No such device: %s" % device_id)
		interface = device.interface_set_get(interface_id)
		if not interface:
			raise fault.new(fault.NO_SUCH_DEVICE, "No such interface: %s.%s" % (device_id, interface_id))
		con = interface.connection
		if not con.upcast().download_supported():
			raise fault.new(fault.DOWNLOAD_NOT_SUPPORTED, "Connection does not support capture download: %s" % con)
		return con.upcast().download_capture_uri()

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
		pset = self.permission_set.filter(user=user_name) # pylint: disable-msg=E1101
		if pset.count() > 0:
			return pset[0].role
		else:
			return None
		
	def check_access(self, atype, user):
		if user.is_admin:
			return True
		if user.name == self.owner:
			return True
		if atype == Permission.ROLE_MANAGER:
			return self.permissions_get(user.name) == Permission.ROLE_MANAGER
		if atype == Permission.ROLE_USER:
			return self.permissions_get(user.name) in [Permission.ROLE_USER, Permission.ROLE_MANAGER]

	def update_resource_usage(self):
		res = {}
		for dev in self.device_set_all():
			dev.update_resource_usage()
			for key in dev.attributes:
				if key.startswith("resources_"):
					if not key in res:
						res[key] = 0
					res[key] += float(dev.attributes[key])
		for con in self.connector_set_all():
			con.update_resource_usage()
			for key in con.attributes:
				if key.startswith("resources_"):
					if not key in res:
						res[key] = 0
					res[key] += float(con.attributes[key])
		for key in res:
			self.attributes[key] = res[key]
		
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
		last_usage = datetime.datetime.strptime(self.attributes["date_usage"], "%Y-%m-%d %H:%M:%S.%f")
		res = {"id": self.id, 
			"attrs": {"name": self.name, "state": self.max_state(), "owner": self.owner,
					"device_count": len(self.device_set_all()), "connector_count": len(self.connector_set_all()),
					"stop_timeout": str(last_usage + self.STOP_TIMEOUT), "destroy_timeout": str(last_usage + self.DESTROY_TIMEOUT), "remove_timeout": str(last_usage + self.REMOVE_TIMEOUT) 
					}
			}
		res["attrs"].update(self.attributes.items())
		if detail:
			res.update({"devices": dict([[v.name, v.upcast().to_dict(auth)] for v in self.device_set_all()]),
				"connectors": dict([[v.name, v.upcast().to_dict(auth)] for v in self.connector_set_all()])
				})
			res.update(permissions=dict([[p.user, p.role] for p in self.permissions_all()]))
			res["permissions"][self.owner]="owner";
		if "task" in res["attrs"]:
			del res["attrs"]["task"]
		if auth:
			task = self.get_task()
			if task:
				if task.is_active():
					res.update(running_task=task.id)
				else:
					res.update(finished_task=task.id)

		return res

						
class Permission(models.Model):
	ROLE_USER="user"
	ROLE_MANAGER="manager"
	topology = models.ForeignKey(Topology)
	user = models.CharField(max_length=30)
	role = models.CharField(max_length=10, choices=((ROLE_USER, 'User'), (ROLE_MANAGER, 'Manager')))

def get(top_id):
	try:
		return Topology.objects.get(id=top_id) # pylint: disable-msg=E1101
	except Topology.DoesNotExist: # pylint: disable-msg=E1101
		raise fault.new(fault.NO_SUCH_TOPOLOGY, "No such topology: %s" % top_id)

def all(): #pylint: disable-msg=W0622
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
