# -*- coding: utf-8 -*-

from connector import *
from tinc_connector import *

class SwitchConnector(Connector):
  
	def deploy(self, dir):
		print "# deploying switch %s ..." % self.id
		TincConnector().deploy(self, dir)
