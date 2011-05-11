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

import dummynet, generic, config, os, subprocess, shutil, fault

from lib import util

# Interesting: http://minerva.netgroup.uniroma2.it/fairvpn
class TincConnector(generic.Connector):
	def upcast(self):
		return self
		
	def tincname(self, con):
		return "tinc_%s" % con.id

	def getStartTasks(self):
		taskset = generic.Connector.getStartTasks(self)
		for con in self.connectionSetAll():
			taskset.addTaskSet("connection-%s" % con, con.upcast().getStartTasks())
		return taskset

	def getStopTasks(self):
		taskset = generic.Connector.getStopTasks(self)
		for con in self.connectionSetAll():
			taskset.addTaskSet("connection-%s" % con, con.upcast().getStopTasks())
		return taskset
		
	def _clusterConnections(self):
		"""
A network with N nodes and cluster_size k has the following properties:

Number of connections is about: N * (k+1)

Network diameter is bounded by: 4 * ( log_k(N) + 2 )
Proof sketch:
- A network with N nodes has a clustering hierarchy depth that is at most log_k(N) + 2
  - In the worst case the site and host clustering split off only a minor part of the nodes but increase the depth by 2
- At each hierarchy level all clusters are connected by pairs of random nodes
  - In the worst case the path from the source to the pair and from the pair to the destination are both maximal
  - In the worst case the path to a connecting node on a higher level leads to a different node in the same lowest level cluster
  - The path has to be taken the whole hierarchy upwards to the root and downwards again
  
Maximal number of connections on a node is bounded by 2 * (k-1) * ( log_k(N) + 2 )
Proof sketch:
- A network with N nodes has a clustering hierarchy depth that is at most log_k(N) + 2
  - In the worst case the site and host clustering split off only a minor part of the nodes but increase the depth by 2
- At each each hierarchy level all clusters are interconnected by random nodes
  - In the worst case the same node is chosen over and over again as a random node
  - Every cluster has an outgoing and an incoming connection to other silbling clusters
  
Some nice properties:
- The shortest path between nodes on different sites will not contain nodes on a third site
- The shortest path between nodes on the same site will be completely within this site
- The shortest path between nodes on different hosts will not contain nodes on a third host
- The shortest path between nodes on the same host will be completely within this host
=> Latencies stay routhly the same as in a full mesh
=> Traffic is stays local if possible
"""
		CLUSTER_SIZE=10
		def isNode(n):
			return isinstance(n, generic.Connection)
		def divide(nodes):
			if isNode(nodes):
				return nodes
			if len(nodes) <= CLUSTER_SIZE:
				return nodes
			clusters={}
			for i in range(0,CLUSTER_SIZE):
				clusters[i]=[]
			i = 0
			for n in nodes:
				clusters[i].append(n)
				i = (i + 1) % CLUSTER_SIZE
			for i in range(0,CLUSTER_SIZE):
				if len(clusters[i]) == 1:
					clusters[i] = clusters[i][0]
			return [divide(c) for c in clusters.values()]
		def getHost(node):
			return node.interface.device.host.name
		def divideByHost(nodes):
			if len(nodes) <= CLUSTER_SIZE:
				return nodes
			clusters = {}
			for n in nodes:
				if not getHost(n) in clusters:
					clusters[getHost(n)] = []
				clusters[getHost(n)].append(n)
			return [divide(c) for c in clusters.values()]
		def getSite(node):
			return node.interface.device.host.group
		def divideBySite(nodes):
			if len(nodes) <= CLUSTER_SIZE:
				return nodes
			clusters = {}
			for n in nodes:
				if not getSite(n) in clusters:
					clusters[getSite(n)] = []
				clusters[getSite(n)].append(n)
			return [divideByHost(c) for c in clusters.values()]
		import random
		def randomNode(cluster):
			if isNode(cluster):
				return cluster
			else:
				return randomNode(random.choice(cluster))
		def connectionList(cluster):
			cons = []
			if isNode(cluster):
				return cons
			for a in cluster:
				#connect cluster internally
				cons += connectionList(a)
				#connect cluster externally
				for b in cluster:
					if a is b:
						#do not connect cluster with itself
						continue
					if isNode(a) and isNode(b) and repr(a) <= repr(b):
						#connect nodes only once but clusters twice
						continue
					cons.append((randomNode(a), randomNode(b)))
			return cons
		def connectionIdMap(clist):
			cmap = {}
			for (a, b) in clist:
				if not cmap.has_key(a.id):
					cmap[a.id] = set()
				cmap[a.id].add(b.id)
				if not cmap.has_key(b.id):
					cmap[b.id] = set()
				cmap[b.id].add(a.id)
			return cmap
		def writeDotFile(file, clist):
			fp = open(file, "w")
			fp.write("graph G {\n")
			for (a, b) in clist:
				aname = "\"%s.%s.%s\"" % (getSite(a), getHost(a), a.id)
				bname = "\"%s.%s.%s\"" % (getSite(b), getHost(b), b.id)
				fp.write("\t%s -- %s;\n" % (aname, bname) )
			fp.write("}\n")
			fp.close()
		allnodes = self.connectionSetAll()
		#print allnodes
		clustered = divideBySite(allnodes)
		#print clustered
		clist = connectionList(clustered)
		#print clist
		#print len(clist)*2
		#writeDotFile("graph", clist)
		cidmap = connectionIdMap(clist)
		#print cidmap
		return cidmap
		
	def getPrepareTasks(self):
		from lib import tasks
		taskset = generic.Connector.getPrepareTasks(self)
		taskset.addTask(tasks.Task("cluster-connections", self._clusterConnections))
		for con in self.connectionSetAll():
			taskset.addTaskSet("connection-%s" % con, con.upcast().getPrepareTasks())
		taskset.addTask(tasks.Task("created-host-files", depends=["connection-%s-create-host-file" % con for con in self.connectionSetAll()]))
		return taskset

	def getDestroyTasks(self):
		taskset = generic.Connector.getDestroyTasks(self)
		for con in self.connectionSetAll():
			taskset.addTaskSet("connection-%s" % con, con.upcast().getDestroyTasks())
		return taskset

	def configure(self, properties):
		generic.Connector.configure(self, properties)
	
	def connectionsAdd(self, iface_name, properties):
		iface = self.topology.interfacesGet(iface_name)
		if self.state == generic.State.STARTED or self.state == generic.State.PREPARED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot add connections to started or prepared connector: %s -> %s" % (iface_name, self.name) )
		if iface.device.state == generic.State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot add connections to running device: %s -> %s" % (iface_name, self.name) )
		if iface.isConnected():
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot add connections to connected interface: %s -> %s" % (iface_name, self.name) )
		con = TincConnection ()
		con.init()
		con.connector = self
		con.interface = iface
		con.configure(properties)
		con.save()

	def connectionsConfigure(self, iface_name, properties):
		iface = self.topology.interfacesGet(iface_name)
		con = self.connectionSetGet(iface)
		con.configure(properties)
		con.save()	
	
	def connectionsDelete(self, iface_name): #@UnusedVariable, pylint: disable-msg=W0613
		iface = self.topology.interfacesGet(iface_name)
		if self.state == generic.State.STARTED or self.state == generic.State.PREPARED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot delete connections to started or prepared connector: %s -> %s" % (iface_name, self.name) )
		if iface.device.state == generic.State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot delete connections to running devices: %s -> %s" % (iface_name, self.name) )
		con = self.connectionSetGet(iface)
		con.delete()

	def getResourceUsage(self):
		if self.state == generic.State.CREATED:
			disk = 0
		else:
			disk = 10000   
		if self.state == generic.State.STARTED:
			ports = len(self.connectionSetAll())
			memory = ( 1200 + 250 * ports ) * 1024
		else:
			memory = 0
			ports = 0
		traffic = 0
		for con in self.connectionSetAll():
			dev = con.interface.device
			if dev.host:
				br = self.bridgeName(con.interface)
				try:
					traffic += int(dev.host.execute("[ -f /sys/class/net/%s/statistics/rx_bytes ] && cat /sys/class/net/%s/statistics/rx_bytes || echo 0" % (br, br) ))
					traffic += int(dev.host.execute("[ -f /sys/class/net/%s/statistics/tx_bytes ] && cat /sys/class/net/%s/statistics/tx_bytes || echo 0" % (br, br) ))
				except:
					traffic = -1
		return {"disk": disk, "memory": memory, "ports": ports, "traffic": traffic}		


class TincConnection(dummynet.EmulatedConnection):
	def upcast(self):
		return self
	
	def configure(self, properties):
		if "gateway4" in properties or "gateway6" in properties:
			assert self.connector.state == generic.State.CREATED, "Cannot change gateways on prepared or started router: %s" % self
		dummynet.EmulatedConnection.configure(self, properties)
		if self.connector.type == "router":
			if not self.attributes["gateway4"]:
				self.attributes["gateway4"] = "10.0.0.254/24" 
			if not self.attributes["gateway6"]:
				self.attributes["gateway6"] = "fd01:ab1a:b1ab:0:0:FFFF:FFFF:FFFF/80" 
			if not len(self.attributes["gateway4"].split("/")) == 2:
				self.attributes["gateway4"] = self.attributes["gateway4"] + "/24"
			if not len(self.attributes["gateway6"].split("/")) == 2:
				self.attributes["gateway6"] = self.attributes["gateway6"] + "/80"
		
	def _startTinc(self):
		host = self.interface.device.host
		connector = self.connector.upcast()
		tincname = connector.tincname(self)
		host.free_port(self.attributes["tinc_port"])		
		host.execute ( "tincd --net=%s" % tincname)
		if not config.remote_dry_run:
			assert host.interface_exists(tincname), "Tinc deamon did not start"
		host.execute ( "ifconfig %s 0.0.0.0 up" %  tincname)

	def _setupRouting(self):
		host = self.interface.device.host
		connector = self.connector.upcast()
		tincname = connector.tincname(self)
		host.execute ("sysctl -q -w net.ipv6.conf.all.forwarding=1");
		host.execute ("sysctl -q -w net.ipv4.conf.all.forwarding=1");
		table_in = 1000 + 2 * self.id
		table_out = 1000 + 2 * self.id + 1 
		host.execute ( "ip addr add %s dev %s" % (self.attributes["gateway4"], self.bridgeName()))
		host.execute ( "ip addr add %s dev %s" % (self.attributes["gateway6"], self.bridgeName()))
		host.execute ( "ip link set up dev %s" % self.bridgeName())
		host.execute ( "grep '^%s ' /etc/iproute2/rt_tables || echo \"%s %s\" >> /etc/iproute2/rt_tables" % ( table_in, table_in, table_in ))
		host.execute ( "grep '^%s ' /etc/iproute2/rt_tables || echo \"%s %s\" >> /etc/iproute2/rt_tables" % ( table_out, table_out, table_out ))
		host.execute ( "iptables -t mangle -A PREROUTING -i %s -j MARK --set-mark %s" % ( tincname, table_in ))
		host.execute ( "iptables -t mangle -A PREROUTING -i %s -j MARK --set-mark %s" % ( self.bridgeName(), table_out ))
		host.execute ( "ip rule add fwmark %s table %s" % ( hex(table_in), table_in ))
		host.execute ( "ip rule add fwmark %s table %s" % ( hex(table_out), table_out ))
		host.execute ( "ip route add table %s default dev %s" % ( table_in, self.bridgeName() ))
		host.execute ( "ip route add table %s default dev %s" % ( table_out, tincname ))

	def _connectBridge(self):
		host = self.interface.device.host
		tincname = self.connector.upcast().tincname(self)
		host.bridge_connect(self.bridgeName(), tincname)
		
	def getStartTasks(self):
		from lib import tasks
		taskset = dummynet.EmulatedConnection.getStartTasks(self)
		taskset.addTask(tasks.Task("start-tinc", self._startTinc))
		if self.connector.type == "router":
			taskset.addTask(tasks.Task("setup-routing", self._setupRouting, depends="start-tinc"))
		else:
			taskset.addTask(tasks.Task("connect-bridge", self._connectBridge, depends="start-tinc"))
		return taskset
		
	def _teardownRouting(self):
		host = self.interface.device.host
		connector = self.connector.upcast()
		tincname = connector.tincname(self)
		table_in = 1000 + 2 * self.id
		table_out = 1000 + 2 * self.id + 1
		host.execute ( "iptables -t mangle -D PREROUTING -i %s -j MARK --set-mark %s" % ( tincname, table_in ))
		host.execute ( "iptables -t mangle -D PREROUTING -i %s -j MARK --set-mark %s" % ( self.bridgeName(), table_out ))
		host.execute ( "ip rule del fwmark %s table %s" % ( hex(table_in), table_in ))
		host.execute ( "ip rule del fwmark %s table %s" % ( hex(table_out), table_out ))
		host.execute ( "ip route del table %s default dev %s" % ( table_in, self.bridgeName() ))
		host.execute ( "ip route del table %s default dev %s" % ( table_out, tincname ))
		
	def _stopTinc(self):
		host = self.interface.device.host
		connector = self.connector.upcast()
		tincname = connector.tincname(self)
		host.execute ( "tincd --net=%s -k" % tincname)		
		
	def getStopTasks(self):
		from lib import tasks
		taskset = dummynet.EmulatedConnection.getStopTasks(self)
		if self.interface.device.host:
			taskset.addTask(tasks.Task("stop-tinc", self._stopTinc))
			if self.connector.type == "router":
				taskset.addTask(tasks.Task("teardown-routing", self._teardownRouting))
		return taskset

	def _assignBridgeId(self):
		if not self.attributes["bridge_id"]:
			self.attributes["bridge_id"] = self.interface.device.host.nextFreeBridge()		
			self.save()

	def _assignTincPort(self):
		if not self.attributes["tinc_port"]:
			self.attributes["tinc_port"] = self.interface.device.host.nextFreePort()
			self.save()

	def _createHostFile(self):
		host = self.interface.device.host
		connector = self.connector.upcast()
		tincname = connector.tincname(self)
		tincport = self.attributes["tinc_port"] 
		path = connector.topology.getControlDir(host.name) + "/" + tincname
		if not os.path.exists(path+"/hosts"):
			try:
				os.makedirs(path+"/hosts")
			except:
				pass
		subprocess.check_call (["openssl",  "genrsa",  "-out",  path + "/rsa_key.priv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self_host_fd = open(path+"/hosts/"+tincname, "w")
		self_host_fd.write("Address=%s\n" % host.name)
		self_host_fd.write("Port=%s\n" % tincport )
		self_host_fd.write("Cipher=none\n" )
		self_host_fd.write("Digest=none\n" )
		if connector.type == "router":
			self_host_fd.write("Subnet=%s\n" % util.calculate_subnet4(self.attributes["gateway4"]))
			self_host_fd.write("Subnet=%s\n" % util.calculate_subnet6(self.attributes["gateway6"]))
		subprocess.check_call (["openssl",  "rsa", "-pubout", "-in",  path + "/rsa_key.priv", "-out",  path + "/hosts/" + tincname + ".pub"], stderr=subprocess.PIPE)
		self_host_pub_fd = open(path+"/hosts/"+tincname+".pub", "r")
		shutil.copyfileobj(self_host_pub_fd, self_host_fd)
		self_host_fd.close()
		self_host_pub_fd.close()
		
	def _createConfigFile(self, task):
		host = self.interface.device.host
		connector = self.connector.upcast()
		tincname = connector.tincname(self)
		path = connector.topology.getControlDir(host.name) + "/" + tincname
		if not os.path.exists(path):
			try:
				os.makedirs(path)
			except:
				pass
		tinc_conf_fd = open(path+"/tinc.conf", "w")
		tinc_conf_fd.write ( "Mode=%s\n" % connector.type )
		tinc_conf_fd.write ( "Name=%s\n" % tincname )
		tinc_conf_fd.write ( "AddressFamily=ipv4\n" )
		connections = task.getDependency("cluster-connections").getResult()
		for con2 in connector.connectionSetAll():
			if not con2.id in connections[self.id]:
				#not connected
				continue
			tincname2 = connector.tincname(con2)
			tinc_conf_fd.write ( "ConnectTo=%s\n" % tincname2 )
		tinc_conf_fd.close()

	def _collectHostFiles(self, task):
		host = self.interface.device.host
		connector = self.connector.upcast()
		tincname = connector.tincname(self)
		path = connector.topology.getControlDir(host.name) + "/" + tincname
		connections = task.getDependency("cluster-connections").getResult()
		for con2 in connector.connectionSetAll():
			if not con2.id in connections[self.id]:
				#not connected
				continue
			host2 = con2.interface.device.host
			tincname2 = connector.tincname(con2)
			path2 = connector.topology.getControlDir(host2.name) + "/" + tincname2
			shutil.copy(path2+"/hosts/"+tincname2, path+"/hosts/"+tincname2)

	def _uploadFiles(self):
		host = self.interface.device.host
		connector = self.connector.upcast()
		tincname = connector.tincname(self)
		path = connector.topology.getControlDir(host.name) + "/" + tincname + "/"
		host.filePut(path, "/etc/tinc/" + tincname)

	def getPrepareTasks(self):
		from lib import tasks
		taskset = dummynet.EmulatedConnection.getPrepareTasks(self)
		taskset.addTask(tasks.Task("assign-bridge-id", self._assignBridgeId))
		taskset.addTask(tasks.Task("assign-tinc-port", self._assignTincPort))
		taskset.addTask(tasks.Task("create-host-file", self._createHostFile, depends=["assign-bridge-id", "assign-tinc-port"]))
		taskset.addTask(tasks.Task("create-config-file", self._createConfigFile, depends=["assign-bridge-id", "assign-tinc-port", "cluster-connections"], callWithTask=True))
		taskset.addTask(tasks.Task("collect-host-files", self._collectHostFiles, depends=["created-host-files", "cluster-connections"], callWithTask=True))
		taskset.addTask(tasks.Task("upload-files", self._uploadFiles, depends=["collect-host-files", "create-config-file"]))
		return taskset
		
	def _unassignBridgeId(self):
		del self.attributes["bridge_id"]

	def _unassignTincPort(self):
		del self.attributes["tinc_port"]

	def _deleteFiles(self):
		host = self.interface.device.host
		connector = self.connector.upcast()
		tincname = connector.tincname(self)
		host.file_delete ( "/etc/tinc/%s" % tincname, recursive=True)
		
	def getDestroyTasks(self):
		from lib import tasks
		taskset = dummynet.EmulatedConnection.getDestroyTasks(self)
		if self.interface.device.host:
			taskset.addTask(tasks.Task("delete-files", self._deleteFiles))
		taskset.addTask(tasks.Task("unassign-bridge-id", self._unassignBridgeId))
		taskset.addTask(tasks.Task("unassign-tinc-port", self._unassignTincPort))
		return taskset

	def toDict(self, auth):
		res = dummynet.EmulatedConnection.toDict(self, auth)	
		if not auth:
			del res["attrs"]["tinc_port"]	
			del res["attrs"]["bridge_id"]	
		return res
