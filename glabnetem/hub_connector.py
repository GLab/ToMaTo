# -*- coding: utf-8 -*-

from connector import *
from tinc_connector import *

class HubConnector(Connector):
  
	def deploy(self, dir):
		print "# deploying hub %s ..." % self.id
		TincConnector().deploy(self, dir)
