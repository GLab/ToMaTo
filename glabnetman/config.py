# -*- coding: utf-8 -*-

from util import *

import ConfigParser, os

class Config(object):
	"""
	This class represents the copnfiguration
	"""
	config=ConfigParser.SafeConfigParser()
	config.read(['glabnetem.conf', '/etc/glabnetem.conf', os.path.expanduser('~/.glabnetem.conf')])

	"""
	Retrieve a configuration value. If the configuration entry does not exist the default will be returned
	@param section the configuration section
	@param option the option in that section
	@default default value
	"""
	def get(section,option,default):
		if Config.config.has_option(section, option): 
			return Config.config.get(section, option)
		else:
			return default
	get = static(get)
	

Config.local_deploy_dir = Config.get("local","deploy_dir","/tmp/glabnetem")
"""
The local directory to use for preparing control scripts before they are uploaded to the hosts.
"""

Config.topology_dir = Config.get("local","topology_dir","config/topologies")
"""
The local directory to use for storing the topology files in.
"""

Config.hosts = Config.get("local","hosts","config/hosts.xml")
"""
The local config file to use for storing the hosts in.
"""

Config.default_template = Config.get("openvz","default_template","debian-6.0-standard_6.0-2_i386")
"""
The default openvz template to use when no template is specified.
"""

Config.remote_deploy_dir = Config.get("remote","deploy_dir","/root/glabnetem")
"""
The remote directory to use for control scripts
"""

Config.remote_dry_run = Config.get("remote","dry_run",False)
"""
If this is true all remote commands are just printed but not executed
"""
