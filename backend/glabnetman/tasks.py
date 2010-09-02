# -*- coding: utf-8 -*-

import uuid, os

import config, util, atexit, time, log

from cStringIO import StringIO

class TaskStatus():
	tasks={}
	def __init__(self):
		self.id = str(uuid.uuid1())
		TaskStatus.tasks[self.id]=self
		self.output = StringIO()
		self.subtasks_total = 0
		self.subtasks_done = 0
		self.started = time.time()
	def done(self):
		self.subtasks_done = self.subtasks_total
	def is_active(self):
		return self.subtasks_done < self.subtasks_total
	def dict(self):
		return {"id": self.id, "output": self.output.getvalue(), "subtasks_done": self.subtasks_done, "subtasks_total": self.subtasks_total, "done": self.subtasks_done>=self.subtasks_total, "started": self.started}
	def check_delete(self):
		if time.time() - self.started > 3600:
			if not os.path.exists(config.log_dir + "/tasks"):
				os.makedirs(config.log_dir + "/tasks")
			logger = log.Logger(config.log_dir + "/tasks/%s"%self.id)
			logger.lograw(self.output.getvalue())
			logger.close()
			del TaskStatus.tasks[self.id]

class UploadTask():
	tasks={}
	def __init__(self):
		self.id = str(uuid.uuid1())
		UploadTask.tasks[self.id]=self
		self.filename = config.local_control_dir+"/tmp/"+self.id
		if not os.path.exists(config.local_control_dir+"/tmp/"):
			os.makedirs(config.local_control_dir+"/tmp/")
		self.fd = open(self.filename, "w")
		self.started = time.time()
	def chunk(self, data):
		self.fd.write(data)
	def finished(self):
		self.fd.close()
		del UploadTask.tasks[self.id]
	def check_delete(self):
		if time.time() - self.started > 3600:
			del UploadTask.tasks[self.id]
			if os.path.exists(self.filename):
				os.remove(self.filename)
		
class DownloadTask():
	tasks={}
	def __init__(self, filename):
		self.filename = filename
		self.id = str(uuid.uuid1())
		DownloadTask.tasks[self.id]=self
		self.fd = open(self.filename, "rb")
		self.started = time.time()
	def chunk(self):
		size=1024*1024
		data = self.fd.read(size)
		if len(data) == 0:
			self.fd.close()
			del DownloadTask.tasks[self.id]
			os.remove(self.filename)
		return data
	def check_delete(self):
		if time.time() - self.started > 3600:
			del DownloadTask.tasks[self.id]
			if os.path.exists(self.filename):
				os.remove(self.filename)
	
def cleanup():
	for task in TaskStatus.tasks.values():
		task.check_delete()
	for task in DownloadTask.tasks.values():
		task.check_delete()
	for task in UploadTask.tasks.values():
		task.check_delete()
	
cleanup_task = util.RepeatedTimer(3, cleanup)
cleanup_task.start()
atexit.register(cleanup_task.stop)