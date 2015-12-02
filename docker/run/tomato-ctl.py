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


# basic functions

def get_interface_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])









# functions to call processes

def run_interactive(command, *args):
	subprocess.call([command] + list(args))

def run_observing(command, *args):
	subprocess.call([command] + list(args))

def assure_path(path):
	if not os.path.exists(path):
		os.makedirs(path)




# functions to control docker

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
		['docker', 'inspect', '-f', '{{.State.Running}}', container],
		stdout=subprocess.PIPE, stderr=open("/dev/null")
	)
	output, err = p.communicate()
	if err:
		return False
	return "true" in output

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

available modules:
 db:      database
 backend: ToMaTo backend
 web:     ToMaTo webfrontend

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
   This will also restart all modules that depend on the selected module.

 shell:
   Open the shell of the container.
   For the db module, this is a mongodb shell.
   For backend and web modules, this is a bash shell.
   This command is not available if no module is selected.

 status:
   Show the status (started|stopped) of the selected module's container.
   If no module is selected, show the status of all containers.

 logs:
   Show the log of the selected container and quit.
   This command is not available if no module is selected.

 logs-live:
   Show the log of the selected container continuously.
   Quit using Ctrl+C.
   This command is not available if no module is selected.


Additional commands for the db module:

 backup:
   Create a backup of the database.
   You can pass an additional argument specifying the backup name.
   If you do not pass a backup name as argument, the current timestamp will be used.
   If the database is not running, it will be started and stopped afterwards.

 restore:
   Restore a backup.
   You have to pass the backup name as additional argument.
   If the database is not running, it will be started and stopped afterwards.


Additional commands for the web module:

 reload:
   Reloads the apache configuration and ToMaTo code.


examples:
 %(cmd)s db stop
 %(cmd)s start
 %(cmd)s web status
""" % {'cmd': sys.argv[0]}
	exit(0)


def web_start(config):
	if web_status(config):
		return
	for directory, _ in config['backend']['additional_directories']:
		assure_path(directory)
	secret_key = "".join(random.choice(string.digits+string.ascii_letters) for _ in range(32))
	cmd = [
		"docker",
		"run",
		"-d",
		"-v", "%s/web:/code" % config['tomato_dir'],
		"-v", "%s/shared:/shared" % config['tomato_dir']
	] + \
	reduce(lambda x, y: x+y, (['-v', '%s:%s' % c] for c in config['web']['additional_directories'])) + \
	[
		"--add-host=%s:%s" % (socket.gethostname(), get_interface_ip_address(config['docker_network_interface'])),
		"--link", "%s:backend" % config['backend']['docker_container'],
		"-p", "%s:80" % str(config['web']['port']),
		"--name", config['web']['docker_container'],
		"-e", "SECRET_KEY=%s" % secret_key,
		"-e", "TIMEZONE=%s" % config['web']['timezone'],
		"-e", "TOMATO_VERSION=%s" % config['web']['version']
	] + \
	config['web']['additional_args'] + \
	[
		config['web']['image']
	]

	run_observing(*cmd)
	run_observing("docker", "start", config['web']['docker_container'])


def web_stop(config):
	if not web_status(config):
		return
	docker_stop(config['web']['docker_container'])


def web_status(config):
	return docker_container_started(config['web']['docker_container'])


def web_shell(config):
	if not web_status(config):
		print "web not running"
		exit(1)
	docker_exec(config['web']['docker_container'], 'bin/bash')

def web_log(config, interactive):
	if not web_status(config):
		print "web not running"
		exit(1)
	docker_logs(config['web']['docker_container'], interactive)

def web_reload(config):
	if not web_status(config):
		print "web not running"
		exit(1)
	docker_exec(config['web']['docker_container'], "service", "apache2", "reload")


def backend_start(config):
	if backend_status(config):
		return
	for directory, _ in config['backend']['additional_directories']:
		assure_path(directory)
	cmd = [
		"docker",
		"run",
		"-d",
		"-v", "%s/backend:/code" % config['tomato_dir'],
		"-v", "%s/shared:/shared" % config['tomato_dir']
	] + \
	reduce(lambda x, y: x+y, (['-v', '%s:%s' % c] for c in config['backend']['additional_directories'])) + \
	[
		"--add-host=%s:%s" % (socket.gethostname(), get_interface_ip_address(config['docker_network_interface'])),
		"--link", "%s:db" % config['db']['docker_container']
	] + \
	reduce(lambda x, y: x+y, [['-p', "%s:%s" % (str(p),str(p))] for p in config['backend']['ports']]) + \
	[
		"-e", "TIMEZONE=Europe/Berlin",
		"-e", "TOMATO_VERSION=%s" % config['backend']['version'],
		"--name", config['backend']['docker_container']
	] + \
	config['backend']['additional_args'] + \
	[
		config['backend']['image']
	]
	run_observing(*cmd)
	run_observing("docker", "start", config['backend']['docker_container'])


def backend_stop(config):
	if not backend_status(config):
		return
	docker_stop(config['backend']['docker_container'])


def backend_status(config):
	return docker_container_started(config['backend']['docker_container'])


def backend_shell(config):
	if not backend_status(config):
		print "backend not running"
		exit(1)
	docker_exec(config['backend']['docker_container'], 'bin/bash')

def backend_log(config, interactive):
	if not backend_status(config):
		print "backend not running"
		exit(1)
	docker_logs(config['backend']['docker_container'], interactive)


def db_start(config):
	if db_status(config):
		return
	for directory, _ in config['db']['additional_directories']:
		assure_path(directory)

	cmd = [
		"docker",
		"run",
		"-d"
	] + \
	reduce(lambda x, y: x+y, (['-v', '%s:%s' % c] for c in config['db']['additional_directories'])) + \
	[
		"-p", "127.0.0.1:%s:%s" % (config['db']['port'],config['db']['port']),
		"-e", "TOMATO_VERSION=%s" % config['backend']['version'],
		"--name", config['db']['docker_container']
	] + \
	config['db']['additional_args'] + \
	[
		config['db']['image'],
		"--storageEngine", "wiredTiger"
	]
	run_observing(*cmd)
	run_observing("docker", "start", config['db']['docker_container'])


def db_stop(config):
	if not db_status(config):
		return
	docker_stop(config['db']['docker_container'])


def db_status(config):
	return docker_container_started(config['db']['docker_container'])


def db_shell(config):
	if not db_status(config):
		print "db not running"
		exit(1)
	docker_exec(config['db']['docker_container'], '/usr/bin/mongo', "localhost:27017/tomato")

def db_log(config, interactive):
	if not db_status(config):
		print "db not running"
		exit(1)
	docker_logs(config['db']['docker_container'], interactive)

def db_backup(config, backup_name):
	backup_dir = config['db']['directories']['backup']
	if not os.path.isabs(backup_dir):
		backup_dir = os.path.join(config['docker_dir'],backup_dir)
	assure_path(backup_dir)
	cmd = [
		'docker',
		'run',
		'-it',
		'--link', '%s:mongo' % config['db']['docker_container'],
		'-v', '%s:/backup' % backup_dir,
		'--rm',
		config['db']['image'],
		'sh', '-c', 'mongodump -h "$MONGO_PORT_27017_TCP_ADDR:$MONGO_PORT_27017_TCP_PORT" -d tomato --out /backup; chmod -R ogu+rwX /backup'
	]
	run_observing(*cmd)
	if not backup_name.endswith(".tar.gz"):
		backup_name += ".tar.gz"
	run_observing('tar', 'czf', backup_name, '-C', backup_dir, '.')
	shutil.rmtree(backup_dir)

def db_restore(config, backup_name):
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
		'--link', '%s:mongo' % config['db']['docker_container'],
		'-v', '%s:/backup' % backup_dir,
		'--rm',
		config['db']['image'],
		'sh', '-c', 'exec mongorestore -h "$MONGO_PORT_27017_TCP_ADDR:$MONGO_PORT_27017_TCP_PORT" "/backup" --drop'
	]
	run_observing(*cmd)
	shutil.rmtree(backup_dir)








def read_config():

	# step 0: default config

	# although some things here are called 'additional', they may be essential.
	config = {
		'db': {
			'docker_container': 'mongodb',
			'image': 'mongo:latest',
			'port': 27017,
			'additional_args': [],
			'additional_directories': [
				('%(data)s', '/data/db')
			],
			'directories': {
				'data': "mongodb-data",
				'backup': "mongodb-backup"
			}
			# 'version'     (will be generated if not found in config)
		},
		'backend': {
			'docker_container': 'tomato-backend',
			'image': 'tomato-backend',
			'ports': [8000, 8001, 8002, 8006] + range(8010,8021),
			'timezone': 'Europe/Berlin',
			'additional_args': [],
			'additional_directories': [
				('%(config)s', '/config'),
				('%(data)s', '/data'),
				('%(logs)s', '/logs')
			],
			'directories': {
				'data': os.path.join("backend", "data"),
				'config': os.path.join("backend", "config"),
				'logs': os.path.join("backend", "logs")
			}
			# 'version'  (will be generated if not found in config)
		},
		'web': {
			'docker_container': 'tomato-web',
			'image': 'tomato-web',
			'port': 8080,
			'timezone': 'Europe/Berlin',
			'additional_args': [],
			'additional_directories': [
				('%(config)s', '/config')
			],
			'directories': {
				'config': os.path.join("web", "config")
			}
			# 'version'  (will be generated if not found in config)
		},
		'docker_network_interface': 'docker0'
		# 'docker_dir'  (will be generated if not found in config)
		# 'tomato_dir'  (will be generated if not found in config)
	}

	# step 1: read config files

	def merge_dicts(dict_a, dict_b):
		for k, v in dict_b.iteritems():
			if k in dict_a:
				if isinstance(v, list):
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

	for path in filter(os.path.exists, ["/etc/tomato/tomato-ctl.conf", os.path.expanduser("~/.tomato/tomato-ctl.conf"), "tomato-ctl.conf", os.path.join(os.path.dirname(__file__), "tomato-ctl.conf")]):
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

	for module in "db", "backend", "web":

		if "version" not in config[module]:
			config[module]['version'] = subprocess.check_output(["bash", "-c", "cd '%s'; git describe --tags | cut -f1,2 -d'-'" % config['tomato_dir']]).split()[0]

		additional_dirs_new = []
		for additional_dir in config[module]['additional_directories']:
			directory = additional_dir[0] % config[module]['directories']
			if not os.path.isabs(directory):
				directory = os.path.join(config['docker_dir'], directory)
			additional_dirs_new.append((directory, additional_dir[1]))
		config[module]['additional_directories'] = additional_dirs_new

	return config



config = read_config()

if len(sys.argv) == 2:

	if sys.argv[1] == "start":
		db_start(config)
		backend_start(config)
		web_start(config)
		exit(0)

	if sys.argv[1] == "stop":
		web_stop(config)
		backend_stop(config)
		db_stop(config)
		exit(0)

	if sys.argv[1] == "restart":
		web_stop(config)
		backend_stop(config)
		db_stop(config)
		db_start(config)
		backend_start(config)
		web_start(config)
		exit(0)

	if sys.argv[1] in ["help","--help","-h"]:
		show_help()
		exit(0)

	if sys.argv[1] =="status":
		print "db:      %s" % ("started" if db_status(config) else "stopped")
		print "backend: %s" % ("started" if backend_status(config) else "stopped")
		print "web:     %s" % ("started" if web_status(config) else "stopped")
		exit(0)

elif len(sys.argv) == 3:

	if sys.argv[1] == "db":

		if sys.argv[2] == "start":
			db_start(config)
			exit(0)

		if sys.argv[2] == "stop":
			web_stop(config)
			backend_stop(config)
			db_stop(config)
			exit(0)

		if sys.argv[2] == "restart":
			web_started = web_status(config)
			backend_started = backend_status(config)
			web_stop(config)
			backend_stop(config)
			db_stop(config)
			db_start(config)
			if backend_started:
				backend_start(config)
			if web_started:
				web_start(config)
			exit(0)

		if sys.argv[2] == "status":
			print "db: %s" % ("started" if db_status(config) else "stopped")
			exit(0)

		if sys.argv[2] == "shell":
			db_shell(config)
			exit(0)

		if sys.argv[2] == "logs":
			db_log(config, False)
			exit(0)

		if sys.argv[2] == "logs-live":
			db_log(config, True)
			exit(0)

		if sys.argv[2] == "backup":
			backup_name = "mongodb-dump-%s" % date.today().isoformat()
			print "Warning: no backup name specified. Using %s." % backup_name
			sys.argv.append(backup_name)
			# now, len(sys.argv == 4)

		if sys.argv[2] == "restore":
			print "Error: you have to specify a backup name."

	if sys.argv[1] == "backend":

		if sys.argv[2] == "start":
			db_start(config)
			backend_start(config)
			exit(0)

		if sys.argv[2] == "stop":
			web_stop(config)
			backend_stop(config)
			exit(0)

		if sys.argv[2] == "restart":
			web_started = web_status(config)
			web_stop(config)
			backend_stop(config)
			db_start(config)
			backend_start(config)
			if web_started:
				web_start(config)
			exit(0)

		if sys.argv[2] == "status":
			print "backend: %s" % ("started" if backend_status(config) else "stopped")
			exit(0)

		if sys.argv[2] == "shell":
			backend_shell(config)
			exit(0)

		if sys.argv[2] == "logs":
			backend_log(config, False)
			exit(0)

		if sys.argv[2] == "logs-interactive":
			backend_log(config, True)
			exit(0)


	if sys.argv[1] == "web":

		if sys.argv[2] == "start":
			db_start(config)
			backend_start(config)
			web_start(config)
			exit(0)

		if sys.argv[2] == "stop":
			web_stop(config)
			exit(0)

		if sys.argv[2] == "restart":
			web_stop(config)
			db_start(config)
			backend_start(config)
			web_start(config)
			exit(0)

		if sys.argv[2] == "status":
			print "web: %s" % ("started" if web_status(config) else "stopped")
			exit(0)

		if sys.argv[2] == "shell":
			web_shell(config)
			exit(0)

		if sys.argv[2] == "logs":
			web_log(config, False)
			exit(0)

		if sys.argv[2] == "logs-interactive":
			web_log(config, True)
			exit(0)

		if sys.argv[2] == "reload":
			web_reload(config)
			exit(0)

if len(sys.argv) == 4:
	if sys.argv[1] == 'db':
		if sys.argv[2] in ('backup', 'restore'):
			backup_name = sys.argv[3]

			is_started = db_status(config)
			if not is_started:
				db_start(config)

			if sys.argv[2] == 'backup':
				db_backup(config, backup_name)
			else:
				db_restore(config, backup_name)

			if not is_started:
				db_stop(config)

			exit(0)


show_help()
exit(1)
