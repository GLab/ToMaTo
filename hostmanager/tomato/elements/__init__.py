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

import os, shutil, time, os.path, datetime, abc
from django.db import models
from threading import RLock,Lock

from ..user import User
from ..connections import Connection
from ..accounting import UsageStatistics, Usage
from ..lib import db, attributes, util, logging, cmd #@UnresolvedImport
from ..lib.attributes import Attr #@UnresolvedImport
from ..lib.decorators import *
from .. import config, dump, scheduler
from ..lib.cmd import fileserver, process, net, path #@UnresolvedImport

ST_CREATED = "created"
ST_PREPARED = "prepared"
ST_STARTED = "started"

TYPES = {}
REMOVE_ACTION = "(remove)"

class Element(db.ChangesetMixin, attributes.Mixin, models.Model):
	type = models.CharField(max_length=20, validators=[db.nameValidator], choices=[(t, t) for t in TYPES.keys()]) #@ReservedAssignment
	owner = models.ForeignKey(User, related_name='elements')
	parent = models.ForeignKey('self', null=True, related_name='children')
	connection = models.ForeignKey(Connection, null=True, related_name='elements')
	usageStatistics = models.OneToOneField(UsageStatistics, null=True, related_name='element')
	state = models.CharField(max_length=20, validators=[db.nameValidator])
	timeout = models.FloatField()
	timeout_attr = Attr("timeout", desc="Timeout", states=[], type="float", null=False)
	attrs = db.JSONField()
	
	DOC = ""
	CAP_ACTIONS = {}
	CAP_NEXT_STATE = {}
	CAP_ATTRS = {"timeout": timeout_attr}
	CAP_CHILDREN = {}
	CAP_PARENT = []
	CAP_CON_CONCEPTS = []
	DEFAULT_ATTRS = {}
	
	class Meta:
		pass

	def init(self, parent=None, attrs={}):
		if parent:
			fault.check(parent.type in self.CAP_PARENT, "Parent type %s not allowed for type %s", (parent.type, self.type))
			fault.check(self.type in parent.CAP_CHILDREN, "Parent type %s does not allow children of type %s", (parent.type, self.type))
			fault.check(parent.state in parent.CAP_CHILDREN[self.type], "Parent type %s does not allow children of type %s in state %s", (parent.type, self.type, parent.state))
		else:
			fault.check(None in self.CAP_PARENT, "Type %s needs parent", self.type)
		self.parent = parent
		self.owner = currentUser()
		self.attrs = dict(self.DEFAULT_ATTRS)
		self.timeout = time.time() + config.MAX_TIMEOUT
		self.save()
		self.getUsageStatistics() #triggers creation
		if not os.path.exists(self.dataPath()):
			os.makedirs(self.dataPath())
		self.modify(attrs)

	def dump(self, **kwargs):
		try:
			data = self.info()
		except Exception, ex:
			data = {"info_exception": str(ex), "type": self.type, "id": self.id, "state": self.state, "attrs": self.attrs}
		dump.dump(connection=data, **kwargs)
		
	def dumpException(self, **kwargs):
		try:
			data = self.info()
		except Exception, ex:
			data = {"info_exception": str(ex), "type": self.type, "id": self.id, "state": self.state, "attrs": self.attrs}
		dump.dumpException(connection=data, **kwargs)

	def getUsageStatistics(self):
		if not self.usageStatistics:
			# only happens during object creation or when object creation failed
			stats = UsageStatistics()
			stats.init()
			stats.save()
			self.usageStatistics = stats
		return self.usageStatistics

	def _saveAttributes(self):
		pass #disable automatic attribute saving

	def isBusy(self):
		return hasattr(self, "_busy") and self._busy
	
	def setBusy(self, busy):
		self._busy = busy
		
	def dataPath(self, filename=""):
		"""
		This method can be used to create filenames relative to a directory
		that is specific for this object. The base directory is created when 
		this object is initialized and recursively removed when the object is
		removed.
		
		All custom files should use paths relative to the base directory.
		Note: If filename contains folder names the using class must take care
			that they exist.
		
		@param filename: a filename relative to the data path
		@type filename: str
		"""
		return os.path.join(config.DATA_DIR, self.TYPE, str(self.id), filename)		
		
	def upcast(self):
		"""
		This method returns an instance of this element with the highest order
		class that it possesses. Due to a limitation of the database backend,
		all loaded objects are of the type that has been used to load them.
		In order to get to their actual type this method must be called.
		
		Classes inheriting from this class should overwrite this method to 
		return self.
		"""
		try:
			return getattr(self, self.type)
		except:
			pass
		fault.raise_("Failed to cast element #%d to type %s" % (self.id, self.type), code=fault.INTERNAL_ERROR)

	def hasParent(self):
		return not self.parent is None

	def checkModify(self, attrs):
		"""
		Checks whether the attribute change can succeed before changing the
		attributes.
		If checks whether the attributes are listen in CAP_ATTRS and if the
		current object state is listed in CAP_ATTRS[NAME].
		
		@param attrs: Attributes to change
		@type attrs: dict
		"""
		fault.check(not self.isBusy(), "Object is busy", code=fault.OBJECT_BUSY)
		for key in attrs.keys():
			fault.check(key in self.CAP_ATTRS, "Unsuported attribute for %s: %s", (self.type, key), code=fault.UNSUPPORTED_ATTRIBUTE)
			self.CAP_ATTRS[key].check(self, attrs[key])
		
	def modify_timeout(self, value):
		fault.check(value > time.time(), "Refusing to set timeout into the past")
		fault.check(value <= time.time() + config.MAX_TIMEOUT, "Refusing to set timeout too far into the future")
		self.timeout = value
		
	def modify(self, attrs):
		"""
		Sets the given attributes to their given values. This method first
		checks if the change can be made using checkModify() and then executes
		the attribute changes by calling modify_KEY(VALUE) for each key/value
		pair in attrs. After calling all these modify_KEY methods, it will save
		the object.
		
		Classes inheriting from this class should only implement the modify_KEY
		methods and not touch this method.  
		
		@param attrs: Attributes to change
		@type attrs: dict
		"""		
		self.checkModify(attrs)
		logging.logMessage("modify", category="element", id=self.id, attrs=attrs)
		self.setBusy(True)
		try:
			for key, value in attrs.iteritems():
				getattr(self, "modify_%s" % key)(value)
		except Exception, exc:
			if fault.unexpectedError(exc):
				self.dumpException()
			raise
		finally:
			self.setBusy(False)				
		self.save()
		logging.logMessage("info", category="element", id=self.id, info=self.info())			
	
	def checkAction(self, action):
		"""
		Checks if the action can be executed. This method checks if the action
		is listed in CAP_ACTIONS and if the current state is listed in 
		CAP_ACTIONS[action].
		
		@param action: Action to check
		@type action: str
		"""
		fault.check(not self.isBusy(), "Object is busy", code=fault.OBJECT_BUSY)
		fault.check(action in self.CAP_ACTIONS, "Unsuported action for %s: %s", (self.type, action), code=fault.UNSUPPORTED_ACTION)
		fault.check(self.state in self.CAP_ACTIONS[action], "Action %s of %s can not be executed in state %s", (action, self.type, self.state), code=fault.INVALID_STATE)
	
	def action(self, action, params):
		"""
		Executes the action with the given parameters. This method first
		checks if the action is possible using checkAction() and then executes
		the action by calling action_ACTION(**params). After calling the action
		method, it will save the object.
		
		Classes inheriting from this class should only implement the 
		action_ACTION method and not touch this method. 
		
		@param action: Name of the action
		@type action: str
		@param params: Parameters for the action
		@type params: dict
		"""
		self.checkAction(action)
		logging.logMessage("action start", category="element", id=self.id, action=action, params=params)
		self.setBusy(True)
		try:
			res = getattr(self, "action_%s" % action)(**params)
		except Exception, exc:
			if fault.unexpectedError(exc):
				self.dumpException()
			raise
		finally:
			self.setBusy(False)
		self.save()
		if action in self.CAP_NEXT_STATE:
			fault.check(self.state == self.CAP_NEXT_STATE[action], "Action %s of %s lead to wrong state, should be %s, was %s", (action, self.type, self.CAP_NEXT_STATE[action], self.state), fault.INTERNAL_ERROR)
		logging.logMessage("action end", category="element", id=self.id, action=action, params=params, res=res)
		logging.logMessage("info", category="element", id=self.id, info=self.info())			
		return res

	def checkRemove(self, recurse=True):
		fault.check(not self.isBusy(), "Object is busy", code=fault.OBJECT_BUSY)
		fault.check(recurse or self.children.empty(), "Cannot remove element with children")
		fault.check(not REMOVE_ACTION in self.CAP_ACTIONS or self.state in self.CAP_ACTIONS[REMOVE_ACTION], "Element type %s can not be removed in its state %s", (self.type, self.state), code=fault.INVALID_STATE)
		for ch in self.getChildren():
			ch.checkRemove(recurse=recurse)
		if self.connection:
			self.getConnection().checkRemove()

	def setState(self, state, recursive=False):
		if recursive:
			for ch in self.getChildren():
				ch.setState(state, True)
		self.state = state
		self.save()

	def remove(self, recurse=True):
		self.checkRemove(recurse)
		logging.logMessage("info", category="element", id=self.id, info=self.info())
		logging.logMessage("remove", category="element", id=self.id)
		if self.parent:
			self.getParent().onChildRemoved(self)
		for ch in self.getChildren():
			ch.remove(recurse=True)
		if self.connection:
			self.getConnection().remove()
		self.delete()
		if os.path.exists(self.dataPath()):
			shutil.rmtree(self.dataPath())
			
	def getParent(self):
		return self.parent.upcast() if self.parent else None
			
	def getChildren(self):
		return [el.upcast() for el in self.children.all()]
			
	def getConnection(self):
		return self.connection.upcast() if self.connection else None
		
	def triggerConnect(self):
		pass
		
	def onConnected(self):
		pass
	
	def onDisconnected(self):
		pass
			
	def onChildAdded(self, child):
		pass
	
	def onChildRemoved(self, child):
		pass
			
	def onTimeout(self):
		self.tearDown()
			
	def tearDown(self):
		if self.connection:
			self.getConnection().tearDown()
			self.connection = None
		if self.state == ST_STARTED:
			self.action_stop()
		if self.state == ST_PREPARED:
			self.action_destroy()
		for ch in self.getChildren():
			ch.tearDown()
		self.remove()			
			
	def getResource(self, type_, blacklist=[]):
		return resources.take(type_, self, blacklist=blacklist)
	
	def returnResource(self, type_, num):
		resources.give(type_, num, self)
		
	@classmethod	
	def cap_attrs(cls):
		return dict([(key, value.info()) for (key, value) in cls.CAP_ATTRS.iteritems()])
					
	def info(self):
		res = {
			"id": self.id,
			"type": self.type,
			"parent": self.parent.id if self.hasParent() else None,
			"state": self.state,
			"timeout": self.timeout,
			"attrs": self.attrs.copy(),
			"children": [ch.id for ch in self.getChildren()],
			"connection": self.connection.id if self.connection else None,
		}
		res['attrs']['rextfv_supported'] = False
		return res
		
	def updateUsage(self, usage, data):
		pass
	
	
class RexTFVElement:
	
	lock = Lock()
	rextfv_max_size = None
	
	@abc.abstractmethod
	def _nlxtp_path(self, filename):
		"""returns a join of the nlXTP path and filename"""
		return
	
	#overwrite if needed. called at the beginning/end of each nlxtp function.:
	def _nlxtp_make_readable(self):
		return
	
	def _nlxtp_make_writeable(self):
		return
	
	def _nlxtp_close(self):
		return

	#deletes all contents in the nlXTP folder. If needed inside a "with lock" block, call the function below.
	def _clear_nlxtp_contents(self):
		with self.lock:
			self._nlxtp_make_writeable()
			try:
				self._clear_nlxtp_contents__already_mounted()
			finally:
				self._nlxtp_close()
				
	def _clear_nlxtp_contents__already_mounted(self): #same function, but does not use the lock mechanism. Use if called inside a "with lock"
		folder = self._nlxtp_path("")
		if os.path.exists(folder):
			for the_file in os.listdir(folder):
				file_path = os.path.join(folder, the_file)
				if os.path.isfile(file_path):
					os.remove(file_path)
				else:
					shutil.rmtree(file_path)
		
	#copies the contents of the archive "filename" to the nlXTP directory.
	def _use_rextfv_archive(self, filename, keepOldFiles=False):
		with self.lock:
			self._nlxtp_make_writeable()
			try:
				fault.check(os.path.exists(filename), "No file has been uploaded")
				if self.rextfv_max_size is not None:
					fault.check(os.path.getsize(filename) < self.rextfv_max_size, "uploaded file is too large")
				if not keepOldFiles:
					self._clear_nlxtp_contents__already_mounted()
				if not os.path.exists(self._nlxtp_path("")):
					os.makedirs(self._nlxtp_path(""))
				path.extractArchive(filename, self._nlxtp_path(""), ["--no-same-owner"])
			finally:
				self._nlxtp_close()
		
	#copies the contents of the nlXTP directory to the archive.
	def _create_rextfv_archive(self, filename):
		with self.lock:
			self._nlxtp_make_readable()
			try:
				if os.path.exists(filename):
					os.remove(filename)
                    
                # try to pack 3 times. If this fails, throw a fault.
				tries_left = 3
				tar_success = False
				while tries_left>0:
					try:
						cmd.run(["tar", "--numeric-owner", "-czvf", filename, "-C", self._nlxtp_path(""), "."])
						tar_success = True
						break
					except:
						tries_left -= 1
					if tries_left > 0:
						time.sleep(1)
				fault.check(tar_success, "Error while packing the archive for download. This usually happens because the device is currently writing for this directory. Please try again later. If this error continues to occur, try to download while the device is stopped.")
			
			finally:
				self._nlxtp_close()
		
	#nlXTP's running status.
	#conventions: status path: exec_status, done-file: exec_status/done, running-file: exec_status/running
	def _rextfv_run_status(self):
		with self.lock:
			self._nlxtp_make_readable()
			try:
				
				# no nlXTP dir or no status dir - unreadable
				if (self._nlxtp_path("") is None) or (not os.path.exists(self._nlxtp_path("exec_status"))):
					return {"readable": False}
				
				# evaluate custom status
				customstat = None
				if (os.path.exists(self._nlxtp_path(os.path.join("exec_status","custom")))):
					with open(self._nlxtp_path(os.path.join("exec_status","custom")),"r") as f:
						customstat = f.read()
						
				# done file exists => not running
				if os.path.exists(self._nlxtp_path(os.path.join("exec_status","done"))):
					return {"readable": True, "done": True, "isAlive": False, "custom":customstat}
				
				# when we're here, done file does not exist. if no running file exists, status is unreadable
				#    (unknown state: if monitor has started, there's always a running or done file
				if not os.path.exists(self._nlxtp_path(os.path.join("exec_status","running"))):
					return {"readable": False}
				
				# when we're here, both running and done file exist.
				# now, check the timestamp in the file.
				with open(self._nlxtp_path(os.path.join("exec_status","running")), 'r') as f:
					timestamp = f.read()
				try:
					timestamp = int(timestamp)
				except:
					return {"readable": False}
				timeout=10*60 #seconds
				diff = time.time() - timestamp
				if diff > timeout: # timeout occured.
					return {"readable": True, "done": False, "isAlive": False, "custom":customstat}
				return {"readable": True, "done": False, "isAlive": True, "custom":customstat}
			finally:
				self._nlxtp_close()
		
	def info(self): #call to get rextfv information. merge with root of Element.info().
		if self.state == ST_CREATED:
			return {}
		res = {'attrs':{}}
		res['attrs']['rextfv_run_status'] = self._rextfv_run_status()
		res['attrs']['rextfv_max_size'] = self.rextfv_max_size
		res['attrs']['rextfv_supported'] = True
		return res

	
	

def get(id_, **kwargs):
	try:
		el = Element.objects.get(id=id_, **kwargs)
		return el.upcast()
	except Element.DoesNotExist:
		return None

def getAll(**kwargs):
	return (el.upcast() for el in Element.objects.filter(**kwargs))

def create(type_, parent=None, attrs={}):
	fault.check(type_ in TYPES, "Unsupported type: %s", type_)
	fault.check(not parent or parent.owner == currentUser(), "Parent element belongs to different user")
	el = TYPES[type_]()
	try:
		el.init(parent, attrs)
		el.save()
	except:
		el.remove()
		raise
	if parent:
		parent.onChildAdded(el)
	logging.logMessage("create", category="element", id=el.id)	
	logging.logMessage("info", category="element", id=el.id, info=el.info())	
	return el

@util.wrap_task
def checkTimeout():
	for el in Element.objects.filter(timeout__lte=time.time()):
		el = el.upcast()
		logging.logMessage("timeout", category="element", info=el.info())
		try:
			el.onTimeout()
		except:
			logging.logException()

scheduler.scheduleRepeated(3600, checkTimeout) #@UndefinedVariable

from .. import fault, currentUser, resources
		

