# -*- coding: utf-8 -*-

from connector import *
from tinc_connector import *

class HubConnector(Connector):
  
	def write_deploy_script(self, dir):
		print "# deploying hub %s ..." % self.id
		TincConnector().write_deploy_script(self, dir)
