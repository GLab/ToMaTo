# -*- coding: utf-8 -*-

from util import parse_bool 

import ConfigParser, os

"""
This class represents the configuration
"""
config=ConfigParser.SafeConfigParser()
config.read(['glabnetman.conf', '/etc/glabnetman.conf', os.path.expanduser('~/.glabnetman.conf')])

def get(section,option,default):
	"""
	Retrieve a configuration value. If the configuration entry does not exist the default will be returned
	@param section the configuration section
	@param option the option in that section
	@default default value
	"""
	if config.has_option(section, option): 
		return config.get(section, option)
	else:
		return default
	

auth_ldap_server_uri = get("auth_ldap","server_uri","ldaps://glab-ldap.german-lab.de:636")
auth_ldap_server_cert = get("auth_ldap","server_cert",'/etc/ldap/certs/cacert.pem')
auth_ldap_binddn = get("auth_ldap","binddn",'cn=ukl.bim,ou=system,dc=german-lab,dc=de')
auth_ldap_bindpw = get("auth_ldap","bindpw",'somepw')
auth_ldap_identity_base = get("auth_ldap","identity_base",'ou=identities,dc=german-lab,dc=de')
auth_ldap_user_group = get("auth_ldap","user_group",'cn=users,ou=projectstructure,ou=groups,dc=german-lab,dc=de')
auth_ldap_admin_group = get("auth_ldap","admin_group",'cn=admin,ou=management,ou=groups,dc=german-lab,dc=de')

local_control_dir = get("local","control_dir","/tmp/glabnetem")
"""
The local directory to use for preparing control scripts before they are uploaded to the hosts.
"""

topology_dir = get("local","topology_dir","config/topologies")
"""
The local directory to use for storing the topology files in.
"""

log_dir = get("local","log_dir","logs")

hosts = get("local","hosts","config/hosts.xml")
"""
The local config file to use for storing the hosts in.
"""

openvz_default_template = get("openvz","default_template","debian-6.0-standard_6.0-2_i386")
"""
The default openvz template to use when no template is specified.
"""

kvm_default_template = get("kvm","default_template","debian_lenny_i386_small.qcow2")
"""
The default kvm template to use when no template is specified.
"""

remote_control_dir = get("remote","control_dir","/root/glabnetman")
"""
The remote directory to use for control scripts
"""

remote_dry_run = parse_bool(get("remote","dry_run",False))
"""
If this is true all remote commands are just printed but not executed
"""

password_salt = get("local", "password_salt", "glabnetman")