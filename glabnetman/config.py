# -*- coding: utf-8 -*-

from util import *

import ConfigParser, os

class Config(object):
	"""
	This class represents the copnfiguration
	"""
	config=ConfigParser.SafeConfigParser()
	config.read(['glabnetman.conf', '/etc/glabnetman.conf', os.path.expanduser('~/.glabnetman.conf')])

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
	

Config.auth_ldap_server_uri = Config.get("auth_ldap","server_uri","ldaps://glab-ldap.german-lab.de:636")
Config.auth_ldap_server_cert = Config.get("auth_ldap","server_cert",'/etc/ldap/certs/cacert.pem')
Config.auth_ldap_binddn = Config.get("auth_ldap","binddn",'cn=ukl.bim,ou=system,dc=german-lab,dc=de')
Config.auth_ldap_bindpw = Config.get("auth_ldap","bindpw",'somepw')
Config.auth_ldap_identity_base = Config.get("auth_ldap","identity_base",'ou=identities,dc=german-lab,dc=de')
Config.auth_ldap_user_group = Config.get("auth_ldap","user_group",'cn=users,ou=projectstructure,ou=groups,dc=german-lab,dc=de')
Config.auth_ldap_admin_group = Config.get("auth_ldap","admin_group",'cn=admin,ou=management,ou=groups,dc=german-lab,dc=de')

Config.local_control_dir = Config.get("local","control_dir","/tmp/glabnetem")
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

Config.remote_control_dir = Config.get("remote","control_dir","/root/glabnetman")
"""
The remote directory to use for control scripts
"""

Config.remote_dry_run = parse_bool(Config.get("remote","dry_run",False))
"""
If this is true all remote commands are just printed but not executed
"""
