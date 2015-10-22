'''
Created on Jan 24, 2014

@author: dswd
'''

import threading, time

MAX_WAIT = 3600.0

class Task:
	def __init__(self, fn, args=None, kwargs=None, timeout=0, repeated=False, immediate=False):
		if not kwargs:
			kwargs = {}
		if not args:
			args = ()
		self.timeout = timeout
		self.repeated = repeated
		self.fn = fn
		self.args = args
		self.kwargs = kwargs
		self.next = time.time() + (0 if immediate else timeout) 
		self.busy = False
		self.last = None
		self.duration = None
	def execute(self):
		self.last = time.time()
		try:
			self.fn(*self.args, **self.kwargs)
		except Exception:
			import traceback
			traceback.print_exc()
		self.duration = time.time()-self.last
		self.last = self.next
		if self.repeated:
			self.next = time.time() + self.timeout
		else:
			self.next = 0
	def info(self):
		return {
			"method": self.fn.__module__+"."+self.fn.__name__,
			"busy": self.busy,
			"args": [str(arg) for arg in self.args],
			"kwargs": {name: str(value) for name, value in self.kwargs.items()},
			"repeated": self.repeated,
			"timeout": self.timeout,
			"next": self.next,
			"last": self.last,
			"duration": self.duration
		}

class TaskScheduler(threading.Thread):
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
		return self._schedule(Task(fn, args, kwargs, timeout=timeout, repeated=True, immediate=immediate))
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
			"wait_frac": self.waitFrac
		}
		return info
