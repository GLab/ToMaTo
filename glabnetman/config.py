# -*- coding: utf-8 -*-

from util import *

import ConfigParser, os

class Config(object):
	config=ConfigParser.SafeConfigParser()
	config.read(['glabnetem.conf', '/etc/glabnetem.conf', os.path.expanduser('~/.glabnetem.conf')])

	def get(section,option,default):
		if Config.config.has_option(section, option): 
			return Config.config.get(section, option)
		else:
			return default
	get = static(get)
	
Config.local_deploy_dir = Config.get("local","deploy_dir","/tmp/glabnetem")
Config.topology_dir = Config.get("local","topology_dir","config/topologies")
Config.topology_ids_shelve = Config.get("local","topology_ids_shelve","config/topology_ids.shelve")
Config.hosts = Config.get("local","hosts","config/hosts.xml")
Config.default_template = Config.get("openvz","default_template","debian-6.0-standard_6.0-2_i386")
Config.remote_deploy_dir = Config.get("remote","deploy_dir","/root/glabnetem")
Config.remote_dry_run = Config.get("remote","dry_run",False)

