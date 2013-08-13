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

LOG_FILE = "/var/log/tomato/main.json.log"
"""
The location of the logfile. All relevant logging information will be written 
to this file.
Note that as this file can become large over time, it is highly recommended to
use a tool like *logrotate* to compress it regularly. The ToMaTo packages 
already include configuration entries for logrotate that have to be adapted
if this setting is changed.  
"""

DUMP_DIR = "/var/log/tomato/dumps"
"""
The location of the dump files thar are created when unexpected errors occur.
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

SERVER = {
	"PORT": 8000,
	"SSL": True,
	"SSL_OPTS": {
		"cert_file" : "/etc/tomato/server.cert",
		"key_file": "/etc/tomato/server.cert",
		"client_certs": "/etc/tomato/client_certs",
	}
}
"""
This field defines where and how to start the API server. It is a list of 
server entries where each server entry is a dict containing the following
values:

   ``PORT`` (default: ``8000``)
      The port number of the API server. This defaults to 8000. If several
      server entries are configured, each one needs its own free port number.
   
   ``SSL`` (default: ``True``)
      Whether SSL should be used or not. Since the authentication uses SSL
      client certificates, this setting must be ``True``.
   
   ``SSL_OPTS``
      This dict contains the following options for the SSL usage:
      
      ``key_file``, ``cert_file`` (default: ``'/etc/tomato/server.cert'``)
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

ADMIN_USERS = []
"""
A list of administrative users names. If a users certificate has a 
*common name* that is listed in this cofiguration field, it is granted
special permissions.
See :doc:`backends` for more information about backend authentication. 
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
Please note that only one data base is supported. 
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
This field defines the maximum timeout value which also is the default timeout.
"""

BITTORRENT_RESTART = 60 * 30 # 30 minutes
"""
This field defines how often the bittorrent client should be restarted.
"""


import socket
_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_socket.connect(("8.8.8.8",80))
PUBLIC_ADDRESS = _socket.getsockname()[0]
_socket.close()

TIME_ZONE = 'Europe/Berlin'

LANGUAGE_CODE = 'de-de'

INSTALLED_APPS = ('tomato', 'south')

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