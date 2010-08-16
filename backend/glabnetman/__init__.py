# -*- coding: utf-8 -*-

import os
os.environ['DJANGO_SETTINGS_MODULE']="glabnetman.config"

import config, log, topology, hosts, fault, tasks

logger = log.Logger(config.log_dir + "/api.log")

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
	raise fault.new(fault.ACCESS_TO_TOPOLOGY_DENIED, "access to topology %s denied" % top.id)

def _host_access(host, user=None):
	if not user.is_admin:
		raise fault.new(fault.ACCESS_TO_HOST_DENIED, "access to host %s denied" % host.hostname)
	
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
	t = tasks.TaskStatus()
	thread.start_new_thread(host.check_save, (t,))
	return t.id

def host_remove(host_name, user=None):
	logger.log("host_remove(%s)" % host_name, user=user.name)
	_host_access(host_name,user)
	hosts.get_host(name=host_name).delete()
	return True

def _parse_xml(xml):
	try:
		from xml.dom import minidom
		dom = minidom.parseString(xml)
		return dom.getElementsByTagName ( "topology" )[0]
	except IndexError:
		raise fault.new(fault.MALFORMED_TOPOLOGY_DESCRIPTION, "Malformed topology description: topology must contain a <topology> tag")
	except Exception, exc:
		raise fault.new(fault.MALFORMED_XML, "Malformed XML: %s" % exc )

def top_info(id, user=None):
	logger.log("top_info(%s)" % id, user=user.username)
	return _topology_info(topology.get(id))

def top_list(state_filter, owner_filter, host_filter, user=None):
	logger.log("top_list(state_filter=%s, owner_filter=%s, host_filter=%s)" % (state_filter, owner_filter, host_filter), user=user.username)
	tops=[]
	all = topology.all()
	if not state_filter=="*":
		all = all.filter(state=state_filter)
	if not owner_filter=="*":
		all = all.filter(owner=owner_filter)
	if not host_filter=="*":
		all = all.filter(device__host__name=host_filter)
	for t in all:
		tops.append(_topology_info(t))
	return tops
	
def top_get(top_id, include_ids=False, user=None):
	logger.log("top_get(%s, include_ids=%s)" % (top_id, include_ids), user=user.username)
	top = topology.get(top_id)
	_top_access(top, user)
	from xml.dom import minidom
	doc = minidom.Document()
	dom = doc.createElement ( "topology" )
	top.save_to(dom, doc, include_ids)
	return dom.toprettyxml(indent="\t", newl="\n")

def top_import(xml, user=None):
	logger.log("top_import()", user=user.username, bigmessage=xml)
	if not user.is_user:
		raise fault.new(fault.NOT_A_REGULAR_USER, "only regular users can create topologies")
	dom = _parse_xml(xml)
	top=topology.Topology(dom, user.name)
	top.save()
	return top.id
	
def top_change(top_id, xml, user=None):
	logger.log("top_change(%s)" % top_id, user=user.username, bigmessage=xml)
	top = topology.get(top_id)
	_top_access(top, user)
	dom = _parse_xml(xml)
	newtop=topology.Topology(dom,user.name)
	return top.change(newtop)

def top_remove(top_id, user=None):
	logger.log("top_remove(%s)" % top_id, user=user.username)
	top = topology.get(top_id)
	_top_access(top, user)
	top.remove()
	return True
	
def top_prepare(top_id, user=None):
	logger.log("top_prepare(%s)" % top_id, user=user.username)
	top = topology.get(top_id)
	_top_access(top, user)
	return top.prepare()
	
def top_destroy(top_id, user=None):
	logger.log("top_destroy(%s)" % top_id, user=user.username)
	top = topology.get(top_id)
	_top_access(top, user)
	return top.destroy()
	
def top_upload(top_id, user=None):
	logger.log("top_upload(%s)" % top_id, user=user.username)
	top = topology.get(top_id)
	_top_access(top, user)
	return top.upload()
	
def top_start(top_id, user=None):
	logger.log("top_start(%s)" % top_id, user=user.username)
	top = topology.get(top_id)
	_top_access(top, user)
	return top.start()
	
def top_stop(top_id, user=None):
	logger.log("top_stop(%s)" % top_id, user=user.username)
	top = topology.get(top_id)
	_top_access(top, user)
	return top.stop()

def task_status(id, user=None):
	logger.log("task_status(%s)" % id, user=user.username)
	return tasks.TaskStatus.tasks[id].dict()
	
def upload_start(user=None):
	logger.log("upload_start()", user=user.username)
	task = tasks.UploadTask()
	return task.id

def upload_chunk(upload_id, chunk, user=None):
	#logger.log("upload_chunk(%s,...)" % upload_id, user=user.username)
	task = tasks.UploadTask.tasks[upload_id]
	task.chunk(chunk.data)
	return 0

def upload_image(top_id, device_id, upload_id, user=None):
	logger.log("upload_image(%s, %s, %s)" % (top_id, device_id, upload_id), user=user.username)
	upload = tasks.UploadTask.tasks[upload_id]
	upload.finished()
	top=topology.get(top_id)
	_top_access(top, user)
	return top.upload_image(device_id, upload.filename)

def download_image(top_id, device_id, user=None):
	logger.log("download_image(%s, %s)" % (top_id, device_id), user=user.username)
	top=topology.get(top_id)
	_top_access(top, user)
	filename = top.download_image(device_id)
	task = tasks.DownloadTask(filename)
	return task.id

def download_chunk(download_id, user=None):
	task = tasks.DownloadTask.tasks[download_id]
	data = task.chunk()
	import xmlrpclib
	return xmlrpclib.Binary(data)

