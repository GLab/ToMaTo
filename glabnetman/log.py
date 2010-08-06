# -*- coding: utf-8 -*-

import atexit, time

class Logger():
	
	def __init__ (self, filename):
		self.filename = filename
		self.fd = open(filename, "a")
		atexit.register(self.fd.close)
		
	def log (self, message, user="unknown", timestamp=None, bigmessage=None):
		if not timestamp:
			timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
		if bigmessage:
			self.fd.write("-"*50 + " BEGIN " + "-"*50 + "\n")
		self.fd.write("%s\t%s\t%s\n" % (timestamp, user, message))
		if bigmessage:
			self.fd.write(bigmessage)
			self.fd.write("-"*51 + " END " + "-"*51 + "\n")

	def lograw (self, message):
		self.fd.write(message)