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

"""
The hostmanager accepts a number of configuration options that are not stored
inside the database for convenience. The configuration will be evaluated at
startup of the hostmanager.

The following configuration values can be set in configuration files in the 
following locations:

  * ``/etc/tomato/hostmanager.conf``
  * ``~/.tomato/hostmanager.conf``
  * ``./hostmanager.conf``
  
These files will be evaluated in the given order, if some of the files do not 
exist, the parser will skip it. These files are evaluated using the python
interpreter, so they have to contain proper python code and can also execute
some code to obtain and set the configuration values. Also the configuration
values can be set without module path since the configuration files are 
evaluated in the right context.
"""

import os

DUMMY_FLOPPY = "/usr/share/tomato-hostmanager/contrib/dummy_floppy.raw"

LOG_FILE = "/var/log/tomato/main.json.log"
"""
The location of the logfile. All relevant logging information will be written 
to this file.
Note that as this file can become large over time, it is highly recommended to
use a tool like *logrotate* to compress it regularly. The ToMaTo packages 
already include configuration entries for logrotate that have to be adapted
if this setting is changed.  
"""

DUMP_DIR = "/var/log/tomato/dumps_hostmanager"
"""
The location of the dump files that are created when unexpected errors occur.
"""

DUMP_LIFETIME = 60*60*24*7
"""
Time in seconds until a dump file may be deleted.
If it has been collected by the dumpmanager until then, it will still be saved
in the dumpmanager's database.
dumps will only be deleted daily, and only one day after the program has started.
"""

DATA_DIR = "/var/lib/tomato"
"""
The main data storage location for ToMaTo. All of the data, including templates
and disk images, will be stored in subfolders of this directory. It is very 
important that this directory has enough free space to store the data 
(100 GiB or more). For Proxmox VE installations this directory is automatically
moved (and symlinked) to the big data partition of Proxmox.
"""

TEMPLATE_DIR = None
"""
The main directory for templates (i.e. ready-to use stock disk images). If this
field is set to ``None`` (the default), the template directory will be a 
subdirectory of the data directory.
"""

SERVER = [{
	"TYPE": "https+xmlrpc",
	"PORT": 8000,
	"SSL_OPTS": {
		"cert_file" : "/etc/tomato/server.pem",
		"key_file": "/etc/tomato/server.pem",
		"client_certs": "/etc/tomato/client_certs",
	}
}, {
  "TYPE": "ssl+jsonrpc",
	"PORT": 8003,
	"SSL_OPTS": {
		"cert_file" : "/etc/tomato/server.pem",
		"key_file": "/etc/tomato/server.pem",
		"client_certs": "/etc/tomato/client_certs.pem",
	}
}]
"""
This field defines where and how to start the API server. It is a list of 
server entries where each server entry is a dict containing the following
values:

   ``TYPE`` (default: ``https+xmlrpc``)
      The type/protocol of the server. Available protocols are ``https+xmlrpc``
      and ``ssl+jsonrpc``.

   ``PORT`` (default: ``8000``)
      The port number of the API server. This defaults to 8000. If several
      server entries are configured, each one needs its own free port number.
   
   ``SSL_OPTS``
      This dict contains the following options for the SSL usage:
      
      ``key_file``, ``cert_file`` (default: ``'/etc/tomato/server.pem'``)
         The paths of the files containing the private key and the SSL 
         certificate for the server in PEM format.
         If one file contains both information, these fields can point to the
         same file.
         The package will automatically create a self-signed certificate in the
         default location.
      
      ``client_certs`` (default: ``'/etc/tomato/client_certs'``)
         The path to the directory where all accepted client (i.e. backend) 
         certificates are stored. See :doc:`backends` for information about
         backend authentication. 
     
     
Note: for backwards compatibility, the list can be omitted and instead a 
single dict containing one server entry can be assigned to this field.
"""

DATABASES = None
DATABASE = {
   'ENGINE': 'django.db.backends.postgresql_psycopg2',
   'NAME': 'tomato'
}
"""
The database to use for ToMaTo. The contents are the same as for
`Django <http://docs.djangoproject.com/en/dev/ref/databases>`_.
The only actively supported database at this time is PostgresQL but other
real databases should work as well. SQLite is known not to work due to its
limited concurrency capabilities. See :doc:`/docs/databases` for information
about selecting and maintaining databases.
Please note that only one database is supported. 
"""

FILESERVER = {
	'PORT': 8888,
	'PATH': None,
}
"""
This field defines where to start the :doc:`fileserver`. It is a dict 
containing the following fields:

   ``PORT`` (default: ``8888``)
      The port number of the fileserver. This must be set to a free TCP port.
   
   ``PATH`` (default: ``None``)
      The path of the directory containing all files stored for download and 
      after upload. If this field is set to ``None`` (the default), the 
      fileserver directory will be a subdirectory of the data directory.
"""

MAX_TIMEOUT = 30*24*60*60 # 30 days
"""
This field defines the maximum element timeout value which also is the default
timeout.
"""

BITTORRENT_RESTART = 60 * 30 # 30 minutes
"""
This field defines how often the bittorrent client should be restarted.
"""

BITTORRENT_PORT_RANGE = (8010, 8020)

RESOURCES = {
	'port': xrange(6000, 7000),
	'vmid': xrange(1000, 2000)
}
"""
This dictionary defines the resources that the hostmanager can use. The default
will work for most systems. If the hostmanager shares the host with other 
systems that also need those resources, these entries might need to be adapted.
"""

WEBSOCKIFY_PORT_BLACKLIST = [6000, 6666]

MAX_REQUESTS = 50

import socket
_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_socket.connect(("8.8.8.8",80))
PUBLIC_ADDRESS = _socket.getsockname()[0]
_socket.close()

TIME_ZONE = 'Europe/Berlin'

LANGUAGE_CODE = 'de-de'

INSTALLED_APPS = ('tomato', 'south')
SECRET_KEY = 'not needed'

DISABLE_TRANSACTION_MANAGEMENT = True

MAINTENANCE = os.environ.has_key('TOMATO_MAINTENANCE')

try:
	import sys
	for path in filter(os.path.exists, ["/etc/tomato/hostmanager.conf", os.path.expanduser("~/.tomato/hostmanager.conf"), "hostmanager.conf"]):
		try:
			execfile(path)
			print >>sys.stderr, "Loaded config from %s" % path
		except Exception, exc:
			print >>sys.stderr, "Failed to load config from %s: %s" % (path, exc)
except:
	import traceback
	traceback.print_exc()

if not isinstance(SERVER, list):
	SERVER = [SERVER]
if not TEMPLATE_DIR:
	TEMPLATE_DIR = os.path.join(DATA_DIR, "templates")
if not FILESERVER["PATH"]:
	FILESERVER["PATH"] = os.path.join(DATA_DIR, "files")
if not DATABASES:
	DATABASES = {'default': DATABASE.copy()}