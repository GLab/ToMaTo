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
			self.func(*self.args, task=self, **self.kwargs)
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
		
if not config.TESTING:	
	cleanup_task = util.RepeatedTimer(3, cleanup)
	cleanup_task.start()
	atexit.register(cleanup_task.stop)
	atexit.register(keep_running)