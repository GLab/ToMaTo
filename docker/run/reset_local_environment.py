#!/usr/bin/python
__author__ = 't-gerhard'

import sys, os
import json
import subprocess
import shutil
import time

sys.path.insert(1, "../../cli/")
import lib as tomato

if not os.path.exists('tomato-ctl.py') or not os.path.exists('../../cli'):
	print "this script must be executed in ToMaTo/docker/run."
	exit(1)



# read config


config = {
	"templates": set(),
	"template_source": {},
	"site": {},
	"hosts": []
}

for path in filter(os.path.exists, ["test_setup.json", "/etc/tomato/test_setup.json", os.path.expanduser("~/.tomato/test_setup.json")]):
	try:
		with open(path, 'r') as f:
			new_config = json.loads(f.read())
		for templ_name in new_config.get("templates", []):
			config['templates'].add(templ_name)
		for host in new_config.get("hosts", []):
			config['hosts'].append(host)
		for k, v in new_config.get("site", {}).iteritems():
			config["site"][k] = v
		for k, v in new_config.get("template_source", {}).iteritems():
			config["template_source"][k] = v

		print >> sys.stderr, "Loaded config from %s" % path
	except Exception, exc:
		print >> sys.stderr, "Failed to load config from %s: %s" % (path, exc)
		exit(1)

print ""




# stop tomato
print "Stopping ToMaTo..."
subprocess.call(["./tomato-ctl.py", "stop"])
print ""

# remove mongodb data
print "Removing Database..."
mongodb_path = os.path.abspath("./mongodb-data")
if os.path.exists(mongodb_path):
	try:
		shutil.rmtree(os.path.abspath("./mongodb-data"))
	except:
		print " this requires superuser privileges."
		cmd = ["sudo", "rm", "-rf", mongodb_path]
		print " [%s]" % " ".join(cmd)
		subprocess.call(cmd)
print ""

# start tomato
print "Starting ToMaTo..."
subprocess.call(["./tomato-ctl.py", "start"])
time.sleep(5)  # give tomato some time to open ports
print ""



# insert site and hosts

print "Adding site and hosts..."
conn = tomato.getConnection(tomato.createUrl("http+xmlrpc", "localhost", 8000, "admin", "changeme"))

conn.site_create(config['site']['name'],
								 'others',
								 config['site']['label'],
								 {'location': config['site']['location'],
									'geolocation': config['site']['geolocation']}
								 )
for host in config['hosts']:
	try:
		conn.host_create(host['name'],
										 config['site']['name'],
										 {'address': host['address'],
											'rpcurl': host['rpcurl']})
	except:
		print "error inserting %s" % host['name']
print ""




# migrate templates

print "Adding templates..."
print " You need to log in to the template source."
migrate_template_params = [
		"./migrate_templates.py",
		"-sh", config['template_source']['host'],
		"-sp", config['template_source']['port'],
		"-dh", "localhost",
		"-dp", "8000",
		"-dU", "admin",
		"-dP", "changeme",
	]
if config['template_source']['restricted_templates']:
	migrate_template_params.append('--include_restricted')
migrate_template_params.append("-t")
for t in config['templates']:
	migrate_template_params.append(t)
p = subprocess.Popen(migrate_template_params,	cwd="../../cli")
p.wait()