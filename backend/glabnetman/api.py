# -*- coding: utf-8 -*-

from host_store import *
from host import *
from topology_store import *
from topology import *
from log import *

import xmlrpclib, uuid
from cStringIO import StringIO

class Fault(xmlrpclib.Fault):
	UNKNOWN = -1
	NO_SUCH_TOPOLOGY = 100
	ACCESS_TO_TOPOLOGY_DENIED = 101
	NOT_A_REGULAR_USER = 102
	INVALID_TOPOLOGY_STATE_TRANSITION = 103
	IMPOSSIBLE_TOPOLOGY_CHANGE = 104
	NO_SUCH_HOST = 200
	NO_SUCH_HOST_GROUP = 201
	ACCESS_TO_HOST_DENIED = 202
	HOST_EXISTS = 203

class TopologyInfo():
	def __init__(self, topology):
		self.id = topology.id
		self.state = str(topology.state)
		self.is_created = self.state == TopologyState.CREATED
		self.is_uploaded = self.state == TopologyState.UPLOADED
		self.is_prepared = self.state == TopologyState.PREPARED
		self.is_started = self.state == TopologyState.STARTED
		self.owner = str(topology.owner)
		self.resource_usage = topology.resource_usage()

class HostInfo():
	def __init__(self, host):
		self.name = str(host.name)
		self.group = str(host.group)
		self.public_bridge = str(host.public_bridge)

class TaskStatus():
	tasks={}
	def __init__(self):
		self.id = str(uuid.uuid1())
		TaskStatus.tasks[self.id]=self
		self.output = StringIO()
		self.subtasks_total = 0
		self.subtasks_done = 0
	def done(self):
		self.subtasks_done = self.subtasks_total
	def dict(self):
		return {"id": self.id, "output": self.output.getvalue(), "subtasks_done": self.subtasks_done, "subtasks_total": self.subtasks_total, "done": self.subtasks_done==self.subtasks_total}

class PublicAPI():
	logger = Logger(Config.log_dir + "/api.log")

	def __init__(self):
		pass
	
	def _top_access(self, top_id, user=None):
		if TopologyStore.get(top_id).owner == user.username:
			return
		if user.is_admin:
			return
		raise Fault(Fault.ACCESS_TO_TOPOLOGY_DENIED, "access to topology %s denied" % top_id)

	def _host_access(self, host_name, user=None):
		if not user.is_admin:
			raise Fault(Fault.ACCESS_TO_HOST_DENIED, "access to host %s denied" % host_name)
	
	def top_info(self, id, user=None):
		PublicAPI.logger.log("top_info(%s)" % id, user=user.username)
		return TopologyInfo(TopologyStore.get(id))

	def top_list(self, filter_owner=None, filter_state=None, filter_host=None, user=None):
		self.logger.log("top_list(filter_owner=%s, filter_state=%s, filter_host=%s)" % (filter_owner, filter_state, filter_host), user=user.username)
		tops=[]
		for t in TopologyStore.topologies.values():
			if (filter_state==None or t.state==filter_state) and (filter_owner==None or t.owner==filter_owner) and (filter_host==None or filter_host in t.affected_hosts()):
				tops.append(TopologyInfo(t))
		return tops
	
	def top_import(self, xml, user=None):
		self.logger.log("top_import()", user=user.username, bigmessage=xml)
		if not user.is_user:
			raise Fault(Fault.NOT_A_REGULAR_USER, "only regular users can create topologies")
		dom=minidom.parseString(xml)
		top=Topology(dom,False)
		top.owner=user.username
		id=TopologyStore.add(top)
		return id
	
	def top_change(self, top_id, xml, user=None):
		PublicAPI.logger.log("top_change(%s)" % top_id, user=user.username, bigmessage=xml)
		self._top_access(top_id, user)
		dom=minidom.parseString(xml)
		newtop=Topology(dom,False)
		top = TopologyStore.get(top_id)
		return top.change(newtop)

	def top_remove(self, top_id, user=None):
		PublicAPI.logger.log("top_remove(%s)" % top_id, user=user.username)
		self._top_access(top_id, user)
		TopologyStore.remove(top_id)
		return True
	
	def top_prepare(self, top_id, user=None):
		PublicAPI.logger.log("top_prepare(%s)" % top_id, user=user.username)
		self._top_access(top_id, user)
		return TopologyStore.get(top_id).prepare()
	
	def top_destroy(self, top_id, user=None):
		PublicAPI.logger.log("top_destroy(%s)" % top_id, user=user.username)
		self._top_access(top_id, user)
		return TopologyStore.get(top_id).destroy()
	
	def top_upload(self, top_id, user=None):
		PublicAPI.logger.log("top_upload(%s)" % top_id, user=user.username)
		self._top_access(top_id, user)
		return TopologyStore.get(top_id).upload()
	
	def top_start(self, top_id, user=None):
		PublicAPI.logger.log("top_start(%s)" % top_id, user=user.username)
		self._top_access(top_id, user)
		return TopologyStore.get(top_id).start()
	
	def top_stop(self, top_id, user=None):
		PublicAPI.logger.log("top_stop(%s)" % top_id, user=user.username)
		self._top_access(top_id, user)
		return TopologyStore.get(top_id).stop()
	
	def top_get(self, top_id, include_ids=False, user=None):
		PublicAPI.logger.log("top_get(%s, include_ids=%s)" % (top_id, include_ids), user=user.username)
		self._top_access(top_id, user)
		top=TopologyStore.get(top_id)
		dom=top.create_dom(include_ids)
		return dom.toprettyxml(indent="\t", newl="\n")
		
	def host_list(self, group_filter=None, user=None):
		PublicAPI.logger.log("host_list(group_filter=%s)" % group_filter, user=user.username)
		hosts=[]
		for h in HostStore.hosts.values():
			if group_filter==None or h.group == group_filter:
				hosts.append(HostInfo(h))
		return hosts

	def host_add(self, host_name, group_name, public_bridge, user=None):
		PublicAPI.logger.log("host_add(%s,%s,%s)" % (host_name, group_name, public_bridge), user=user.username)
		self._host_access(host_name,user)
		host=Host()
		host.name = host_name
		host.group = group_name
		host.public_bridge = public_bridge
		host.check()
		HostStore.add(host)
		return True

	def host_remove(self, host_name, user=None):
		PublicAPI.logger.log("host_remove(%s)" % host_name, user=user.username)
		self._host_access(host_name,user)
		HostStore.remove(host_name)
		return True
		
	def account(self, user=None):
		PublicAPI.logger.log("account()", user=user.username)
		return user

	def task_status(self, id, user=None):
		PublicAPI.logger.log("task_status(%s)" % id, user=user.username)
		return TaskStatus.tasks[id].dict()