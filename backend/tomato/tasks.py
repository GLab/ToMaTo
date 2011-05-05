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

import uuid, os, traceback, threading

import config, util, fault, atexit, time, log

from cStringIO import StringIO

class Status():
	WAITING = "waiting"
	RUNNING = "running"
	ABORTED = "aborted"
	SUCCEEDED = "succeeded"
	REVERSING = "reversing"
	FAILED = "failed"
	
class Task():
	def __init__(self, name, fn=None, reverseFn=None, onFinished=None, depends=[]):
		self.name = name
		self.fn = fn
		self.reverseFn = reverseFn
		self.onFinished = onFinished
		self.status = Status.WAITING
		self.output = StringIO()
		self.result = None
		self.process = None
		self.depends = depends[:]
	def getStatus(self):
		return self.status
	def getOutput(self):
		return self.output.getvalue()
	def getResult(self):
		return self.result
	def run(self):
		assert self.status == Status.WAITING
		self.status = Status.RUNNING
		if self.fn:
			try:
				depends = {}
				for dep in self.depends:
					depends[dep] = self.process.tasks[dep]
				self.result = self.fn(self, depends)
				self.status = Status.SUCCEEDED
			except Exception, exc:
				self.result = exc
				#FIXME: append stack trace and error message to output
				if self.reverseFn:
					self.status = Status.REVERSING
					try:
						self.reverseFn()
						self.status = Status.ABORTED
					except:
						#FIXME: append stack trace and error message to output
						self.status = Status.FAILED
				else:
					self.status = Status.FAILED
		else:
			self.status = Status.SUCCEEDED
		try:
			if self.onFinished:
				self.onFinished()
		except Exception, exc:
			import traceback
			traceback.print_exc()
	def dict(self):
		return {"name": self.name, "status": self.getStatus(), "output": self.getOutput(), "result": self.getResult()}
		
class Process():
	def __init__(self, name=None, tasks={}, onFinished=None):
		self.name = name
		self.tasks = tasks.copy()
		self.onFinished = onFinished
	def addTask(self, task):
		self.tasks[task.name] = task
		task.process = self
	def removeTask(self, taskname):
		del self.tasks[taskname]
	def getTask(self, taskname):
		return self.tasks[taskname]
	def abort(self):
		for task in self.tasks.values():
			if task.status == Status.WAITING:
				task.status = Status.ABORTED
	def getStatus(self):
		for task in self.tasks.values():
			if task.status == Status.FAILED:
				return Status.FAILED
		for task in self.tasks.values():
			if task.status == Status.REVERSING:
				return Status.REVERSING
		for task in self.tasks.values():
			if task.status == Status.RUNNING:
				return Status.RUNNING
		for task in self.tasks.values():
			if task.status == Status.ABORTED:
				return Status.ABORTED
		for task in self.tasks.values():
			if task.status == Status.SUCCEEDED:
				return Status.SUCCEEDED
		return Status.WAITING
	def _canrun(self, task):
		if task.status != Status.WAITING:
			return False
		for dep in task.depends:
			if self.tasks[dep].status != Status.SUCCEEDED:
				return False
		return True
	def _findTaskToRun(self):
		for task in self.tasks.values():
				if self._canrun(task):
					return task
	def _runOnFinished(self):
		try:
			if self.onFinished:
				self.onFinished()
		except:
			import traceback
			traceback.print_exc()
	def run(self):
		while True:
			task = self._findTaskToRun()
			if task:
				task.run()
				if task.status != Status.SUCCEEDED:
					self.abort()
					self._runOnFinished()
					return
			else:
				self._runOnFinished()
				return
	def dict(self):
		res = {"status": self.getStatus(), "name": self.name, "tasks":{}}
		for task in self.tasks.values():
			res["tasks"][task.name] = task.dict()
		return res
				
class TaskStatus():
	tasks={}
	ACTIVE = "active"
	DONE = "done"
	FAILED = "failed"
	def __init__(self, func, *args, **kwargs):
		self.id = str(uuid.uuid1())
		TaskStatus.tasks[self.id]=self
		self.func = func
		self.args = args
		self.kwargs = kwargs
		self.output = StringIO()
		self.subtasks_total = 0
		self.subtasks_done = 0
		self.status = TaskStatus.ACTIVE 
		self.started = time.time()
	def done(self):
		self.status = TaskStatus.DONE
		set_current_task(None)
	def failed(self):
		self.status = TaskStatus.FAILED
		set_current_task(None)
	def is_active(self):
		return self.status == TaskStatus.ACTIVE
	def dict(self):
		return {"id": self.id, "output": self.output.getvalue(), 
			"subtasks_done": self.subtasks_done, "subtasks_total": self.subtasks_total,
			"status": self.status, "active": self.status == TaskStatus.ACTIVE, 
			"failed": self.status == TaskStatus.FAILED, "done": self.status==TaskStatus.DONE,
			"started": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.started))}
	def _run(self):
		try:
			set_current_task(self)
			self.func(*self.args, **self.kwargs)
			self.done()
		except Exception, exc: #pylint: disable-msg=W0703
			if config.TESTING:
				traceback.print_exc()
			fault.errors_add('%s:%s' % (exc.__class__.__name__, exc), traceback.format_exc())
			self.output.write('%s:%s' % (exc.__class__.__name__, exc))
			self.failed()
	def start(self):
		util.start_thread(self._run)
	def check_delete(self):
		if (time.time() - self.started > 3600*24*3) or (time.time() - self.started > 3600 and self.status == TaskStatus.DONE):
			if not os.path.exists(config.log_dir + "/tasks"):
				os.makedirs(config.log_dir + "/tasks")
			logger = log.get_logger(config.log_dir + "/tasks/%s"%self.id)
			logger.lograw(self.output.getvalue())
			logger.close()
			del TaskStatus.tasks[self.id]
	
def cleanup():
	for task in TaskStatus.tasks.values():
		task.check_delete()
		
def running_tasks():
	tasks = []
	for task in TaskStatus.tasks.values():
		if task.is_active():
			tasks.append(task)
	return tasks
	
def keep_running():
	i = 0;
	while running_tasks() and i < 300:
		print "%s tasks still running" % len(running_tasks())
		time.sleep(1)
		i=i+1
		
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