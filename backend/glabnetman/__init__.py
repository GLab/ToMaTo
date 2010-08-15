# -*- coding: utf-8 -*-

import os
os.environ['DJANGO_SETTINGS_MODULE']="glabnetman.config"

import config, log, topology, hosts

logger = log.Logger(config.log_dir + "/api.log")

class Fault():
	UNKNOWN = -1
	NO_SUCH_TOPOLOGY = 100
	ACCESS_TO_TOPOLOGY_DENIED = 101
	NOT_A_REGULAR_USER = 102
	INVALID_TOPOLOGY_STATE_TRANSITION = 103
	IMPOSSIBLE_TOPOLOGY_CHANGE = 104
	TOPOLOGY_HAS_PROBLEMS = 105
	MALFORMED_XML = 106
	MALFORMED_TOPOLOGY_DESCRIPTION = 107
	NO_SUCH_DEVICE = 108
	UPLOAD_NOT_SUPPORTED = 109
	DOWNLOAD_NOT_SUPPORTED = 110
	INVALID_TOPOLOGY_STATE = 111
	NO_SUCH_HOST = 200
	NO_SUCH_HOST_GROUP = 201
	ACCESS_TO_HOST_DENIED = 202
	HOST_EXISTS = 203

def _topology_info(top):
	state = str(top.state)
	return {"id": top.id, "state": str(top.state), "name": top.name,
		"is_created": state == topology.State.CREATED,
		"is_uploaded": state == topology.State.UPLOADED, 
		"is_prepared": state == topology.State.PREPARED,
		"is_started": state == topology.State.STARTED,
		"owner": str(top.owner), "analysis": top.analysis,
		"devices": [(k,_device_info(v)) for (k,v) in top.devices.items()], "device_count": len(top.devices),
		"connectors": top.connectors.keys(), "connector_count": len(top.connectors)}

def _device_info(dev):
	res = {"id": dev.id, "type": dev.type, "host": dev.host_name}
	if dev.type == "openvz":
		res.update(vnc_port=dev.vnc_port, vnc_password=dev.vnc_password())
	return res

def _host_info(host):
	return {"name": str(host.name), "group": str(host.group), 
		"public_bridge": str(host.public_bridge), "device_count": host.device_set.count()}

def _top_access(top, user=None):
	if top.owner == user.name:
		return
	if user.is_admin:
		return
	raise Fault(Fault.ACCESS_TO_TOPOLOGY_DENIED, "access to topology %s denied" % top.id)

def _host_access(host, user=None):
	if not user.is_admin:
		raise Fault(Fault.ACCESS_TO_HOST_DENIED, "access to host %s denied" % host.hostname)

def syncdb():
	from django.core.management import call_command
	call_command('syncdb')
	
def login(username, password):
	import ldapauth
	if config.auth_dry_run:
		import generic
		if username=="guest":
			return generic.User(username, False, False)
		elif username=="admin":
			return generic.User(username, True, True)
		else:
			return generic.User(username, True, False)
	else:
		return ldapauth.login(username, password)

def account(user=None):
	logger.log("account()", user=user.name)
	return user

def host_list(group_filter=None, user=None):
	logger.log("host_list(group_filter=%s)" % group_filter, user=user.name)
	res=[]
	qs = hosts.Host.objects.all()
	if group_filter:
		qs=qs.filter(group__name=group_filter)
	for h in qs:
		res.append(_host_info(h))
	return res

def host_add(host_name, group_name, public_bridge, user=None):
	logger.log("host_add(%s,%s,%s)" % (host_name, group_name, public_bridge), user=user.name)
	_host_access(host_name,user)
	from hosts import Host, HostGroup
	import task, thread
	try:
		group = HostGroup.objects.get(name=group_name)
	except HostGroup.DoesNotExist:
		group = HostGroup.objects.create(name=group_name)
	host = Host(name=host_name, public_bridge=public_bridge, group=group)
	t = task.TaskStatus()
	thread.start_new_thread(host.check_save, (t,))
	return t.id

def host_remove(host_name, user=None):
	logger.log("host_remove(%s)" % host_name, user=user.name)
	_host_access(host_name,user)
	hosts.Host.objects.get(name=host_name).delete()
	return True