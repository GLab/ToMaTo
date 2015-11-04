#!/usr/bin/python
import sys
import subprocess
import os
import random
import string
import time
import json

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

Usage: %(cmd)s [MODULE] [COMMAND]
  or:  %(cmd)s [COMMAND]
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
		"--link", "%s:db" % config['db']['docker_container']
	] + \
	reduce(lambda x, y: x+y, [['-p', str(p)] for p in config['backend']['ports']]) + \
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







# although some things here are called 'additional', they may be essential.
config = {
	'db': {
		'docker_container': 'mongodb',
		'image': 'mongo:latest',
		'port': 27017,
		'additional_args': [],
		'additional_directories': [
			(os.path.join(os.getcwd(), "mongodb-data"), '/data')
		]
		# 'version'  (will be generated if not found in config)
	},
	'backend': {
		'docker_container': 'tomato-backend',
		'image': 'tomato-backend',
		'ports': [8000, 8001, 8002, 8006] + range(8010,8021),
		'timezone': 'Europe/Berlin',
		'additional_args': [],
		'additional_directories': [
			(os.path.join(os.getcwd(), "backend", "config"), '/config'),
			(os.path.join(os.getcwd(), "backend", "data"), '/data'),
			(os.path.join(os.getcwd(), "backend", "logs"), '/logs')
		]
		# 'version'  (will be generated if not found in config)
	},
	'web': {
		'docker_container': 'tomato-web',
		'image': 'tomato-web',
		'port': 8080,
		'timezone': 'Europe/Berlin',
		'additional_args': [],
		'additional_directories': [
			(os.path.join(os.getcwd(), "web", "config"), '/config')
		]
		# 'version'  (will be generated if not found in config)
	},
	'docker_dir': os.getcwd()
	# 'tomato_dir'  (will be generated if not found in config)
}

def merge_dirs(dir_a, dir_b):
	for k, v in dir_b.iteritems():
		if k in dir_a:
			if isinstance(v, list):
				assert isinstance(dir_a[k], list)
				dir_a[k] = dir_a[k] + v
			elif isinstance(v, dict):
				assert isinstance(dir_a[k], dict)
				dir_a[k] = merge_dirs(dir_a[k], v)
			else:
				dir_a[k] = v
		else:
			dir_a[k] = v
		return dir_a

for path in filter(os.path.exists, ["/etc/tomato/tomato-ctl.conf", os.path.expanduser("~/.tomato/tomato-ctl.conf"), "tomato-ctl.conf"]):
	try:
		with open(path) as f:
			conf_new = json.loads(f.read())
			config = merge_dirs(config, conf_new)
		print "loaded config from %s" % path
	except:
		print "failed to load config from %s" % path
		raise

if 'tomato_dir' not in config:
	config['tomato_dir'] = os.path.join(config['docker_dir'], "..", "..")
print ""
for module in "db", "backend", "web":
	if "version" not in config[module]:
		config[module]['version'] = subprocess.check_output(["bash", "-c", "cd '%s'; git describe --tags | cut -f1,2 -d'-'" % config['tomato_dir']]).split()[0]

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
			web_stop(config)
			backend_stop(config)
			db_stop(config)
			db_start(config)
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
			web_stop(config)
			backend_stop(config)
			db_start(config)
			backend_start(config)
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


show_help()
exit(1)
