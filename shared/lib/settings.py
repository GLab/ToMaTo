__author__ = 't-gerhard'

import yaml, os
from error import InternalError

default_settings = yaml.load("""
# ignored from backend config:
#
#  AUTH = []
#  AUTH.append({
#  "name": "",
#  "provider": "internal",
#  "options": {
#      "password_timeout": None,
#      "account_timeout": 60*60*24*365*5, # 5 years
#      "allow_registration": True,
#      "default_flags": ["over_quota", "new_account"]
#  }
#})
#
#
#
#
#
#  ERROR_NOTIFY = []
#  MAX_REQUESTS = 50
#  MAX_WORKERS = 25
#
#
#
#
#
# import socket
# _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# _socket.connect(("8.8.8.8",80))
# PUBLIC_ADDRESS = _socket.getsockname()[0]
# _socket.close()
#
# socket.setdefaulttimeout(1800)
#
#
#
# (importing of config files)
#
#
#
# HOST_AVAILABILITY_FACTOR = math.pow(0.5, HOST_UPDATE_INTERVAL/HOST_AVAILABILITY_HALFTIME)
#
#
#
#
#
#
# backend_users config completely ignored.
#
#
#
#
#
# ignored in web/tomato/settings.py
#
#  everything until line 99
#  server_{protocol, host, port} will be taken from services section
#  server_httprealm
#
#  line 112-119
#
#  ( reading of config files)
#

services:
  backend_api:  # currently, this points to backend_core
    host: twentythree
    interfaces:
      - port: 8000
        ssl: false
        protocol: ??
      - port: 8001
        ssl: true
        protocol: ??
  backend_core:
    host: twentythree
    port: 8000
    protocol: ??
  backend_users:
    host: twentythree
    port: 8002
    protocol: sslrpc2
  web:
    host: twentythree
    port: 8080
    protocol: http

external-urls:
  aup:        http://tomato-lab.org/aup
  help:       http://github.com/GLab/ToMaTo/wiki
  impressum:  http://tomato-lab.org/contact/
  project:    http://tomato-lab.org
  json-feed:  http://www.tomato-lab.org/feed.json
  rss-feed:   http://tomato-lab.org/feed.xml
  bugtracker: http://github.com/GLab/ToMaTo/issues

github:
  # access tokens can be created via GitHub settings -> My Personal Access Tokens
  # The token needs the scope 'repo' or 'public_repo' (depending on whether the repository is private or not)
  access-token:

  repository-owner: GLab
  repository-name:  ToMaTo

backend_core:
  paths:
    templates:  /var/lib/tomato/templates
    log:    /var/log/tomato/main.log
  dumps:
    enabled:  true
    directory:  /var/log/tomato/dumps  # location where error dumps are stored
    lifetime:  604800  # 7 days. Dumps older than this will be deleted. This does not affect dumps that have been collected by the dump manager.
  ssl:
    cert:  /etc/tomato/backend_core.pem
    ca:  /etc/tomato/ca.pem
  bittorrent:
    tracker-port: 8002
    bittorrent-restart: 1800  # 30 minutes
  database:
    db-name: tomato
    server:
      host: localhost
      port: 27017
  host-connections:
    update-interval: 60
    availability-halftime: 7776000  # 90 days
    resource-sync-interval: 600
    component-timeout: 31104000  # 12 months

backend_users:
  paths:
    log:  /var/log/tomato/main.log
  dumps:
    enabled:  true
    directory:  /var/log/tomato/dumps  # location where error dumps are stored
    lifetime:  604800  # 7 days. Dumps older than this will be deleted. This does not affect dumps that have been collected by the dump manager.
  ssl:
    cert:  /etc/tomato/backend_users.pem
    ca:  /etc/tomato/ca.pem
  database:
    db-name: tomato
    server:
      host: localhost
      port: 27017

web:
  paths:
    log:  /var/log/tomato/main.log
  ssl:
    cert:  /etc/tomato/backend_users.pem
    ca:  /etc/tomato/ca.pem
  duration-log:

    # this logs the duration of all API calls.
    # however, this slows down the webfrontend in case of many HTTP requests.
    enabled:  false

    # for each API call, the duration log file is opened and closed.
    # thus, to increase performance, this should be on tmpfs or similar.
    # it doesn't need to be stored in a persistent file system.
    location:  /tmp/webfrontend_api_duration_log.json

    # the call duration is calculated as an average of the last n calls. (or all calls, if there weren't that many)
    # a higher size means a better averaging, but while debugging, this means that changes take longer until they are effective.
    size:    25

  web-resources:
    tutorial-list:        http://packages.tomato-lab.org/tutorials/index.json
    default-executable-archive-list:

  # specify how often user information is updated (seconds between updates).
  # a longer interval improves performance for webfrontend and backend,
  # but it means that it takes some time for user account changes to be applied.
  # updates are only done when the user opens a page which uses the API.
  account-info-update-interval: 120

rpc-timeout: 60

email:
  smtp-server: localhost
  from: ToMaTo backend <tomato@localhost>
  messages:
    notification:
      subject: "[ToMaTo] %(subject)s"
      body: |
        Dear %(realname)s

        "%(message)s"

        Sincerely,
        Your ToMaTo backend
    new-user-welcome:
      subject: Registration at ToMaTo-Lab
      body: |
        Dear %s,

        Welcome to the ToMaTo-Lab testbed. Your registration will be reviewed by our administrators shortly. Until then, you can create a topology (but not start it).
        You should also subscribe to our mailing list at https://lists.uni-kl.de/tomato-lab.

        Best Wishes,
        The ToMaTo Testbed
    new-user-admin-inform:
      subject: User Registration
      body: |
        Dear ToMaTo administrator,

        A new user, %s, has just registered at the ToMaTo testbed.
        You can review all pending user registrations at https://master.tomato-lab.org/account/registrations

        Best Wishes,
        The ToMaTo Testbed

topologies:
  timeout-initial: 3600
  timeout-default: 259200  # 3 days
  timeout-max: 2592000  # 30 days
  timeout-warning: 86400  # 1 day
  timeout-remove: 7776000  # 90 days
  timeout-options: [86400, 259200, 1209600, 2592000]  # 1, 3, 14, 30 days

user-quota:
  default:
    cputime: 12960000  # 5 cores * 90 days
    memory: 1000000000  # 10GB * 90 days
    diskspace: 100000000000  # 100GB * 90 days
    traffic: 1620000000000  # 5Mbit/s all the time
    continous-factor: 1

dumpmanager:
  collection-interval: 1800  # 30 minutes. Interval in which the dumpmanager will collect error dumps from sources.

""")

settings = None

def init(filename, tomato_module):
	global settings
	settings = SettingsProvider(filename, tomato_module)

class Config:
	TOMATO_MODULE_WEB = "web"
	TOMATO_MODULE_BACKEND_CORE = "backend_core"
	TOMATO_MODULE_BACKEND_USERS = "backend_users"
	TOMATO_MODULE_BACKEND_API = "backend_api"

	EMAIL_NOTIFICATION = "notification"
	EMAIL_NEW_USER_WELCOME = "new-user-welcome"
	EMAIL_NEW_USER_ADMIN = "new-user-admin-inform"

	USER_QUOTA_DEFAULT = "default"

	WEB_RESOURCE_TUTORIAL_LIST = "tutorial-list"
	WEB_RESOURCE_DEFAULT_EXECUTABLE_ARCHIVE_LIST = "default-executable-archive-list"



class SettingsProvider:
	def __init__(self, filename, tomato_module):
		"""
		Load settings from settings file

		:param str filename: path to settings file
		:param str tomato_module: tomato module (e.g., "web" or "backend_core")
		:return: None
		"""
		self.tomato_module = tomato_module
		InternalError.check(os.path.exists(filename), code=InternalError.CONFIGURATION_ERROR, message="configuration missing", todump=False, data={'filename': filename})
		with open(filename, "r") as f:
			print "reading settings file '%s'." % filename
			self.original_settings = yaml.load(f.read())
			print "done reading settings file."
		self._check_settings()

	def get_tomato_module_name(self):
		"""
		get tomato module of this
		:return: tomato module name
		:rtype: str
		"""
		return self.tomato_module

	def get_web_resource_location(self, resource_type):
		"""
		get the url to the specified web resource (Config.WEB_RESOURCE_*)
		:return: url to the resource list
		:rtype: str
		"""
		InternalError.check('web-resources' in self.original_settings[self.tomato_module], code=InternalError.CONFIGURATION_ERROR, message="web resource configuration missing")
		InternalError.check(resource_type in self.original_settings[self.tomato_module]['web-resources'], code=InternalError.INVALID_PARAMETER, message="No such web resource type", data={"resource_type": resource_type})
		return self.original_settings[self.tomato_module]['web-resources'][resource_type]

	def get_duration_log_settings(self):
		"""
		get duration log settings
		:return: dict containing 'enabled', 'location', 'size'
		:rtype: dict
		"""
		InternalError.check('duration-log' in self.original_settings[self.tomato_module], code=InternalError.CONFIGURATION_ERROR, message="duration log configuration missing")
		return {k: v for k, v in self.original_settings[self.tomato_module]['duration-log'].iteritems()}

	def get_host_connections_settings(self):
		"""
		get host connections settings
		:return: dict containing 'update-interval', 'availability-halftime', 'resource-sync-interval', 'component-timeout'
		:rtype: dict
		"""
		InternalError.check('host-connections' in self.original_settings[self.tomato_module], code=InternalError.CONFIGURATION_ERROR, message="host connection configuration missing")
		return {k: v for k, v in self.original_settings[self.tomato_module]['host-connections'].iteritems()}

	def get_db_settings(self):
		"""
		get database settings
		:return: dict containing 'database' (name), 'host' and 'port'
		:rtype: dict
		"""
		return {
			'database': self.original_settings[self.tomato_module]['database']['db-name'],
			'host': self.original_settings[self.tomato_module]['database']['server']['host'],
			'port': self.original_settings[self.tomato_module]['database']['server']['port']
		}

	def get_bittorrent_settings(self):
		"""
		bittorrent settings
		:return: dict containing 'tracker-port' and 'bittorrent-restart'
		:rtype: dict
		"""
		InternalError.check('bittorrent' in self.original_settings[self.tomato_module], code=InternalError.CONFIGURATION_ERROR, message="bittorrent configuration missing")
		return {k: v for k, v in self.original_settings[self.tomato_module]['bittorrent'].iteritems()}

	def get_ssl_ca_filename(self):
		"""
		get the ssl ca cert filename
		:return: path to ssl ca cert
		:rtype: str
		"""
		return self.original_settings[self.tomato_module]['ssl']['ca']

	def get_ssl_cert_filename(self):
		"""
		get the ssl cert filename
		:return: path to ssl cert
		:rtype: str
		"""
		return self.original_settings[self.tomato_module]['ssl']['cert']

	def get_template_dir(self):
		"""
		get the directory where templates will be stored
		:return: directory path
		:rtype: str
		"""
		InternalError.check('templates' in self.original_settings[self.tomato_module]['paths'], code=InternalError.CONFIGURATION_ERROR, message="template directory missing")
		return self.original_settings[self.tomato_module]['paths']['templates']

	def get_log_filename(self):
		"""
		get the filename to write the log to
		:return: filename
		:rtype: str
		"""
		return self.original_settings[self.tomato_module]['paths']['log']

	def get_github_settings(self):
		"""
		get the github config
		:return: the github config, a dict containing 'access-token', 'repository-owner', 'repository-name'
		:rtype: dict(str)
		"""
		InternalError.check('github' in self.original_settings, code=InternalError.CONFIGURATION_ERROR, message="github not configured")
		return {k: v for k, v in self.original_settings['github'].iteritems()}

	def get_rpc_timeout(self):
		"""
		get the rpc timeout
		:return: rpc timeout
		:rtype: int|float
		"""
		return self.original_settings['rpc-timeout']

	def get_user_quota(self, config_name):
		"""
		get quota parameters for the configuration configured in settings under this name
		:param str config_name: name of the configuration in settings (/user-quota/[config_name])
		:return: dict containing 'cputime', 'memory', 'diskspace', 'traffic', 'continous-factor'
		:rtype: dict
		"""
		InternalError.check(config_name in self.original_settings['user-quota'], code=InternalError.INVALID_PARAMETER, message="No such quota config", data={"config_name": config_name})
		return {k: v for k, v in self.original_settings['user-quota'][config_name].iteritems()}

	def get_topology_settings(self):
		"""
		get the topology config
		:return: dict as in settings file
		:rtype: dict
		"""
		return {k: v for k, v in self.original_settings['topologies'].iteritems()}

	def get_dumpmanager_config(self):
		"""
		get the dumpmanager config
		:return: dict containing the parameter 'collection-interval'
		:rtype: dict
		"""
		return {
			'collection-interval': self.original_settings['dumpmanager']['collection-interval']
		}

	def get_email_settings(self, message_type):
		"""
		get email parameters for a certain message type.
		:param str message_type: message type from Config.EMAIL_*
		:return: configuration including 'smtp-server', 'from', 'subject', 'body'
		:trype: dict(str)
		"""
		settings = self.original_settings['email']
		InternalError.check(message_type in settings['messages'], code=InternalError.INVALID_PARAMETER, message="No such message template", data={"message_type": message_type})

		return {
			'smtp-server': settings['smtp-server'],
			'from': settings['from'],
			'subject': settings['messages'][message_type]['subject'],
			'body': settings['messages'][message_type]['body']
		}

	def get_external_url(self, external_url):
		InternalError.check(external_url in self.original_settings['external-urls'], code=InternalError.INVALID_PARAMETER, message="External URL does not exist", data={"external-url": external_url})
		return self.original_settings['external-urls']

	def get_interfaces(self, target_module):
		"""
		:param str target_module: tomato module to retrieve this information for.
		:return: a list of interface configs. each config is a dict, containing host, port, protocol, and optionally ssl
		:rtype: list(dict)
		"""
		InternalError.check(target_module in self.original_settings['services'], code=InternalError.INVALID_PARAMETER, message="invalid module", data={"target_module": target_module})
		conf = self.original_settings['services'][target_module]
		if 'interfaces' in conf:
			res = []
			for interface in conf['interfaces']:
				res.append({
					'host': conf['host'],
					'port': interface['port'],
					'protocol': interface['protocol'],
					'ssl': interface['ssl']
				})
		else:
			return [{
				'host': conf['host'],
				'port': conf['port'],
				'protocol': conf['protocol']
			}]

	def get_own_interface_config(self):
		"""
		return own interface config
		:return: a list of interface configs. each config is a dict, containing host, port, protocol, and optionally ssl
		:rtype: list(dict)
		"""
		if self.tomato_module == "backend_core":
			return self.get_interfaces('backend_api')
		else:
			return self.get_interfaces(self.tomato_module)


	def _check_settings(self):
		"""
		Check settings for completeness.
		When an error is found, either fill it in, or raise an exception.
		:return: None
		"""

		error_found = False  # set to true if tomato cannot be started
		bad_paths = []

		# services

		if 'services' not in self.original_settings:
			print "Configuration ERROR at /services: section is missing."
			print " this is fatal."
			error_found = True
			bad_paths.append('/services')
		else:
			for service in default_settings['services']:
				service_settings = self.original_settings['services'].get(service, None)
				if service_settings is None:
					print "Configuration ERROR at /services/%s: is missing." % service
					print " this is fatal."
					error_found = True
					bad_paths.append('/services/%s' % service)
				else:
					if not self.original_settings['services'][service].get('host', None):
						print "Configuration ERROR at /services/%s/host: %s hostname not found" % (service, service)
						print " this is fatal."
						error_found = True
						bad_paths.append('/services/%s/host')
					if 'interfaces' in service_settings:
						interface_config_error_found = False
						for interface in service_settings['interfaces']:
							for s in ("port", "ssl", "protocol"):
								if interface.get(s, None) is None:
									print "Configuration ERROR at /services/%s/interfaces: %s not specified" % (service, s)
									interface_config_error_found = True
						if interface_config_error_found:
							print " Using default interface config for %s" % service
							if 'interface' in default_settings['services'][service]:
								service_settings['interface'] = default_settings['services'][service]['interface']
							else:
								del service_settings['interface']
								service_settings['port'] = default_settings['services'][service]['port']
								service_settings['protocol'] = default_settings['services'][service]['protocol']
					else:
						for s in ('port', 'protocol'):
							if not service_settings.get(s, None):
								print "Configuration ERROR at /services/%s/%s: %s not specified" % (service, s, s)
								if s in default_settings['services'][service]:
									print " using default %s." % s
									service_settings[s] = default_settings['services'][service][s]
								else:
									print " this is fatal."
									error_found = True
									bad_paths.append('/services/%s/%s' % (service, s))


		# external urls
		if 'external-urls' not in self.original_settings:
			print "Configuration WARNING at /external-urls: section is missing."
			print " using defeault external urls."
			self.original_settings['external-urls'] = default_settings['external-urls']
		else:
			for k, v in default_settings['external-urls'].iteritems():
				if k not in self.original_settings['external-urls']:
					print "Configuration ERROR at /external-urls: %s missing" % k
					print " using default URL"
					self.original_settings['external-urls'][k] = v
				else:
					if not self.original_settings['external-urls'][k]:
						print "Configuration WARNING at /extrnal-urls/%s: is empty" % k


		# github
		if self.is_web():
			if not self.original_settings['github'].get('access-token', None):
				print "Configuration WARNING at /github/access-token: GitHub access token is not set."
				print "  access tokens can be created on the GitHub page in settings -> My Personal Access Tokens"
				print "  The token needs the scope 'repo' or 'public_repo'"
				self.original_settings['github']['access-token'] = ""
			else:
				for s in ("repository-owner", "repository-name"):
					if not self.original_settings['github'].get(s, None):
						print "Configuration WARNING at /github/%s: %s not configured" % (s,s)
						print " disabling GitHub."
						del self.original_settings['github']


		# rpc-timeout
		if not self.original_settings.get('rpc-timeout', None):
			print "Configuration WARNING at /rpc-timeout: not set"
			print " using default RPC timeout."
			self.original_settings['rpc-timeout'] = default_settings['rpc-timeout']

		# e-mail
		if not self.original_settings.get('email', None):
			print "Configuration ERROR at /email: is missing."
			print " this is fatal."
			error_found = True
			bad_paths.append('/email')
		else:
			if not self.original_settings['email'].get('smtp-server', None):
				print "Configuration ERROR at /email/smtp-server: is missing."
				print " this is fatal."
				error_found = True
				bad_paths.append('/email/smtp-server')
			if not self.original_settings['email'].get('from', None):
				print "Configuration ERROR at /email/smtp-server/from: is missing."
				print " using default E-Mail sender"
				self.original_settings['email']['from'] = default_settings['email']['from']
			if not self.original_settings['email'].get('messages', None):
				print "Configuration ERROR at /email/messages: is missing."
				print " using default messages"
				self.original_settings['email']['messages'] = default_settings['email']['messages']
			for m, message in default_settings['email']['messages'].iteritems():
				if not self.original_settings['email']['messages'].get(m, None):
					print "Configuration ERROR at /email/messages/%s: is missing." % m
					print " using default message"
					self.original_settings['email']['messages'][m] = message
				else:
					for k in ('subject', 'body'):
						if not self.original_settings['email']['messages'][m].get(k, None):
							print "Configuration ERROR at /email/messages/%s/%s: is missing." % (m,k)
							print " using default %s" % k
							self.original_settings['email']['messages'][m][k] = message[k]


		# topologies
		if not self.original_settings.get('topologies', None):
			print "Configuration ERROR at /topologies: is missing."
			print " using default topology settings."
			self.original_settings['topologies'] = default_settings['topologies']
		else:
			for k, v in default_settings['topologies'].iteritems():
				if not self.original_settings['topologies'].get(k, None):
					print "Configuration ERROR at /topologies/%s: not set." % k
					print " using default."
					self.original_settings['topologies'][k] = v

		# user-quota
		if not self.original_settings.get('user-quota', None):
			print "Configuration ERROR at /user-quota: is missing."
			print " using default user quota settings."
			self.original_settings['user-quota'] = default_settings['user-quota']
		else:
			for q, quota in default_settings['user-quota'].iteritems():
				if not self.original_settings['user-quota'].get(q, None):
					print "Configuration ERROR at /user-quota/%s: is missing." % q
					print " using default settings for %s" % q
					self.original_settings['user-quota'][q] = quota
				else:
					for k, v in quota.iteritems():
						if not self.original_settings['user-quota'][q].get(k, None):
							print "Configuration ERROR at /user-quota/%s/%s: is missing." % (q, k)
							print " using default %s for %s" % (k, q)
							self.original_settings['user-quota'][q][k] = v

		# dumpmanager
		if not self.original_settings.get('dumpmanager', None):
			print "Configuration ERROR at /dumpmanager: is missing."
			print " using default dumpmanager settings."
			self.original_settings['dumpmanager'] = default_settings['dumpmanager']
		else:
			for k, v in default_settings['dumpmanager'].iteritems():
				if not self.original_settings['dumpmanager'].get(k, None):
					print "Configuration ERROR at /dumpmanager/%s: is missing." % k
					print " using default setting for %s" % k
					self.original_settings['dumpmanager'][k] = v


		# this module's settings
		this_module_setting = self.original_settings.get(self.tomato_module, None)
		this_mosule_defaults = default_settings[self.tomato_module]
		if this_module_setting is None:
			print "Configuration ERROR at /%s: is missing." % self.tomato_module
			print " this is fatal."
			error_found = True
			bad_paths.append('/%s' % self.tomato_module)
		for sec, default_sec_val in this_mosule_defaults.iteritems():
			if not this_module_setting.get(sec, None):
				print "Configuration ERROR at /%s/%s: is missing." % (self.tomato_module, sec)
				if sec in ('paths', 'ssl', 'database'):
					print " this is fatal."
					error_found = True
					bad_paths.append('/%s/%s' % (self.tomato_module, sec))
				else:
					print " using default %s" % sec
					this_module_setting[sec] = default_sec_val
			else:
				if isinstance(default_sec_val, dict):
					for k, v in default_sec_val.iteritems():
						if not this_module_setting[sec].get(k, None):
							print "Configuration ERROR at /%s/%s/%s: is missing." % (self.tomato_module, sec, k)
							if (sec == "database" and k == "server") or (sec in ('paths', 'ssl')) or (sec == 'duration-log' and k == 'location'):
								print " this is fatal."
								error_found = True
								bad_paths.append('/%s/%s/%s' % (self.tomato_module, sec, k))
							else:
								print " using default."
								this_module_setting[sec][k] = v
						else:
							if sec == "database" and k == 'server':
								if not this_module_setting[sec][k].get('host', None):
									print "Configuration ERROR at %s/%s/%s/host" % (self.tomato_module, sec, k)
									print " this is fatal."
									error_found = True
									bad_paths.append('%s/%s/%s/host' % (self.tomato_module, sec, k))
								if not this_module_setting[sec][k].get('port', None):
									print "Configuration ERROR at %s/%s/%s/port" % (self.tomato_module, sec, k)
									print " using default port."
									this_module_setting[sec][k]['port'] = v['port']

		InternalError.check(not error_found, code=InternalError.CONFIGURATION_ERROR, message="fatal configuration error", todump=False)







	def is_web(self):
		return self.tomato_module == "web"

	def is_backend_core(self):
		return self.tomato_module == "backend_core"

	def is_backend_users(self):
		return self.tomato_module == "backend_users"