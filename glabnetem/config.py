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
	topology_dir = get("local","topology_dir","config/topologies")
	topology_ids_shelve = get("local","topology_ids_shelve","config/topology_ids.shelve")
	hosts_shelve = get("local","hosts_shelve","config/hosts.shelve")
	default_template = get("openvz","default_template","debian-6.0-standard_6.0-2_i386")
	remote_deploy_dir = get("remote","deploy_dir","/root/glabnetem")
	remote_dry_run = get("remote","dry_run",False)

