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

import atexit, time

class Logger():
	
	def __init__ (self, filename):
		self.filename = filename
		self.fd = open(filename, "a")
		atexit.register(self.close)
		
	def log (self, message, user="unknown", timestamp=None, bigmessage=None):
		if not timestamp:
			timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
		if bigmessage:
			self.fd.write("-"*50 + " BEGIN " + "-"*50 + "\n")
		self.fd.write(("%s\t%s\t%s\n" % (timestamp, user, message)).encode("utf-8"))
		if bigmessage:
			self.fd.write(bigmessage)
			self.fd.write("-"*51 + " END " + "-"*51 + "\n")

	def lograw (self, message):
		self.fd.write(message)
		
	def __exit__(self, *args):
		self.close()
		
	def __enter__(self, *args):
		return self
		
	def close(self):
		try:
			self.fd.close()
			del loggers[self.filename]
		except: #pylint: disable-msg=W0702
			pass
		
loggers={}		
		
def getLogger(filename):
	if loggers.has_key(filename):
		return loggers[filename]
	else:
		logger = Logger(filename)
		loggers[filename] = logger
		return logger