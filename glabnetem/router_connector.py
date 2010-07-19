# -*- coding: utf-8 -*-

from connector import *
from tinc_connector import *

class RouterConnector(Connector):
  
	def write_deploy_script(self, dir):
		print "# deploying router %s ..." % self.id
		TincConnector().write_deploy_script(self, dir)
