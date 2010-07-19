# -*- coding: utf-8 -*-

from connector import *
from tinc_connector import *

class RouterConnector(Connector):
  
	def deploy(self, dir):
		print "# deploying router %s ..." % self.id
		TincConnector().deploy(self, dir)
