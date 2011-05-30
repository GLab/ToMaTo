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
import config, fault, generic, attributes, auth

from lib import log, tasks, util, db

class Topology(attributes.Mixin, models.Model):
	"""
	This class represents a whole topology and offers methods to work with it
	"""
	
	id = models.AutoField(primary_key=True)
	# The id of the topology, this is an assigned value
	
	name = models.CharField(max_length=30, blank=True)
	# The name of the topology.

	owner = models.ForeignKey(auth.User)

	date_usage = models.DateTimeField(null=True)
	
	task = models.CharField(max_length=250, null=True)
		
	attrs = db.JSONField(default={})
		
	STOP_TIMEOUT = datetime.timedelta(weeks=config.TIMEOUTS["STOP"])
	DESTROY_TIMEOUT = datetime.timedelta(weeks=config.TIMEOUTS["DESTROY"])
	REMOVE_TIMEOUT = datetime.timedelta(weeks=config.TIMEOUTS["REMOVE"])

	def logger(self):
		if not os.path.exists(config.LOG_DIR + "/top"):
			os.makedirs(config.LOG_DIR + "/top")
		return log.getLogger(config.LOG_DIR + "/top/%s"%self.id)

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
		self.date_usage = datetime.datetime.now()
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
		date = self.date_usage
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
		if not self.task:
			return None
		if not tasks.processes.has_key(self.task):
			return None
		return tasks.processes[self.task]

	def isBusy(self):
		t = self.getTask()
		if not t:
			return False
		return t.isActive()

	def checkBusy(self):
		fault.check(not self.isBusy(), "Topology is busy with a task")

	def startProcess(self, process, direct=False):
		self.checkBusy()
		self.task = process.id
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
		exists = self.device_set.filter(name=dev.name).exclude(id=dev.id).count() > 0
		fault.check(not exists, "Duplicate device id: %s", dev.name)
		self.device_set.add(dev) # pylint: disable-msg=E1101

	def connectorSetAll(self):
		return self.connector_set.all() # pylint: disable-msg=E1101
	
	def connectorSetGet(self, name):
		return self.connector_set.get(name=name).upcast() # pylint: disable-msg=E1101

	def connectorSetAdd(self, con):
		exists = self.connector_set.filter(name=con.name).exclude(id=con.id).count() > 0 # pylint: disable-msg=E1101
		fault.check(not exists, "Duplicate connector id: %s", con.name)
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
		return config.LOCAL_TMP_DIR+"/"+host_name

	def getRemoteControlDir(self):
		"""
		The remote directory where all control scripts and files will be copied to.
		"""
		return config.REMOTE_DIR+"/"+str(self.id)

	def _getTasks(self):
		tmap = {"start": {}, "stop": {}, "prepare": {}, "destroy": {}}
		for dev in self.deviceSetAll():
			tmap["start"][dev] = dev.upcast().getStartTasks()
			tmap["stop"][dev] = dev.upcast().getStopTasks()
			tmap["prepare"][dev] = dev.upcast().getPrepareTasks()
			tmap["destroy"][dev] = dev.upcast().getDestroyTasks()
		for con in self.connectorSetAll():
			tmap["start"][con] = con.upcast().getStartTasks()
			tmap["stop"][con] = con.upcast().getStopTasks()
			tmap["prepare"][con] = con.upcast().getPrepareTasks()
			tmap["destroy"][con] = con.upcast().getDestroyTasks()
		return tmap
		
	def _stateForward(self, start, direct):
		proc = tasks.Process("topology-%s" % "start" if start else "prepare")
		proc.add(tasks.Task("renew", self.renew))
		tmap = self._getTasks()
		devs_prepare = tasks.TaskSet()
		for dev in self.deviceSetAll():
			if dev.state == generic.State.CREATED:
				devs_prepare.add(tmap["prepare"][dev])
		cons_prepare = tasks.TaskSet()
		for con in self.connectorSetAll():
			if con.state == generic.State.CREATED:
				cons_prepare.add(tmap["prepare"][con].after(devs_prepare))
		proc.add([devs_prepare, cons_prepare])
		if start:
			devs_start = tasks.TaskSet()
			for dev in self.deviceSetAll():
				if dev.state != generic.State.STARTED:
					devs_start.add(tmap["start"][dev].after([devs_prepare,cons_prepare]))
			cons_start = tasks.TaskSet()
			for con in self.connectorSetAll():
				if con.state != generic.State.STARTED:
					cons_start.add(tmap["start"][con].after([devs_prepare,cons_prepare]))
			proc.add([devs_start, cons_start])		
		return self.startProcess(proc, direct)

	def prepare(self, direct):
		return self._stateForward(False, direct)

	def start(self, direct):
		return self._stateForward(True, direct)

	def _stateBackward(self, destroy, remove, direct, renew):
		proc = tasks.Process("topology-%s" % "remove" if remove else "destroy" if destroy else "stop")
		if renew:
			proc.add(tasks.Task("renew", self.renew))
		tmap = self._getTasks()
		devs_stop = tasks.TaskSet()
		for dev in self.deviceSetAll():
			if dev.state == generic.State.STARTED:
				devs_stop.add(tmap["stop"][dev])
		cons_stop = tasks.TaskSet()
		for con in self.connectorSetAll():
			if con.state == generic.State.STARTED:
				cons_stop.add(tmap["stop"][con])
		proc.add([devs_stop, cons_stop])
		if destroy:
			cons_destroy = tasks.TaskSet()
			for con in self.connectorSetAll():
				if con.state != generic.State.CREATED:
					cons_destroy.add(tmap["destroy"][con].after([devs_stop,cons_stop]))
			devs_destroy = tasks.TaskSet()
			for dev in self.deviceSetAll():
				if dev.state != generic.State.CREATED:
					devs_destroy.add(tmap["destroy"][dev].after([devs_stop,cons_destroy]))
			proc.add([devs_destroy, cons_destroy])		
			if remove:
				proc.addTask(tasks.Task("remove", self.delete, after=[devs_destroy, cons_destroy]))
		return self.startProcess(proc, direct)

	def stop(self, direct, renew=True):
		return self._stateBackward(False, False, direct, renew)

	def destroy(self, direct, renew=True):
		return self._stateBackward(True, False, direct, renew)

	def remove(self, direct):
		return self._stateBackward(True, True, direct, False)
			
	def _log(self, task, output):
		logger = log.getLogger(config.LOG_DIR+"/top_%s.log" % self.id)
		logger.log(task, bigmessage=output)
		
	def downloadImageUri(self, device_id):
		self.renew()
		fault.check(not self.isBusy(), "Topology is busy with a task")
		device = self.deviceSetGet(device_id)
		fault.check(device, "No such device: %s", device_id)
		fault.check(device.upcast().downloadSupported(), "Device does not support image download: %s", device_id)
		return device.upcast().downloadImageUri()

	def downloadCaptureUri(self, connector_id, ifname): #@UnusedVariable, pylint: disable-msg=W0613
		self.renew()
		fault.check(not self.isBusy(), "Topology is busy with a task")
		interface = self.interfacesGet(ifname)
		fault.check(interface, "No such interface: %s", ifname)
		con = interface.connection.upcast()
		fault.check(con.downloadSupported(), "Connection does not support capture download: %s" , con)
		return con.downloadCaptureUri()

	def permissionsAdd(self, user_name, role):
		self.renew()
		self.permission_set.add(Permission(user=user_name, role=role)) # pylint: disable-msg=E1101
		self.save()
	
	def permissionsAll(self):
		return self.permission_set.all() # pylint: disable-msg=E1101
	
	def permissionsRemove(self, user_name):
		self.renew()
		self.permission_set.filter(user__name=user_name).delete() # pylint: disable-msg=E1101
		self.save()
		
	def permissionsGet(self, user):
		pset = self.permission_set.filter(user=user) # pylint: disable-msg=E1101
		if pset.count() > 0:
			return pset[0].role
		else:
			return None
		
	def checkAccess(self, atype, user):
		if user.is_admin:
			return True
		if user == self.owner:
			return True
		if atype == Permission.ROLE_MANAGER:
			return self.permissionsGet(user) == Permission.ROLE_MANAGER
		if atype == Permission.ROLE_USER:
			return self.permissionsGet(user) in [Permission.ROLE_USER, Permission.ROLE_MANAGER]

	def resources(self):
		return self.getAttribute("resources")

	def getIdUsage(self):
		ids = {}
		for dev in self.deviceSetAll():
			for (key, value) in dev.upcast().getIdUsage().iteritems():
				ids[key] = ids.get(key, set()) | value
		for con in self.connectorSetAll():
			for (key, value) in con.upcast().getIdUsage().iteritems():
				ids[key] = ids.get(key, set()) | value
		return ids

	def updateResourceUsage(self):
		res = {}
		for dev in self.deviceSetAll():
			dev.updateResourceUsage()
			r = dev.getAttribute("resources")
			for key in r:
				if not key in res:
					res[key] = 0
				res[key] += r[key]
		for con in self.connectorSetAll():
			con.updateResourceUsage()
			r = dev.getAttribute("resources")
			for key in r:
				if not key in res:
					res[key] = 0
				res[key] += r[key]
		self.setAttribute("resources", res)
		
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
		res = {"id": self.id, 
			"attrs": {"name": self.name, "state": self.maxState(), "owner": self.owner,
					"device_count": len(self.deviceSetAll()), "connector_count": len(self.connectorSetAll()),
					"stop_timeout": str(self.date_usage + self.STOP_TIMEOUT), "destroy_timeout": str(self.date_usage + self.DESTROY_TIMEOUT), "remove_timeout": str(self.date_usage + self.REMOVE_TIMEOUT) 
					},
			"resources": self.resources(),
			}
		if detail:
			res.update({"devices": dict([[v.name, v.upcast().toDict(auth)] for v in self.deviceSetAll()]),
				"connectors": dict([[v.name, v.upcast().toDict(auth)] for v in self.connectorSetAll()])
				})
			res.update(permissions=dict([[p.user, p.role] for p in self.permissionsAll()]))
			res["permissions"][self.owner]="owner";
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
	user = models.ForeignKey(auth.User)
	role = models.CharField(max_length=10, choices=((ROLE_USER, 'User'), (ROLE_MANAGER, 'Manager')))

	class Meta:
		unique_together = (("topology", "user"),)


def get(top_id):
	try:
		return Topology.objects.get(id=top_id) # pylint: disable-msg=E1101
	except Topology.DoesNotExist: # pylint: disable-msg=E1101
		raise fault.new("No such topology: %s" % top_id)

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

if not config.MAINTENANCE:
	cleanup_task = util.RepeatedTimer(300, cleanup)
	cleanup_task.start()
	atexit.register(cleanup_task.stop)
	update_resource_usage_task = util.RepeatedTimer(10000, updateResourceUsage)
	update_resource_usage_task.start()
	atexit.register(update_resource_usage_task.stop)
