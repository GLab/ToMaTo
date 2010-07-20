# -*- coding: utf-8 -*-

from util import *

import ConfigParser, os

class ConfigHelper(object):
	config=ConfigParser.SafeConfigParser()
	config.read(['glabnetem.conf', '/etc/glabnetem.conf', os.path.expanduser('~/.glabnetem.conf')])
	
class Config(object):
	def get(section,option,default):
		if ConfigHelper.config.has_option(section, option): 
			return ConfigHelper.config.get(section, option)
		else:
			return default
	get = static(get)
	
	local_deploy_dir = get("local","deploy_dir","/tmp/glabnetem")
	topology_dir = get("local","topology_dir","topologies")
	default_template = get("openvz","default_template","debian")
	remote_deploy_dir = get("remote","deploy_dir","/root/glabnetem")
