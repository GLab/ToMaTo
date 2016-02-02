#!/usr/bin/python
import sys
import subprocess
import os
import random
import string
import time
import json
import shutil
import socket, fcntl, struct
from datetime import date


TOMATO_MODULES = ['web', 'backend_core']
DB_MODULE = "db"
CONFIG_PATHS = ["/etc/tomato/tomato-ctl.conf", os.path.expanduser("~/.tomato/tomato-ctl.conf"), "tomato-ctl.conf", os.path.join(os.path.dirname(__file__), "tomato-ctl.conf")]


# basic functions

def get_interface_ip_address(ifname):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	return socket.inet_ntoa(fcntl.ioctl(
		s.fileno(),
		0x8915,  # SIOCGIFADDR
		struct.pack('256s', ifname[:15])
	)[20:24])

def get_hostname():
	return socket.gethostname()

def flat_list(list_of_lists):
	if len(list_of_lists) == 0:
		return []
	return reduce(lambda x, y: x+y, list_of_lists)

def append_to_str(string, between, all_strings):
	return string + between + "".join([" " for i in range(0, max(len(s) for s in all_strings)-len(string))])





# functions to call processes

def run_interactive(command, *args):
	subprocess.call([command] + list(args))

def run_observing(command, *args):
	subprocess.call([command] + list(args))

def assure_path(path):
	if not os.path.exists(path):
		os.makedirs(path)




# functions to control docker

def docker_start(container_name, args):
	run_observing("docker", "run", "-d", *args)
	run_observing("docker", "start", container_name)

def docker_exec(container, command, *args):
	run_interactive(
		"docker",
		"exec",
		"-it",
		container,
		command,
		*args
	)

def docker_stop(container):
	run_observing("docker", "stop", container)
	run_observing("docker", "rm", container)

def docker_container_started(container):
	p = subprocess.Popen(
		['docker', 'logs', container],
		stdout=subprocess.PIPE, stderr=subprocess.PIPE
	)
	p.communicate()
	if p.returncode:
		return False
	return True

def docker_logs(container, interactive):
	if interactive:
		try:
			run_observing('docker', 'logs', '-f', container)
		except KeyboardInterrupt:
			print ""
	else:
		run_observing('docker', 'logs', container)


def show_help():
	print """tomato-ctl:  control ToMaTo's docker containers.

Usage: %(cmd)s [COMMAND]
  or:  %(cmd)s [MODULE] [COMMAND]
  or:  %(cmd)s db [BACKUP|RESTORE] [BACKUP_NAME]
  or:  %(cmd)s help
  or:  %(cmd)s help-config

For information about how to configure %(cmd)s, please run '%(cmd)s help-config'

available modules:
 %(modules)s

available commands:

 start:
   Start the container
   This will also start all modules that depend on the selected module.
   If no module is selected, all modules will be started.

 stop:
   Stop the container
   This will also stop all modules that depend on the selected module.
   If no module is selected, all modules will be stopped.

 restart:
   Restart the container
   This is equivalent to stop and then start.
   When restarting %(DB_MODULE)s, this will restart all other running modules.

 shell:
   Open the shell of the container.
   For the database module, this is a mongodb shell.
   For backend and web modules, this is a bash shell (if not configured otherwise).
   This command is not available if no module is selected.

 status:
   Show the status (started|stopped|disabled) of the selected module container.
   If no module is selected, show the status of all containers.

 logs:
   Show the log of the selected container and quit.
   This command is not available if no module is selected.

 logs-live:
   Show the log of the selected container continuously.
   Quit using Ctrl+C.
   This command is not available if no module is selected.


Additional commands for the %(DB_MODULE)s module:

 backup:
   Create a backup of the database.
   You can pass an additional argument specifying the backup name.
   If you do not pass a backup name as argument, the current timestamp will be used.
   If the database is not running, it will be started and stopped afterwards.

 restore:
   Restore a backup.
   You have to pass the backup name as additional argument.
   If the database is not running, it will be started and stopped afterwards.

examples:
 %(cmd)s db stop
 %(cmd)s start
 %(cmd)s web status
""" % {
		'cmd': sys.argv[0],
		'DB_MODULE': DB_MODULE,
		'modules': "\n ".join([DB_MODULE]+TOMATO_MODULES)
	}


def show_help_configure(config):
	defconfig = generate_default_config()
	print """Config files may be stored at:
 %(config_paths)s
   Config files are interpreted in this order.
   If multiple config files specify the same variable, the latest config file wins.

Config files are stored in JSON format, the root is a dict.
The following settings can be set in the root dict:

 docker_dir (string, absolute path):
   All relative paths will be assumed to be relative to this directory.
   If not set, this will be assumed to be the directory in which this script is placed.

 tomato_dir (string, path):
   Directory of the ToMaTo code.
   This is used for determining the ToMaTo version, and for mounting code to the containers.
   If not set, this is assumed to be docker_dir/../..

 docker_network_interface:
   Network interface of the host for communicating with containers.
   default: 'docker0'

 docker_conainer_namespace:
   container names will start with this string, and a _.
   eg, if this is set to 'tomato', the 'backend_core' module will run in the container 'tomato_backend_core'.
   default: 'tomato'

The configuration of a modules is specified as a subdictionary, where its key is the module name.
 available modules: %(modules)s

The configuration of the database module (%(DB_MODULE)s) differs from the other modules.

Configuration parameters for all modules:

 enabled:
   Modules will only be started if this is set to True.
   The %(DB_MODULE)s module will always be started regardless of this setting.

 image:
   The Docker image to use for this container.
   default for %(DB_MODULE)s: 'mongo-latest'
   default for other modules: 'tomato_[MODULE_NAME]'

 timezone:
   Sets the 'TIMEZONE' environment variable.
   default: '%(default_timezone)s'

 ports:
   Either a list of entries, or a single entry.
   If an entry is an integer, it is treated as a tuple (entry, entry).
   This forwards ports on the host to specific ports on the container.
   The first entry is the port on the host, the second one on the container.

 additional_args:
   List of additional arguments when creating the container via 'docker run -d'
   When specified by multiple config files, all arguments are used.

 additional_directories:
   List of tuples of directories.
   For each entry, the container's directory is linked to the host's directory.
   The container's directory is the second element, and the host's directory is the first element.

 shell_cmd:
   Command to use when running the shell.
   default for %(DB_MODULE)s: '%(default_db_shell_cmd)s'
   default for other modules: /bin/bash

 directories:
   Dict of special directories. They will also be mounted to the right location on the container.
   The exact list of expected directories varies per module:
    %(default_directories)s
   The configuration is a dict, where the keys are the names of the directories, and the values are their paths.

 code_directories:
   not used for %(DB_MODULE)s.
   A list of directories in tomato_dir that will be mounted to /code/dir_name on the container.
   The first directory will be mounted as /code/service, The other directories will be mounted with their own name in /code.

""" % {
		'config_paths': CONFIG_PATHS,
		'modules': ", ".join([DB_MODULE] + TOMATO_MODULES),
		'DB_MODULE': DB_MODULE,
		'default_timezone': defconfig[DB_MODULE]['timezone'],
		'default_db_shell_cmd': defconfig[DB_MODULE]['shell_cmd'],
		'default_directories': "\n    ".join(append_to_str(module, ": ", TOMATO_MODULES+[DB_MODULE]) + (", ".join(defconfig[module]['directories'].keys())) for module in sorted([DB_MODULE]+TOMATO_MODULES))
	}

def generate_default_config():
	return {
		'web': {
			'enabled': True,
			'image': 'tomato_web',
			'ports': [(8080, 80)],
			'timezone': 'Europe/Berlin',
			'additional_args': [],
			'additional_directories': [
				('%(config)s', '/config')
			],
			'directories': {
				'config': os.path.join("backend_core", "config")
			},
			'code_directories': ['web', 'shared'],
			'shell_cmd': "/bin/bash"
			# 'version'  (will be generated if not found in config)
		},
		'backend_core': {
			'enabled': True,
			'image': 'tomato_backend_core',
			'ports': [8000, 8001, 8002, 8006] + range(8010, 8021),
			'timezone': 'Europe/Berlin',
			'additional_args': [],
			'additional_directories': [
				('%(config)s', '/config'),
				('%(data)s', '/data'),
				('%(logs)s', '/logs')
			],
			'directories': {
				'data': os.path.join("backend_core", "data"),
				'config': os.path.join("backend_core", "config"),
				'logs': os.path.join("backend_core", "logs")
			},
			'code_directories': ['backend_core', 'shared'],
			'shell_cmd': "/bin/bash"
			# 'version'  (will be generated if not found in config)
		},
		'db': {
			# enabled: True,
			# is_database: True
			'image': 'mongo:latest',
			'ports': [27017],
			'timezone': 'Europe/Berlin',
			'additional_args': [],
			'additional_directories': [
				('%(data)s', '/data/db')
			],
			'directories': {
				'data': "mongodb-data",
				'backup': "mongodb-backup"
			},
			'shell_cmd': ['/usr/bin/mongo', "localhost:27017/tomato"]
		},
		'docker_network_interface': 'docker0',
		'docker_container_namespace': 'tomato'
		# 'docker_dir'  (will be generated if not found in config)
		# 'tomato_dir'  (will be generated if not found in config)
	}

def read_config():

	# step 0: default config

	# although some things here are called 'additional', they may be essential.
	config = generate_default_config()

	# step 1: read config files

	def merge_dicts(dict_a, dict_b):
		for k, v in dict_b.iteritems():
			if k in dict_a:
				if isinstance(v, list) and k not in  ("port", "shell_cmd", "code_directories"):
					assert isinstance(dict_a[k], list)
					dict_a[k] = dict_a[k] + v
				elif isinstance(v, dict):
					assert isinstance(dict_a[k], dict)
					dict_a[k] = merge_dicts(dict_a[k], v)
				else:
					dict_a[k] = v
			else:
				dict_a[k] = v
		return dict_a

	for path in filter(os.path.exists, CONFIG_PATHS):
		try:
			with open(path) as f:
				conf_new = json.loads(f.read())
				config = merge_dicts(config, conf_new)
			print " [tomato-ctl] loaded config from %s" % path
		except:
			print " [tomato-ctl] failed to load config from %s" % path
			raise


	# step 2: calculate missing paths.
	if 'tomato_dir' not in config:
		config['tomato_dir'] = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
	if 'docker_dir' not in config:
		config['docker_dir'] = os.path.join(config['tomato_dir'], "docker", "run")
	print ""

	for module in "db", "backend_core", "web":

		if "version" not in config[module]:
			config[module]['version'] = subprocess.check_output(["bash", "-c", "cd '%s'; git describe --tags | cut -f1,2 -d'-'" % config['tomato_dir']]).split()[0]

		additional_dirs_new = []
		for additional_dir in config[module]['additional_directories']:
			directory = additional_dir[0] % config[module]['directories']
			if not os.path.isabs(directory):
				directory = os.path.join(config['docker_dir'], directory)
			additional_dirs_new.append((directory, additional_dir[1]))
		config[module]['additional_directories'] = additional_dirs_new

	# step 3: fill in missing data
	config[DB_MODULE]['enabled'] = True
	config[DB_MODULE]['is_database'] = True

	return config





class Module:
	def __init__(self, module_name, config):
		self.module_name = module_name
		module_config = config[module_name]
		self.enabled = module_config['enabled']

		tomato_dir = config['tomato_dir']
		additional_directories = module_config['additional_directories']
		host_ip = get_interface_ip_address(config['docker_network_interface'])
		host_name = get_hostname()
		self.container_name = "%s_%s" % (config['docker_container_namespace'], module_name)
		db_container = "%s_db" % config['docker_container_namespace']
		timezone = module_config['timezone']
		tomato_version = module_config['version']
		additional_args = module_config['additional_args']
		self.image = module_config['image']

		code_directories = []
		if 'code_directories' in module_config:
			is_first = True
			for directory in module_config['code_directories']:
				if is_first:
					is_first = False
					code_directories.append(("service", directory))
				else:
					code_directories.append((directory, directory))

		config_ports = module_config['ports']
		if not isinstance(config_ports, list):
			config_ports = [config_ports]
		ports = []
		for p in config_ports:
			if isinstance(p, tuple) or isinstance(p, list):
				ports.append((str(p[0]), str(p[1])))
			else:
				ports.append((str(p), str(p)))

		self.start_args = flat_list([
			flat_list([["-v", "%s/%s:/code/%s" % (tomato_dir, host_dir, container_dir)] for container_dir, host_dir in code_directories]),
			flat_list([["-v", "%s:%s" % c] for c in additional_directories]),
			["--add-host=%s:%s" % (host_name, host_ip)],
			["--link", "%s:db" % db_container],
			flat_list([["-p", "%s:%s" % p] for p in ports]),
			["-e", "TIMEZONE=%s" % timezone],
			["-e", "TOMATO_VERSION=%s" % tomato_version],
			["--name", self.container_name],
			additional_args,
			[self.image]
		])

		self.shell_cmd = module_config['shell_cmd']
		if not isinstance(self.shell_cmd, list):
			self.shell_cmd = [self.shell_cmd]

		self.is_db = module_config.get('is_database', False)

	def start(self, ignore_disabled=False):
		if ignore_disabled or self.enabled:
			docker_start(self.container_name, self.start_args)

	def stop(self):
		if self.is_started():
			docker_stop(self.container_name)

	def restart(self):
		if self.is_started():
			self.stop()
			self.start()

	def is_started(self):
		return docker_container_started(self.container_name)

	def logs(self, continuous):
		if self.is_started():
			docker_logs(self.container_name, continuous)
		else:
			print "container stopped."

	def shell(self):
		if self.is_started():
			docker_exec(self.container_name, *self.shell_cmd)
		else:
			print "container stopped."

	def create_backup(self, backup_name):
		if not self.is_started():
			"Cannot run backup while container is stopped."
			return

		if not self.is_db:
			print "not a database container."
			return

		backup_dir = config['db']['directories']['backup']
		if not os.path.isabs(backup_dir):
			backup_dir = os.path.join(config['docker_dir'],backup_dir)
		assure_path(backup_dir)
		cmd = flat_list([
			['docker', 'run', '-it'],
			['--link', '%s:mongo' % self.container_name],
			['-v', '%s:/backup' % backup_dir],
			['--rm'],
			[self.image],
			['sh', '-c', 'mongodump -h "$MONGO_PORT_27017_TCP_ADDR:$MONGO_PORT_27017_TCP_PORT" -d tomato --out /backup; chmod -R ogu+rwX /backup']
		])
		run_observing(*cmd)
		if not backup_name.endswith(".tar.gz"):
			backup_name += ".tar.gz"
		run_observing('tar', 'czf', backup_name, '-C', backup_dir, '.')
		shutil.rmtree(backup_dir)

	def restore_backup(self, backup_name):
		if not self.is_started():
			"Cannot run backup while container is stopped."
			return

		if not self.is_db:
			print "not a database container."
			return

		backup_dir = config['db']['directories']['backup']
		if not os.path.isabs(backup_dir):
			backup_dir = os.path.join(config['docker_dir'],backup_dir)
		assure_path(backup_dir)
		if not backup_name.endswith(".tar.gz"):
			backup_name += ".tar.gz"
		run_observing('tar', 'xzf', backup_name, '-C', backup_dir)
		cmd = [
			'docker',
			'run',
			'-it',
			'--link', '%s:mongo' % self.container_name,
			'-v', '%s:/backup' % backup_dir,
			'--rm',
			self.image,
			'sh', '-c', 'exec mongorestore -h "$MONGO_PORT_27017_TCP_ADDR:$MONGO_PORT_27017_TCP_PORT" "/backup" --drop'
		]
		run_observing(*cmd)
		shutil.rmtree(backup_dir)




config = read_config()
db_module = Module(DB_MODULE, config)
tomato_modules = {module_name: Module(module_name, config) for module_name in TOMATO_MODULES}

args = sys.argv

if len(args) == 2:
	if args[1] == "start":
		db_module.start()
		for module in tomato_modules.itervalues():
			module.start()
		exit(0)

	if args[1] == "stop":
		for module in tomato_modules.itervalues():
			module.stop()
		db_module.stop()
		exit(0)

	if args[1] == "restart":
		modules_started = [mod for mod in tomato_modules.itervalues() if mod.is_started()]
		for module in modules_started:
			module.stop()
		db_module.restart()
		for module in modules_started:
			module.start()
		exit(0)

	if args[1] == "status":
		stats = {}
		max_len = len(DB_MODULE)
		stats[DB_MODULE] = 'started' if db_module.is_started() else 'stopped'
		for module_name, module in tomato_modules.iteritems():
			max_len = max(max_len, len(module_name))
			stats[module_name] = 'started' if module.is_started() else ('stopped' if module.enabled else 'disabled')
		for module_name in sorted(stats.iterkeys()):
			mod_name_print = append_to_str(module_name, ": ", stats.iterkeys())
			print mod_name_print, stats[module_name]
		exit(0)

	if args[1] in ('help-config', '--help-config'):
		show_help_configure(config)
		exit(0)

if len(args) in [3,4]:
	module_name = args[1]
	is_db_module = None
	module = None
	if module_name in TOMATO_MODULES:
		module = tomato_modules[module_name]
		is_db_module = False
	elif module_name == DB_MODULE:
		module = db_module
		is_db_module = True
	else:
		print "available modules", ", ".join(TOMATO_MODULES+[DB_MODULE])
		exit(1)

	if args[2] == "start" and len(args) == 3:
		if not is_db_module:
			db_module.start()
		module.start()
		exit(0)

	if args[2] == "stop" and len(args) == 3:
		module.stop()
		exit(0)

	if args[2] == "restart" and len(args) == 3:
		if is_db_module:
			modules_started = [mod for mod in tomato_modules.itervalues() if mod.is_started()]
			for mod in modules_started:
				mod.stop()
			module.restart()
			for mod in modules_started:
				mod.start()
			exit(0)
		else:
			module.restart()
			exit(0)

	if args[2] == "status" and len(args) == 3:
		print "%s: %s" % (module_name, 'started' if module.is_started() else ('stopped' if module.enabled else 'disabled'))
		exit(0)

	if args[2] == "shell" and len(args) == 3:
		module.shell()
		exit(0)

	if args[2] == "logs" and len(args) == 3:
		module.logs(False)
		exit(0)

	if args[2] == "logs-live" and len(args) == 3:
		module.logs(True)
		exit(0)

	if args[2] in ("backup", "restore"):
		comm = args[2]
		if len(args) == 3:
			if comm == "restore":
				print "Error: please specify the backup name."
				print " ".join(args+["[BACKUP_NAME]"])
				exit(1)
			backup_name = "mongodb-dump-%s" % date.today().isoformat()
			print "Warning: no backup name specified. Using %s." % backup_name
		else:
			backup_name = args[3]

		is_started = db_status(config)
		if not is_started:
			db_start(config)

		if comm == 'backup':
			db_backup(config, backup_name)
		else:
			db_restore(config, backup_name)

		if not is_started:
			db_stop(config)

		exit(0)

show_help()