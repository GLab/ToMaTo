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

import uuid, os, threading
import util, atexit, time, log

from tomato import config, fault

from cStringIO import StringIO

class Status():
	WAITING = "waiting"
	RUNNING = "running"
	ABORTED = "aborted"
	SUCCEEDED = "succeeded"
	REVERSING = "reversing"
	FAILED = "failed"
	
class Task():
	def __init__(self, name, fn=None, args=(), kwargs={}, reverseFn=None, reverseArgs=(), reverseKwargs={}, onFinished=None, before=[], after=[], callWithTask=False):
		self.name = name
		self.fn = fn
		self.args = args
		self.kwargs = kwargs
		self.reverseFn = reverseFn
		self.reverseArgs = reverseArgs
		self.reverseKwargs = reverseKwargs
		self.onFinished = onFinished
		self.status = Status.WAITING
		self.output = StringIO()
		self.result = None
		self.process = None
		self.afterSet = set()
		self.beforeSet = set()
		self.after(after)
		self.before(before)
		self.callWithTask = callWithTask
		self.started = None
		self.finished = None
	def getStatus(self):
		return self.status
	def isActive(self, status=None):
		if not status:
			status = self.getStatus()
		return status == Status.RUNNING or status == Status.REVERSING
	def isDone(self, status=None):
		if not status:
			status = self.getStatus()
		return status == Status.FAILED or status == Status.ABORTED or status == Status.SUCCEEDED
	def isSucceeded(self):
		return self.status == Status.SUCCEEDED
	def getOutput(self):
		return self.output.getvalue()
	def getResult(self):
		return self.result
	def getBefore(self):
		return self.beforeSet
	def getAfter(self):
		return self.afterSet
	def after(self, task):
		if task == self:
			return
		if not isinstance(task, Task):
			for t in task:
				self.after(t)
		else:
			self.afterSet.add(task)
		return self
	def before(self, task):
		if task == self:
			return
		if not isinstance(task, Task):
			for t in task:
				self.before(t)
		else:
			self.beforeSet.add(task)
		return self
	def prefix(self, prefix):
		self.name = "%s-%s" % (prefix, self.name)
		return self
	def getProcess(self):
		return self.process
	def getDependency(self, name):
		for t in self.afterSet:
			if t.name.endswith(name):
				return t
		for t in self.beforeSet:
			if t.name.endswith(name):
				return t
	def _reverse(self):
		self.status = Status.REVERSING
		try:
			if self.callWithTask:
				self.result = self.reverseFn(self, *(self.reverseArgs), **(self.reverseKwargs))
			else:
				self.result = self.reverseFn(*(self.reverseArgs), **(self.reverseKwargs))
			self.status = Status.ABORTED
		except Exception, exc:
			self.status = Status.FAILED
			import traceback
			fault.errors_add('%s:%s' % (exc.__class__.__name__, exc), traceback.format_exc())
			self.output.write('%s:%s' % (exc.__class__.__name__, exc))
	def _run(self):
		#print "Running %s" % self.name
		self.status = Status.RUNNING
		if self.callWithTask:
			self.result = self.fn(self, *(self.args), **(self.kwargs))
		else:
			self.result = self.fn(*(self.args), **(self.kwargs))
		self.status = Status.SUCCEEDED
	def _runOnFinished(self):
		try:
			if self.onFinished:
				self.onFinished()
		except Exception, exc:
			import traceback
			fault.errors_add('%s:%s' % (exc.__class__.__name__, exc), traceback.format_exc())
	def run(self):
		set_current_task(self)
		self.started = time.time()
		assert self.status == Status.RUNNING
		if self.fn:
			try:
				self._run()
			except Exception, exc:
				self.result = exc
				fault.log(exc)
				self.output.write('%s:%s' % (exc.__class__.__name__, exc))
				if self.reverseFn:
					self._reverse()
				else:
					self.status = Status.FAILED
		else:
			self.status = Status.SUCCEEDED
		self._runOnFinished()
		self.finished = time.time()
	def dict(self):
		status = self.getStatus()
		return {"name": self.name, "status": status, "active": self.isActive(status),
			"done": self.isDone(status), "after": [t.name for t in self.afterSet], "before": [t.name for t in self.beforeSet],
			"output": self.getOutput(), "result": "%s" % self.getResult(),
			"started": util.datestr(self.started) if self.started else None,
			"finished": util.datestr(self.finished) if self.finished else None,
			"duration": util.timediffstr(self.started, self.finished if self.finished else time.time()) if self.started else None,
			}
		
class TaskSet():
	def __init__(self, tasks=[]):
		self.tasks = set()
		self.add(tasks)
	def find(self, name):
		for t in self:
			if t.name == name:
				return t
	def add(self, task):
		if not isinstance(task, Task):
			for t in task:
				self.add(t)
		else:
			self.tasks.add(task)
	def after(self, task):
		if not isinstance(task, Task):
			for t in task:
				self.after(t)
		else:
			for t in self.tasks:
				t.after(task)
		return self
	def before(self, task):
		if not isinstance(task, Task):
			for t in task:
				self.before(t)
		else:
			for t in self.tasks:
				t.before(task)
		return self
	def prefix(self, prefix):
		for t in self.tasks:
			t.prefix(prefix)
		return self
	def __len__(self):
		return len(self.tasks)
	def __iter__(self):
		return self.tasks.__iter__()
		
class Process():
	def __init__(self, name=None, tasks=[], onFinished=None):
		self.name = name
		self.tasks = set()
		for t in tasks:
			self.add(t)
		self.onFinished = onFinished
		self.id = str(uuid.uuid1())
		processes[self.id]=self
		self.started = None
		self.finished = None
		self.trace = None
		self.lock = threading.Lock()
		self.dependencies = {}
		self.readyTasks = set()
	def _prepare(self):
		for task in self.tasks:
			for t in task.getAfter():
				t.before(task)
			for t in task.getBefore():
				t.after(task)
		for task in self.tasks:
			self.dependencies[task] = set(task.getAfter())
			if not task.getAfter():
				self.readyTasks.add(task)
	def _taskDone(self, task):
		if task.status == Status.SUCCEEDED:
			for t in task.getBefore():
				self.dependencies[t].remove(task)
				if not self.dependencies[t] and t.status == Status.WAITING:
					self.readyTasks.add(t)
	def add(self, task):
		if not isinstance(task, Task):
			for t in task:
				self.add(t)
		else:
			self.tasks.add(task)
			task.process = self
	def abort(self):
		self.readyTasks.clear()
		for task in self.tasks:
			if task.status == Status.WAITING:
				task.status = Status.ABORTED
	def getStatus(self):
		for task in self.tasks:
			if task.status == Status.REVERSING:
				return Status.REVERSING
		for task in self.tasks:
			if task.status == Status.RUNNING:
				return Status.RUNNING
		for task in self.tasks:
			if task.status == Status.FAILED:
				return Status.FAILED
		for task in self.tasks:
			if task.status == Status.ABORTED:
				return Status.ABORTED
		for task in self.tasks:
			if task.status == Status.SUCCEEDED:
				return Status.SUCCEEDED
		if not self.tasks:
			return Status.SUCCEEDED
		return Status.WAITING
	def isActive(self, status=None):
		if not status:
			status = self.getStatus()
		return status == Status.RUNNING or status == Status.REVERSING
	def isDone(self, status=None):
		if not status:
			status = self.getStatus()
		return status == Status.FAILED or status == Status.ABORTED or status == Status.SUCCEEDED
	def _runOnFinished(self):
		try:
			if self.onFinished:
				self.onFinished()
		except Exception, exc:
			import traceback
			fault.errors_add('%s:%s' % (exc.__class__.__name__, exc), traceback.format_exc())
	def _getReadyTask(self):
		try:
			self.lock.acquire()
			if not self.readyTasks:
				return
			task = list(self.readyTasks)[0]
			self.readyTasks.remove(task)
			return task
		finally:
			self.lock.release()
	def run(self):
		self.started = time.time()
		while True:
			task = self._getReadyTask()
			if task:
				assert task.status == Status.WAITING
				task.status = Status.RUNNING
				task.run()
				if task.status == Status.SUCCEEDED:
					self._taskDone(task)
				else:
					self.abort()
					self.finished = time.time()
					self._runOnFinished()
					if isinstance(task.result, Exception):
						raise fault.new("Task failed: %s" % task.result, code=fault.USER_ERROR)
					else:
						return
			else:
				if not self.isActive():
					if not self.finished:
						self.finished = time.time()
						self._runOnFinished()
					return
				else:
					time.sleep(1)
	def dict(self):
		status = self.getStatus()
		res = {"id": self.id, "status": status, "active": self.isActive(status), 
			"done": self.isDone(status), "name": self.name,
			"started": util.datestr(self.started) if self.started else None,
			"finished": util.datestr(self.finished) if self.finished else None,
			"duration": util.timediffstr(self.started, self.finished if self.finished else time.time()) if self.started else None,
			"tasks":[], "tasks_total": len(self.tasks)}
		active = 0
		done = 0
		for task in self.tasks:
			d = task.dict()
			res["tasks"].append(d)
			if d["active"]:
				active += 1
			if d["done"]:
				done += 1
		res["tasks_active"] = active
		res["tasks_done"] = done			
		return res
	def start(self, direct=False):
		try:
			self._prepare()
			if direct:
				self.run()
				return self.dict()
			else:
				workers = max(min(min(MAX_WORKERS - workerthreads, MAX_WORKERS_PROCESS), len(self.tasks)), 1)
				while workers>0:
					util.start_thread(self._worker)
					workers -= 1
				return self.id
		except Exception, exc:
			fault.log(exc)
			if direct:
				raise
	def _worker(self):
		global workerthreads
		workerthreads += 1
		try:
			self.run()
		except Exception, exc:
			fault.log(exc)
		finally:
			workerthreads -= 1

	def check_delete(self):
		if (self.started and time.time() - self.started > 3600*24*3) or (self.finished and time.time() - self.finished > 3600 and not self.isActive()):
			if not os.path.exists(config.LOG_DIR + "/tasks"):
				os.makedirs(config.LOG_DIR + "/tasks")
			logger = log.getLogger(config.LOG_DIR + "/tasks/%s"%self.id)
			logger.lograw(str(self.dict()))
			logger.close()
			del processes[self.id]

MAX_WORKERS = 100
MAX_WORKERS_PROCESS = 5
workerthreads = 0
processes={}
					
def cleanup():
	for p in processes.values():
		p.check_delete()
		
def running_processes():
	running = []
	for p in processes.values():
		if p.isActive():
			running.append(p)
	return running
	
def keep_running():
	i = 0
	while running_processes() and i < 300:
		print "%s processes still running" % len(running_processes())
		time.sleep(10)
		i=i+10
		
_current_task = threading.local()

def set_current_task(task):
	_current_task.task = task

def get_current_task():
	if "task" in _current_task.__dict__:
		return _current_task.task
	else:
		return None
		
if not config.MAINTENANCE:	
	cleanup_task = util.RepeatedTimer(3, cleanup)
	cleanup_task.start()
	atexit.register(cleanup_task.stop)
	atexit.register(keep_running)
