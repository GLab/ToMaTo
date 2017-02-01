'''
Created on Jan 24, 2014

@author: dswd
'''

import threading, time, random
from .error import Error
from .exceptionhandling import wrap_and_handle_current_exception

MAX_WAIT = 3600.0

class Task(object):
	__slots__ = ("timeout", "repeated", "fn", "args", "kwargs", "next_timeout", "busy", "next", "last", "duration", "success")
	def __init__(self, fn, args=None, kwargs=None, timeout=0, repeated=False, immediate=False, random_offset=True):
		if not kwargs:
			kwargs = {}
		if not args:
			args = ()
		self.timeout = timeout
		self.repeated = repeated
		self.fn = fn
		self.args = args
		self.kwargs = kwargs

		# if random offset to be used as first timeout, next_timeout must be randomly selected.
		if random_offset:
			next_time = random.random() * timeout
		else:
			next_time = timeout

		# if there is an additional, immediate execution, next_time has to be used as next_timeout, and next_time must be 0.
		if immediate:
			self.next_timeout = next_time  # will be overwritten by self.timeout after first execute()
			next_time = 0
		else:
			self.next_timeout = timeout

		self.next = time.time() + next_time

		self.busy = False
		self.last = None
		self.duration = None
		self.success = None
	def execute(self):
		self.last = time.time()
		try:
			self.fn(*self.args, **self.kwargs)
			self.success = True
		except Exception, e:
			self.success = False
			if isinstance(e, Error):
				e.todump = True
			wrap_and_handle_current_exception(re_raise=False)
		self.duration = time.time()-self.last
		self.last = self.next
		if self.repeated:
			self.next = time.time() + self.next_timeout
			self.next_timeout = self.timeout
		else:
			self.next = 0
	def info(self):
		return {
			"method": (self.fn.__module__+"." if self.fn.__module__ else "")+self.fn.__name__,
			"busy": self.busy,
			"args": [str(arg) for arg in self.args],
			"kwargs": {name: str(value) for name, value in self.kwargs.items()},
			"repeated": self.repeated,
			"timeout": self.timeout,
			"next": self.next,
			"last": self.last,
			"duration": self.duration,
			"success": self.success
		}

class TaskScheduler(threading.Thread):
	__slots__ = ("tasks", "tasksLock", "nextId", "workers", "workersLock", "stopped", "wakeup", "stopped_confirm", "maxLateTime", "maxWorkers", "minWorkers", "waitFrac")
	DAILY = 3600*24
	def __init__(self, maxLateTime=2.0, maxWorkers=5, minWorkers=1):
		self.tasks = {}
		self.tasksLock = threading.RLock()
		self.nextId = 1
		self.workers = 0
		self.workersLock = threading.RLock()
		threading.Thread.__init__(self)
		self.stopped = False
		self.wakeup = threading.Event()
		self.stopped_confirm = threading.Event()
		self.maxLateTime = maxLateTime
		self.maxWorkers = maxWorkers
		self.minWorkers = minWorkers
		self.waitFrac = 0.5
		self.lastTask = 0
		self.taskRate = 0
	def _nextTask(self):
		try:
			with self.tasksLock:
				availableTasks = filter(lambda (tid, task): not task.busy, self.tasks.items())
				return min(availableTasks, key=lambda (tid, task): task.next)
		except ValueError:
			return (None, None)
	def _waitTime(self):
		with self.tasksLock:
			_, nextTask = self._nextTask()
			return min(nextTask.next - time.time(), MAX_WAIT) if nextTask else MAX_WAIT
	def _adaptWorkers(self, wait, mainThread):
		startThread = False
		with self.workersLock:
			self.waitFrac *= 0.99
			self.waitFrac += 0.01 if wait > 0.0 else 0.0
			if wait < -self.maxLateTime or self.waitFrac < 0.1:
				if self.workers < self.maxWorkers:
					self.workers += 1
					self.waitFrac = 0.5
					startThread = True
			if wait >= MAX_WAIT or self.waitFrac > 0.9:
				if self.workers > self.minWorkers and not mainThread:
					return False
			if self.workers < self.minWorkers:
				self.workers += 1
				self.waitFrac = 0.5
				startThread = True
		if startThread:
			threading.Thread(target=self._workerLoop).start()
		return True #continue running
	def _workerLoop(self, mainThread=False):
		while not self.stopped:
			wait = self._waitTime()
			if not self._adaptWorkers(wait, mainThread):
				break
			if wait > 0:
				self.wakeup.wait(wait)
				if self.stopped:
					break
			taskId, _ = self._nextTask()
			self.executeTask(taskId)
		with self.workersLock:
			self.waitFrac = 0.5
			self.workers -= 1
			if not self.workers:			
				self.stopped_confirm.set()
	def executeTask(self, taskId, force=False):
		with self.tasksLock:
			if not taskId in self.tasks:
				return
			task = self.tasks[taskId]
			if task.next > time.time() and not force:
				return
			if task.busy:
				return
			task.busy = True
		task.execute()
		now = time.time()
		if int(now) % 60 != int(self.lastTask) % 60:
			self.taskRate *= 0.5
		self.taskRate += 1.0
		self.lastTask = now
		with self.tasksLock:
			task.busy = False
			if not task.repeated:
				del self.tasks[taskId]
		return True
	def run(self):
		with self.workersLock:
			self.workers += 1
			while self.workers < self.minWorkers:
				self.workers += 1
				threading.Thread(target=self._workerLoop).start()
		self._workerLoop(True)
	def stop(self):
		self.stopped = True
		self.wakeup.set()
		self.stopped_confirm.wait()
	def _schedule(self, task):
		taskid = self.nextId
		self.tasks[taskid] = task
		self.nextId += 1
		self.wakeup.set()
		self.wakeup.clear()
		return taskid
	def scheduleOnce(self, timeout, fn, *args, **kwargs):
		return self._schedule(Task(fn, args, kwargs, timeout=timeout, repeated=False))
	def scheduleRepeated(self, timeout, fn, *args, **kwargs):
		#print "Ignoring task %s" % fn
		#return
		immediate = kwargs.pop("immediate", True)
		random_offset = kwargs.pop("random_offset", True)
		return self._schedule(Task(fn, args, kwargs, timeout=timeout, repeated=True, immediate=immediate, random_offset=random_offset))

	def scheduleMaintenance(self, timeout, keyfn, maintenancefn):
		"""
		schedule maintenance for multiple objects.
		Objects may be created or removed, without affecting maintenance (except for missing it once, maybe)
		:param timeout: interval in which to run maintenance (per object)
		:param keyfn: function which returns a list of object identifiers to be used by maintenancefn
		:param maintenancefn: function takes an object identifier as argument, and runs the maintenance.
		:return: maintenance scheduler id
		"""
		def maintenance_scheduler():
			to_sync = set(keyfn())
			current_tasks = {t.args[0]: tid for tid, t in self.tasks.items() if t.fn == maintenancefn}
			syncing = set(current_tasks.keys())
			for ident in to_sync - syncing:
				self.scheduleRepeated(timeout, maintenancefn, ident, random_offset=True, immediate=True)
			for ident in syncing - to_sync:
				self.cancelTask(current_tasks[ident])
		maintenance_scheduler.__name__ = "maintenance_scheduler:" + keyfn.__module__+"."+keyfn.__name__
		maintenance_scheduler.__module__ = ""
		self.scheduleRepeated(timeout, maintenance_scheduler, immediate=True)

	def cancelTask(self, taskId):
		with self.tasksLock:
			del self.tasks[taskId]
	def info(self):
		tasks = []
		with self.tasksLock:
			for id_, t in self.tasks.items():
				info = t.info()
				info["id"] = id_
				tasks.append(info)
		info = {
			"tasks": tasks,
			"max_late_time": self.maxLateTime,
			"max_workers": self.maxWorkers,
			"min_workers": self.minWorkers,
			"workers": self.workers,
			"wait_frac": self.waitFrac,
			"last_task": self.lastTask,
			"task_rate": self.taskRate / 2.0
		}
		return info
