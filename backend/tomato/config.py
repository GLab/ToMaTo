# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from util import parse_bool 

import ConfigParser, os

# This class represents the configuration

config = ConfigParser.SafeConfigParser()
config.read(['tomato.conf', '/etc/tomato/tomato.conf', '/etc/tomato.conf', os.path.expanduser('~/.tomato.conf')])

def get(section, option, default):
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
    

auth_ldap_server_uri = get("auth_ldap", "server_uri", "ldaps://glab-ldap.german-lab.de:636")
auth_ldap_server_cert = get("auth_ldap", "server_cert", '/etc/ldap/certs/cacert.pem')
auth_ldap_binddn = get("auth_ldap", "binddn", 'cn=ukl.bim,ou=system,dc=german-lab,dc=de')
auth_ldap_bindpw = get("auth_ldap", "bindpw", 'somepw')
auth_ldap_identity_base = get("auth_ldap", "identity_base", 'ou=identities,dc=german-lab,dc=de')
auth_ldap_user_group = get("auth_ldap", "user_group", 'cn=users,ou=projectstructure,ou=groups,dc=german-lab,dc=de')
auth_ldap_admin_group = get("auth_ldap", "admin_group", 'cn=admin,ou=management,ou=groups,dc=german-lab,dc=de')

auth_htpasswd_admin_user = get("auth_htpasswd", "admin_user", 'admin')
auth_htpasswd_file = get("auth_htpasswd", "file", '')

local_control_dir = get("local", "control_dir", "/tmp/tomato")
# The local directory to use for preparing control scripts before they are uploaded to the hosts.

log_dir = get("local", "log_dir", "logs")

remote_control_dir = get("remote", "control_dir", "/root/tomato")
# The remote directory to use for control scripts

remote_dry_run = parse_bool(get("remote", "dry_run", True))
# If this is true all remote commands are just printed but not executed

remote_ssh_key = get("remote", "ssh_key", os.path.expanduser('~/.ssh/id_rsa'))

password_salt = get("local", "password_salt", "tomato")

auth_provider = get("auth", "provider", "htpasswd")

timeout_stop_weeks = int(get("timeout", "stop", 4))
timeout_destroy_weeks = int(get("timeout", "destroy", 12))
timeout_remove_weeks = int(get("timeout", "remove", 24))

server_port = int(get("server", "port", 8000))
server_ssl = parse_bool(get("server", "ssl", False))
server_ssl_private_key = get("server", "ssl_private_key", "")
server_ssl_ca_key = get("server", "ssl_ca_key", "")

DATABASE_ENGINE = get("local", "database_engine", 'sqlite3')
DATABASE_NAME = get("local", "database_name", 'db.sqlite')
DATABASE_HOST = get("local", "database_host", '')
DATABASE_PORT = get("local", "database_port", '')
DATABASE_USER = get("local", "database_user", '')
DATABASE_PASSWORD = get("local", "database_password", '')

TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'de-de'

INSTALLED_APPS = ('tomato', 'south')

TESTING = os.environ.has_key('TOMATO_TESTING')

if TESTING:
    print "Running in testing mode"
    DATABASE_ENGINE = "sqlite3"
    DATABASE_NAME = "testing.db.sqlite"
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
    remote_dry_run = True
    auth_provider = "dummy"
    
MAINTENANCE = os.environ.has_key('TOMATO_MAINTENANCE')
