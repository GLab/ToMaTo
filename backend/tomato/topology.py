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
import os, datetime, atexit
import config, fault, generic, attributes

from lib import log, tasks, util

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
		return log.getLogger(config.log_dir + "/top/%s"%self.id)

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

	def maxState(self):
		max_state = generic.State.CREATED
		for con in self.connectorSetAll():
			if not con.isExternal():
				if con.state == generic.State.PREPARED and max_state == generic.State.CREATED:
					max_state = generic.State.PREPARED
				if con.state == generic.State.STARTED and (max_state == generic.State.CREATED or max_state == generic.State.PREPARED):
					max_state = generic.State.STARTED
		for dev in self.deviceSetAll():
			if dev.state == generic.State.PREPARED and max_state == generic.State.CREATED:
				max_state = generic.State.PREPARED
			if dev.state == generic.State.STARTED and (max_state == generic.State.CREATED or max_state == generic.State.PREPARED):
				max_state = generic.State.STARTED
		return max_state

	def checkTimeout(self):
		now = datetime.datetime.now()
		date = datetime.datetime.strptime(self.attributes["date_usage"], "%Y-%m-%d %H:%M:%S.%f")
		if not date:
			return
		if now > date + self.REMOVE_TIMEOUT:
			self.logger().log("timeout: removing topology")
			self.remove(True)
		elif now > date + self.DESTROY_TIMEOUT:
			self.logger().log("timeout: destroying topology")
			max_state = self.maxState()
			if max_state == generic.State.PREPARED or max_state == generic.State.STARTED:
				self.destroy(False)
		elif now > date + self.STOP_TIMEOUT:
			self.logger().log("timeout: stopping topology")
			if self.maxState() == generic.State.STARTED:
				self.stop(False)
		
	def getTask(self):
		if not self.attributes["task"]:
			return None
		if not tasks.processes.has_key(self.attributes["task"]):
			return None
		return tasks.processes[self.attributes["task"]]

	def isBusy(self):
		t = self.getTask()
		if not t:
			return False
		return t.isActive()

	def checkBusy(self):
		if self.isBusy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")

	def startProcess(self, process, direct=False):
		self.checkBusy()
		self.attributes["task"] = process.id
		self.save()
		return process.start(direct)

	def deviceSetAll(self):
		return self.device_set.all() # pylint: disable-msg=E1101
	
	def deviceSetGet(self, name):
		return self.device_set.get(name=name).upcast() # pylint: disable-msg=E1101
	
	def interfacesGet(self, iface_name):
		iface_name = iface_name.split(".")
		return self.deviceSetGet(iface_name[0]).interfaceSetGet(iface_name[1])

	def deviceSetAdd(self, dev):
		if self.device_set.filter(name=dev.name).exclude(id=dev.id).count() > 0: # pylint: disable-msg=E1101
			raise fault.new(fault.DUPLICATE_DEVICE_ID, "Duplicate device id: %s" % dev.name)
		self.device_set.add(dev) # pylint: disable-msg=E1101

	def connectorSetAll(self):
		return self.connector_set.all() # pylint: disable-msg=E1101
	
	def connectorSetGet(self, name):
		return self.connector_set.get(name=name).upcast() # pylint: disable-msg=E1101

	def connectorSetAdd(self, con):
		if self.connector_set.filter(name=con.name).exclude(id=con.id).count() > 0: # pylint: disable-msg=E1101
			raise fault.new(fault.DUPLICATE_CONNECTOR_ID, "Duplicate connector id: %s" % con.name)
		self.connector_set.add(con) # pylint: disable-msg=E1101

	def affectedHosts (self):
		"""
		The set of all hosts that this topology has devices on.
		"""
		import hosts
		return hosts.Host.objects.filter(device__topology=self).distinct() # pylint: disable-msg=E1101
	
	def getControlDir(self,host_name):
		"""
		The local directory where all control scripts and files are stored.
		@param host_name the name of the host for the deployment
		"""
		return config.local_control_dir+"/"+host_name

	def getRemoteControlDir(self):
		"""
		The remote directory where all control scripts and files will be copied to.
		"""
		return config.remote_control_dir+"/"+str(self.id)

	def start(self, direct):
		proc = tasks.Process("topology-start")
		proc.addTask(tasks.Task("renew", self.renew))
		devs_prepared = []
		for dev in self.deviceSetAll():
			if dev.state == generic.State.CREATED:
				pset = dev.upcast().getPrepareTasks()
				proc.addTaskSet("prepare-device-%s" % dev.name, pset)
				devs_prepared.append(pset.getLastTask().name)
				sset = dev.upcast().getStartTasks()
				sset.addGlobalDepends(pset.getLastTask().name)
				proc.addTaskSet("start-device-%s" % dev.name, sset)
			elif dev.state == generic.State.PREPARED:
				sset = dev.upcast().getStartTasks()
				proc.addTaskSet("start-device-%s" % dev.name, sset)
		proc.addTask(tasks.Task("devices-prepared", depends=devs_prepared))
		for con in self.connectorSetAll():
			if con.state == generic.State.CREATED:
				pset = con.upcast().getPrepareTasks()
				pset.addGlobalDepends("devices-prepared")
				proc.addTaskSet("prepare-connector-%s" % con.name, pset)
				sset = con.upcast().getStartTasks()
				sset.addGlobalDepends(pset.getLastTask().name)
				sset.addGlobalDepends("devices-prepared")
				proc.addTaskSet("start-connector-%s" % con.name, sset)
			elif con.state == generic.State.PREPARED:
				sset = con.upcast().getStartTasks()
				sset.addGlobalDepends("devices-prepared")
				proc.addTaskSet("start-connector-%s" % con.name, sset)
		return self.startProcess(proc, direct)

	def stop(self, direct, renew=True):
		proc = tasks.Process("topology-stop")
		if renew:
			proc.addTask(tasks.Task("renew", self.renew))
		for dev in self.deviceSetAll():
			if dev.state == generic.State.PREPARED or dev.state == generic.State.STARTED:
				sset = dev.upcast().getStopTasks()
				proc.addTaskSet("stop-device-%s" % dev.name, sset)
		for con in self.connectorSetAll():
			if con.state == generic.State.PREPARED or con.state == generic.State.STARTED:
				sset = con.upcast().getStopTasks()
				proc.addTaskSet("stop-connector-%s" % con.name, sset)
		return self.startProcess(proc, direct)

	def prepare(self, direct):
		proc = tasks.Process("topology-prepare")
		proc.addTask(tasks.Task("renew", self.renew))
		devs_prepared = []
		for dev in self.deviceSetAll():
			if dev.state == generic.State.CREATED:
				pset = dev.upcast().getPrepareTasks()
				proc.addTaskSet("prepare-device-%s" % dev.name, pset)
				devs_prepared.append(pset.getLastTask().name)
		proc.addTask(tasks.Task("devices-prepared", depends=devs_prepared))
		for con in self.connectorSetAll():
			if con.state == generic.State.CREATED:
				pset = con.upcast().getPrepareTasks()
				pset.addGlobalDepends("devices-prepared")
				proc.addTaskSet("prepare-connector-%s" % con.name, pset)
		return self.startProcess(proc, direct)

	def destroy(self, direct, renew=True):
		proc = tasks.Process("topology-destroy")
		if renew:
			proc.addTask(tasks.Task("renew", self.renew))
		cons_destroyed = []	
		for con in self.connectorSetAll():
			if con.state == generic.State.STARTED:
				sset = con.upcast().getStopTasks()
				proc.addTaskSet("stop-connector-%s" % con.name, sset)
				dset = con.upcast().getDestroyTasks()
				dset.addGlobalDepends(sset.getLastTask().name)
				proc.addTaskSet("destroy-connector-%s" % con.name, dset)
				cons_destroyed.append(dset.getLastTask().name)
			elif con.state == generic.State.PREPARED:
				dset = con.upcast().getDestroyTasks()
				proc.addTaskSet("destroy-connector-%s" % con.name, dset)				
		proc.addTask(tasks.Task("connectors-destroyed", depends=cons_destroyed))				
		for dev in self.deviceSetAll():
			if dev.state == generic.State.STARTED:
				sset = dev.upcast().getStopTasks()
				proc.addTaskSet("stop-device-%s" % dev.name, sset)
				dset = dev.upcast().getDestroyTasks()
				dset.addGlobalDepends(sset.getLastTask().name)
				dset.addGlobalDepends("connectors-destroyed")
				proc.addTaskSet("destroy-device-%s" % dev.name, dset)
			elif dev.state == generic.State.PREPARED:
				dset = dev.upcast().getDestroyTasks()
				dset.addGlobalDepends("connectors-destroyed")
				proc.addTaskSet("destroy-device-%s" % dev.name, dset)
		return self.startProcess(proc, direct)

	def remove(self, direct):
		proc = tasks.Process("topology-remove")
		cons_destroyed = []	
		for con in self.connectorSetAll():
			if con.state == generic.State.STARTED:
				sset = con.upcast().getStopTasks()
				proc.addTaskSet("stop-connector-%s" % con.name, sset)
				dset = con.upcast().getDestroyTasks()
				dset.addGlobalDepends(sset.getLastTask().name)
				proc.addTaskSet("destroy-connector-%s" % con.name, dset)
				cons_destroyed.append(dset.getLastTask().name)
			elif con.state == generic.State.PREPARED:
				dset = con.upcast().getDestroyTasks()
				proc.addTaskSet("destroy-connector-%s" % con.name, dset)				
		proc.addTask(tasks.Task("connectors-destroyed", depends=cons_destroyed))				
		for dev in self.deviceSetAll():
			if dev.state == generic.State.STARTED:
				sset = dev.upcast().getStopTasks()
				proc.addTaskSet("stop-device-%s" % dev.name, sset)
				dset = dev.upcast().getDestroyTasks()
				dset.addGlobalDepends(sset.getLastTask().name)
				dset.addGlobalDepends("connectors-destroyed")
				proc.addTaskSet("destroy-device-%s" % dev.name, dset)
			elif dev.state == generic.State.PREPARED:
				dset = dev.upcast().getDestroyTasks()
				dset.addGlobalDepends("connectors-destroyed")
				proc.addTaskSet("destroy-device-%s" % dev.name, dset)
		proc.addTask(tasks.Task("remove", self.delete, depends=[t.name for t in proc.tasks]))
		return self.startProcess(proc, direct)
			
	def _log(self, task, output):
		logger = log.getLogger(config.log_dir+"/top_%s.log" % self.id)
		logger.log(task, bigmessage=output)
		
	def downloadImageUri(self, device_id):
		self.renew()
		if self.isBusy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		device = self.deviceSetGet(device_id)
		if not device:
			raise fault.new(fault.NO_SUCH_DEVICE, "No such device: %s" % device_id)
		if not device.upcast().downloadSupported():
			raise fault.new(fault.DOWNLOAD_NOT_SUPPORTED, "Device does not support image download: %s" % device_id)
		return device.upcast().downloadImageUri()

	def downloadCaptureUri(self, connector_id, ifname): #@UnusedVariable, pylint: disable-msg=W0613
		self.renew()
		if self.isBusy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		device_id, interface_id = ifname.split(".")
		device = self.deviceSetGet(device_id)
		if not device:
			raise fault.new(fault.NO_SUCH_DEVICE, "No such device: %s" % device_id)
		interface = device.interfaceSetGet(interface_id)
		if not interface:
			raise fault.new(fault.NO_SUCH_DEVICE, "No such interface: %s.%s" % (device_id, interface_id))
		con = interface.connection
		if not con.upcast().downloadSupported():
			raise fault.new(fault.DOWNLOAD_NOT_SUPPORTED, "Connection does not support capture download: %s" % con)
		return con.upcast().downloadCaptureUri()

	def permissionsAdd(self, user_name, role):
		self.renew()
		self.permission_set.add(Permission(user=user_name, role=role)) # pylint: disable-msg=E1101
		self.save()
	
	def permissionsAll(self):
		return self.permission_set.all() # pylint: disable-msg=E1101
	
	def permissionsRemove(self, user_name):
		self.renew()
		self.permission_set.filter(user=user_name).delete() # pylint: disable-msg=E1101
		self.save()
		
	def permissionsGet(self, user_name):
		pset = self.permission_set.filter(user=user_name) # pylint: disable-msg=E1101
		if pset.count() > 0:
			return pset[0].role
		else:
			return None
		
	def checkAccess(self, atype, user):
		if user.is_admin:
			return True
		if user.name == self.owner:
			return True
		if atype == Permission.ROLE_MANAGER:
			return self.permissionsGet(user.name) == Permission.ROLE_MANAGER
		if atype == Permission.ROLE_USER:
			return self.permissionsGet(user.name) in [Permission.ROLE_USER, Permission.ROLE_MANAGER]

	def resources(self):
		res = {}
		for key in self.attributes:
			if key.startswith("resources_"):
				res[key[10:]] = self.attributes[key]
		return res

	def updateResourceUsage(self):
		res = {}
		for dev in self.deviceSetAll():
			dev.updateResourceUsage()
			for key in dev.attributes:
				if key.startswith("resources_"):
					if not key in res:
						res[key] = 0
					res[key] += float(dev.attributes[key])
		for con in self.connectorSetAll():
			con.updateResourceUsage()
			for key in con.attributes:
				if key.startswith("resources_"):
					if not key in res:
						res[key] = 0
					res[key] += float(con.attributes[key])
		for key in res:
			self.attributes[key] = res[key]
		
	def toDict(self, auth, detail):
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
			"attrs": {"name": self.name, "state": self.maxState(), "owner": self.owner,
					"device_count": len(self.deviceSetAll()), "connector_count": len(self.connectorSetAll()),
					"stop_timeout": str(last_usage + self.STOP_TIMEOUT), "destroy_timeout": str(last_usage + self.DESTROY_TIMEOUT), "remove_timeout": str(last_usage + self.REMOVE_TIMEOUT) 
					}
			}
		res["attrs"].update(self.attributes.items())
		if detail:
			res.update({"devices": dict([[v.name, v.upcast().toDict(auth)] for v in self.deviceSetAll()]),
				"connectors": dict([[v.name, v.upcast().toDict(auth)] for v in self.connectorSetAll()])
				})
			res.update(permissions=dict([[p.user, p.role] for p in self.permissionsAll()]))
			res["permissions"][self.owner]="owner";
		if "task" in res["attrs"]:
			del res["attrs"]["task"]
		if auth:
			task = self.getTask()
			if task:
				if task.isActive():
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
		top.checkTimeout()

def updateResourceUsage():
	for top in all():
		top.updateResourceUsage()

if not config.TESTING and not config.MAINTENANCE:
	cleanup_task = util.RepeatedTimer(300, cleanup)
	cleanup_task.start()
	atexit.register(cleanup_task.stop)
	update_resource_usage_task = util.RepeatedTimer(10000, updateResourceUsage)
	update_resource_usage_task.start()
	atexit.register(update_resource_usage_task.stop)
