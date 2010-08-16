# -*- coding: utf-8 -*-

import uuid, os

import config

from cStringIO import StringIO

class TaskStatus():
	tasks={}
	def __init__(self):
		self.id = str(uuid.uuid1())
		TaskStatus.tasks[self.id]=self
		self.output = StringIO()
		self.subtasks_total = 0
		self.subtasks_done = 0
	def done(self):
		self.subtasks_done = self.subtasks_total
	def dict(self):
		return {"id": self.id, "output": self.output.getvalue(), "subtasks_done": self.subtasks_done, "subtasks_total": self.subtasks_total, "done": self.subtasks_done==self.subtasks_total}

class UploadTask():
	tasks={}
	def __init__(self):
		self.id = str(uuid.uuid1())
		UploadTask.tasks[self.id]=self
		self.filename = config.local_control_dir+"/tmp/"+self.id
		if not os.path.exists(config.local_control_dir+"/tmp/"):
			os.makedirs(config.local_control_dir+"/tmp/")
		self.fd = open(self.filename, "w")
	def chunk(self, data):
		self.fd.write(data)
	def finished(self):
		self.fd.close()
		del UploadTask.tasks[self.id]
		
class DownloadTask():
	tasks={}
	def __init__(self, filename):
		self.filename = filename
		self.id = str(uuid.uuid1())
		DownloadTask.tasks[self.id]=self
		self.fd = open(self.filename, "rb")
	def chunk(self):
		size=1024*1024
		data = self.fd.read(size)
		if len(data) == 0:
			self.fd.close()
			del DownloadTask.tasks[self.id]
			os.remove(self.filename)
		return data