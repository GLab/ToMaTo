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
	def __init__(self, name, fn=None, args=(), kwargs={}, reverseFn=None, reverseArgs=(), reverseKwargs={}, onFinished=None, depends=[], callWithTask=False):
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
		if isinstance(depends, str):
			self.depends = [depends]
		else:
			self.depends = depends[:]
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
	def getOutput(self):
		return self.output.getvalue()
	def getResult(self):
		return self.result
	def getProcess(self):
		return self.process
	def getDependency(self, name):
		if name in self.depends:
			return self.process.tasksmap[name]
		else:
			for n in self.depends:
				if n.endswith(name):
					return self.getDependency(n)
			return None
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
				import traceback
				excstr = traceback.format_exc()
				fault.errors_add('%s:%s' % (exc.__class__.__name__, exc), excstr)
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
			"done": self.isDone(status), "depends": self.depends,
			"output": self.getOutput(), "result": "%s" % self.getResult(),
			"started": util.datestr(self.started) if self.started else None,
			"finished": util.datestr(self.finished) if self.finished else None,
			"duration": util.timediffstr(self.started, self.finished if self.finished else time.time()) if self.started else None,
			}
		
class TaskSet():
	def __init__(self):
		self.tasks = []
		self.tasksmap = {}
		self.firstTask = None
		self.lastTask = None
	def addTask(self, task):
		self.tasks.append(task)
		self.tasksmap[task.name] = task
		if self.firstTask:
			task.depends.append(self.firstTask.name)
		if self.lastTask:
			self.lastTask.depends.append(task.name)
		task.process = self
	def addTaskSet(self, prefix, taskset):
		taskset.addPrefix(prefix)
		for t in taskset.tasks:
			self.addTask(t)
	def addGlobalDepends(self, dep):
		for t in self.tasks:
			t.depends.append(dep)
		return self
	def addFirstTask(self, task):
		self.firstTask = None
		self.addTask(task)
		self.firstTask = task
		self._makeFirstTask(task)
	def addLastTask(self, task):
		self.lastTask = None
		self.addTask(task)
		self.lastTask = task
		self._makeLastTask(task)
	def addPrefix(self, prefix):
		oldnames = self.tasksmap.keys()[:] 
		self.tasksmap = {}
		for task in self.tasks:
			task.name = prefix + "-" + task.name
			self.tasksmap[task.name] = task
			newdeps = []
			for d in task.depends:
				if d in oldnames:
					newdeps.append(prefix + "-" + d)
				else:
					newdeps.append(d)
			task.depends = newdeps
		return self
	def _makeFirstTask(self, task):
		for t in self.tasks:
			if task != t:
				t.depends.append(task.name)		
	def _createFirstTask(self):
		task = Task("dummy-first")
		self._makeFirstTask(task)
		self.addFirstTask(task)
	def getFirstTask(self):
		if not self.firstTask:
			self._createFirstTask()
		self._makeFirstTask(self.firstTask)
		return self.firstTask
	def _makeLastTask(self, task):
		for t in self.tasks:
			if task != t:
				task.depends.append(t.name)
	def _createLastTask(self):
		task = Task("dummy-last")
		self._makeLastTask(task)
		self.addLastTask(task)
	def getLastTask(self):
		if not self.lastTask:
			self._createLastTask()
		self._makeLastTask(self.lastTask)
		return self.lastTask			
		
class Process():
	def __init__(self, name=None, tasks=[], onFinished=None):
		self.name = name
		self.tasks = []
		self.tasksmap = {}
		for t in tasks:
			self.addTask(t)
		self.onFinished = onFinished
		self.id = str(uuid.uuid1())
		processes[self.id]=self
		self.started = None
		self.finished = None
		self.trace = None
		self.lock = threading.Lock()
	def addTask(self, task):
		self.tasks.append(task)
		self.tasksmap[task.name] = task
		task.process = self
	def addTaskSet(self, prefix, taskset):
		taskset.addPrefix(prefix)
		for t in taskset.tasks:
			self.addTask(t)
	def abort(self):
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
	def _canrun(self, task):
		if task.status != Status.WAITING:
			return False
		assert not task.name in task.depends, "Task depends on itself: %s" % task.name
		for dep in task.depends:
			assert self.tasksmap.has_key(dep), "Undefined dependency: %s" % dep
			if self.tasksmap[dep].status != Status.SUCCEEDED:
				return False
		return True
	def _findTaskToRun(self):
		waiting = 0
		active = 0
		for task in self.tasks:
			if task.status == Status.WAITING:
				waiting += 1
			if task.isActive():
				active += 1
			if self._canrun(task):
				return task
		assert active or not waiting, "No tasks active but still some tasks waiting"
	def _runOnFinished(self):
		try:
			if self.onFinished:
				self.onFinished()
		except Exception, exc:
			import traceback
			fault.errors_add('%s:%s' % (exc.__class__.__name__, exc), traceback.format_exc())
	def run(self):
		self.started = time.time()
		while True:
			self.lock.acquire()
			task = self._findTaskToRun()
			if task:
				assert task.status == Status.WAITING
				task.status = Status.RUNNING
				self.lock.release()
				task.run()
				if task.status != Status.SUCCEEDED:
					self.abort()
					self.finished = time.time()
					self._runOnFinished()
					return
			else:
				self.lock.release()
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
			if direct:
				self.run()
				return self.dict()
			else:
				import traceback
				workers = max(min(min(MAX_WORKERS - workerthreads, MAX_WORKERS_PROCESS), len(self.tasks)), 1)
				while workers>0:
					util.start_thread(self._worker)
					workers -= 1
				return self.id
		except:
			import traceback
			traceback.print_exc()
	def _worker(self):
		global workerthreads
		workerthreads += 1
		try:
			self.run()
		except:
			import traceback
			#FIXME: handle exception properly
			traceback.print_exc()
		finally:
			workerthreads -= 1

	def check_delete(self):
		if (self.started and time.time() - self.started > 3600*24*3) or (self.finished and time.time() - self.finished > 3600 and not self.isActive()):
			if not os.path.exists(config.log_dir + "/tasks"):
				os.makedirs(config.log_dir + "/tasks")
			logger = log.getLogger(config.log_dir + "/tasks/%s"%self.id)
			logger.lograw(self.dict())
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
		
if not config.TESTING and not config.MAINTENANCE:	
	cleanup_task = util.RepeatedTimer(3, cleanup)
	cleanup_task.start()
	atexit.register(cleanup_task.stop)
	atexit.register(keep_running)