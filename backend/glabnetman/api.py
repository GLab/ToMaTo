# -*- coding: utf-8 -*-

import host_store, topology_store, config
from host import Host
from topology import Topology, TopologyState
from log import Logger
from task import TaskStatus, UploadTask, DownloadTask

import xmlrpclib, thread
from xml.dom import minidom

class Fault(xmlrpclib.Fault):
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
		"is_created": state == TopologyState.CREATED,
		"is_uploaded": state == TopologyState.UPLOADED, 
		"is_prepared": state == TopologyState.PREPARED,
		"is_started": state == TopologyState.STARTED,
		"owner": str(top.owner), "analysis": top.analysis,
		"devices": top.devices.keys(), "device_count": len(top.devices),
		"connectors": top.connectors.keys(), "connector_count": len(top.connectors)}

def _host_info(host):
	return {"name": str(host.name), "group": str(host.group), 
		"public_bridge": str(host.public_bridge), "device_count": len(host.devices)}

logger = Logger(config.log_dir + "/api.log")

def _top_access(top_id, user=None):
	if topology_store.get(top_id).owner == user.username:
		return
	if user.is_admin:
		return
	raise Fault(Fault.ACCESS_TO_TOPOLOGY_DENIED, "access to topology %s denied" % top_id)

def _host_access(host_name, user=None):
	if not user.is_admin:
		raise Fault(Fault.ACCESS_TO_HOST_DENIED, "access to host %s denied" % host_name)
	
def top_info(id, user=None):
	logger.log("top_info(%s)" % id, user=user.username)
	return _topology_info(topology_store.get(id))

def top_list(state_filter, owner_filter, host_filter, user=None):
	logger.log("top_list(state_filter=%s, owner_filter=%s, host_filter=%s)" % (state_filter, owner_filter, host_filter), user=user.username)
	tops=[]
	for t in topology_store.topologies.values():
		host_filter_matches=False
		if not host_filter=="*":
			for host in t.affected_hosts():
				if host.name == host_filter:
					host_filter_matches=True
		if (state_filter=="*" or t.state==state_filter) and (owner_filter=="*" or t.owner==owner_filter) and (host_filter=="*" or host_filter_matches):
			tops.append(_topology_info(t))
	return tops
	
def _parse_xml(xml):
	try:
		return minidom.parseString(xml)
	except Exception, exc:
		raise Fault(Fault.MALFORMED_XML, "Malformed XML: %s" % exc )

def top_import(xml, user=None):
	logger.log("top_import()", user=user.username, bigmessage=xml)
	if not user.is_user:
		raise Fault(Fault.NOT_A_REGULAR_USER, "only regular users can create topologies")
	dom = _parse_xml(xml)
	top=Topology(dom,False)
	top.owner=user.username
	id=topology_store.add(top)
	return id
	
def top_change(top_id, xml, user=None):
	logger.log("top_change(%s)" % top_id, user=user.username, bigmessage=xml)
	_top_access(top_id, user)
	dom = _parse_xml(xml)
	newtop=Topology(dom,False)
	top = topology_store.get(top_id)
	return top.change(newtop)

def top_remove(top_id, user=None):
	logger.log("top_remove(%s)" % top_id, user=user.username)
	_top_access(top_id, user)
	topology_store.remove(top_id)
	return True
	
def top_prepare(top_id, user=None):
	logger.log("top_prepare(%s)" % top_id, user=user.username)
	_top_access(top_id, user)
	return topology_store.get(top_id).prepare()
	
def top_destroy(top_id, user=None):
	logger.log("top_destroy(%s)" % top_id, user=user.username)
	_top_access(top_id, user)
	return topology_store.get(top_id).destroy()
	
def top_upload(top_id, user=None):
	logger.log("top_upload(%s)" % top_id, user=user.username)
	_top_access(top_id, user)
	return topology_store.get(top_id).upload()
	
def top_start(top_id, user=None):
	logger.log("top_start(%s)" % top_id, user=user.username)
	_top_access(top_id, user)
	return topology_store.get(top_id).start()
	
def top_stop(top_id, user=None):
	logger.log("top_stop(%s)" % top_id, user=user.username)
	_top_access(top_id, user)
	return topology_store.get(top_id).stop()
	
def top_get(top_id, include_ids=False, user=None):
	logger.log("top_get(%s, include_ids=%s)" % (top_id, include_ids), user=user.username)
	_top_access(top_id, user)
	top=topology_store.get(top_id)
	dom=top.create_dom(include_ids)
	return dom.toprettyxml(indent="\t", newl="\n")
		
def host_list(group_filter=None, user=None):
	logger.log("host_list(group_filter=%s)" % group_filter, user=user.username)
	hosts=[]
	for h in host_store.hosts.values():
		if group_filter==None or h.group == group_filter:
			hosts.append(_host_info(h))
	return hosts

def host_add(host_name, group_name, public_bridge, user=None):
	logger.log("host_add(%s,%s,%s)" % (host_name, group_name, public_bridge), user=user.username)
	_host_access(host_name,user)
	host=Host()
	host.name = host_name
	host.group = group_name
	host.public_bridge = public_bridge
	task = TaskStatus()
	thread.start_new_thread(host_store.check_add, (host,task))
	return task.id

def host_remove(host_name, user=None):
	logger.log("host_remove(%s)" % host_name, user=user.username)
	_host_access(host_name,user)
	host_store.remove(host_name)
	return True
		
def account(user=None):
	logger.log("account()", user=user.username)
	return user

def task_status(id, user=None):
	logger.log("task_status(%s)" % id, user=user.username)
	return TaskStatus.tasks[id].dict()
	
def upload_start(user=None):
	logger.log("upload_start()", user=user.username)
	task = UploadTask()
	return task.id

def upload_chunk(upload_id, chunk, user=None):
	#logger.log("upload_chunk(%s,...)" % upload_id, user=user.username)
	task = UploadTask.tasks[upload_id]
	task.chunk(chunk.data)
	return 0

def upload_image(top_id, device_id, upload_id, user=None):
	logger.log("upload_image(%s, %s, %s)" % (top_id, device_id, upload_id), user=user.username)
	upload = UploadTask.tasks[upload_id]
	upload.finished()
	_top_access(top_id, user)
	top=topology_store.get(top_id)
	return top.upload_image(device_id, upload.filename)

def download_image(top_id, device_id, user=None):
	logger.log("download_image(%s, %s)" % (top_id, device_id), user=user.username)
	_top_access(top_id, user)
	top=topology_store.get(top_id)
	filename = top.download_image(device_id)
	task = DownloadTask(filename)
	return task.id

def download_chunk(download_id, user=None):
	task = DownloadTask.tasks[download_id]
	data = task.chunk()
	return xmlrpclib.Binary(data)

host_store.init()
topology_store.init()