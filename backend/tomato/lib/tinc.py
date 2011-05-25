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

import random, math, shutil, time

from tomato import generic, config

import process, fileutil, ifaceutil, util, tasks

class Mode:
	ROUTER = "router"
	SWITCH = "switch"
	HUB = "hub"

class Endpoint:
	#All other endpoints must be subclasses of this class
	def getSite(self):
		pass
	def getHost(self):
		pass
	def getId(self):
		pass
	def getPort(self):
		pass
	def getBridge(self):
		pass
	def getSubnets(self):
		pass

def _getHostName(node):
	return node.getHost()

def _getSiteName(node):
	return node.getSite()

def _randomNode(cluster):
	if _isEndpoint(cluster):
		return cluster
	else:
		return _randomNode(random.choice(cluster))

def _isEndpoint(n):
	return isinstance(n, Endpoint)

def _areEndpoints(list):
	for n in list:
		if not _isEndpoint(n):
			return False
	return True

"""
Cluster a list of tinc endpoints called "nodes" and create a list of connections to set up.

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

def _cluster(nodes):
	if _isEndpoint(nodes):
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
	return [_cluster(c) for c in clusters.values()]

def _clusterByHost(nodes):
	if len(nodes) <= CLUSTER_SIZE:
		return nodes
	clusters = {}
	for n in nodes:
		if not _getHostName(n) in clusters:
			clusters[_getHostName(n)] = []
		clusters[_getHostName(n)].append(n)
	return [_cluster(c) for c in clusters.values()]

def _clusterBySite(nodes):
	if len(nodes) <= CLUSTER_SIZE:
		return nodes
	clusters = {}
	for n in nodes:
		if not _getSiteName(n) in clusters:
			clusters[_getSiteName(n)] = []
		clusters[_getSiteName(n)].append(n)
	return [_clusterByHost(c) for c in clusters.values()]

def _connectClusters(cluster):
	cons = []
	if _isEndpoint(cluster):
		return cons
	for a in cluster:
		#connect cluster internally
		cons += _connectClusters(a)
		#connect cluster externally
		for b in cluster:
			if a is b:
				#do not connect cluster with itself
				continue
			if _isEndpoint(a) and _isEndpoint(b) and repr(a) <= repr(b):
				#connect nodes only once but clusters twice
				continue
			na = _randomNode(a)
			nb = _randomNode(b)
			cons.append((na, nb))
			cons.append((nb, na))
	return cons

def _determineConnections(allnodes):
	connections = _connectClusters(_clusterBySite(allnodes))
	assert _isConnected(allnodes, connections)
	assert len(connections) <= (len(allnodes) * (CLUSTER_SIZE+1)) * 1.5
	assert _diameter(allnodes, connections) <= 4 * ( math.log(len(allnodes), CLUSTER_SIZE) + 2 )
	assert _maxDegree(allnodes, connections) <= 2 * (CLUSTER_SIZE-1) * ( math.log(len(allnodes), CLUSTER_SIZE) + 2 )
	return connections

def _connectionMap(connections):
	map = {}
	for (src, dst) in connections:
		if not src in map:
			map[src] = set()
		map[src].add(dst)
	return map

def _isConnected(nodes, connections):
	map = _connectionMap(connections)
	nIn = set()
	nTodo = []
	nTodo.append(_randomNode(list(nodes)))
	while nTodo:
		n = random.choice(nTodo)
		nTodo.remove(n)
		nIn.add(n)
		for n in map[n]:
			if not n in nIn and not n in nTodo:
				nTodo.append(n)
	return len(nIn) == len(nodes)

def _shortestPaths(nodes, connections):
	#This is an implementation of the Floyd-Warshall algorithm
	dists = {}
	for src in nodes:
		for dst in nodes:
			val = len(nodes)
			if src == dst:
				val = 0
			if (src, dst) in connections:
				val = 1
			dists[(src,dst)] = val
	for mid in nodes:
		for src in nodes:
			for dst in nodes:
				dists[(src, dst)] = min( dists[(src,dst)], dists[(src,mid)] + dists[(mid,dst)] )
	return dists

def _diameter(nodes, connections):
	dists = _shortestPaths(nodes, connections)
	maxDist = 0
	for d in dists.values():
		maxDist = max(maxDist, d)
	return maxDist

def _maxDegree(nodex, connections):
	degrees={}
	def inc(n):
		if not n in degrees:
			degrees[n] = 0
		degrees[n] += 1
	maxD = 0
	for (src, dst) in connections:
		inc(src)
		inc(dst)
		maxD = max(maxD, max(degrees[src], degrees[dst]))
	return maxD

def _writeDotFile(file, clist):
	fp = open(file, "w")
	fp.write("graph G {\n")
	for (a, b) in clist:
		aname = "\"%s.%s.%s\"" % (_getSiteName(a), _getHostName(a), a.id)
		bname = "\"%s.%s.%s\"" % (_getSiteName(b), _getHostName(b), b.id)
		fp.write("\t%s -- %s;\n" % (aname, bname) )
	fp.write("}\n")
	fp.close()
	
def _tincName(endpoint):
	return "tinc_%d" % endpoint.getId()
	
def _pidFile(endpoint):
	return "/var/run/tinc.%s.pid" % _tincName(endpoint)

def _configDir(endpoint):
	return "/etc/tinc/%s" % _tincName(endpoint)
	
def getState(endpoint):
	assert _isEndpoint(endpoint)
	host = endpoint.getHost()
	assert host
	if not fileutil.existsDir(host, _configDir(endpoint)):
		return generic.State.CREATED
	if not fileutil.existsFile(host, _pidFile(endpoint)):
		return generic.State.PREPARED
	if not process.processRunning(host, _pidFile(endpoint), "tincd"):
		return generic.State.PREPARED
	return generic.State.STARTED
	
def _startEndpoint(endpoint):
	assert getState(endpoint) == generic.State.PREPARED
	host = endpoint.getHost()
	assert host
	assert process.portFree(host, endpoint.getPort())
	iface = _tincName(endpoint)
	host.execute("tincd --net=%s" % iface )
	util.waitFor(lambda :ifaceutil.interfaceExists(host, iface))
	assert ifaceutil.interfaceExists(host, iface), "Tinc deamon did not start"
	ifaceutil.ifup(host, iface)

def _stopEndpoint(endpoint):
	assert getState(endpoint) != generic.State.CREATED
	host = endpoint.getHost()
	assert host
	host.execute("tincd --net=%s -k" % _tincName(endpoint))
	assert getState(endpoint) == generic.State.PREPARED

def _setupRouting(endpoint):
	host = endpoint.getHost()
	assert host
	bridge = endpoint.getBridge()
	assert bridge
	id = endpoint.getId()
	assert id
	assert ifaceutil.bridgeExists(host, bridge)
	tincname = _tincName(endpoint)
	assert ifaceutil.interfaceExists(host, tincname)
	assert not ifaceutil.interfaceBridge(host, tincname)
	#enable ip forwarding
	host.execute ("sysctl -q -w net.ipv6.conf.all.forwarding=1");
	host.execute ("sysctl -q -w net.ipv4.conf.all.forwarding=1");
	#calculate unique table ids
	table_in = 1000 + 2 * id
	table_out = 1000 + 2 * id + 1
	#create tables in rt_tables if they don't exist 
	host.execute ( "grep '^%s ' /etc/iproute2/rt_tables || echo \"%s %s\" >> /etc/iproute2/rt_tables" % ( table_in, table_in, table_in ))
	host.execute ( "grep '^%s ' /etc/iproute2/rt_tables || echo \"%s %s\" >> /etc/iproute2/rt_tables" % ( table_out, table_out, table_out ))
	#mark all packages based on incoming interfaces
	host.execute ( "iptables -t mangle -A PREROUTING -i %s -j MARK --set-mark %s" % ( tincname, table_in ))
	host.execute ( "iptables -t mangle -A PREROUTING -i %s -j MARK --set-mark %s" % ( bridge, table_out ))
	#create rules to use routing tables according to the marks of the packages
	host.execute ( "ip rule add fwmark %s table %s" % ( hex(table_in), table_in ))
	host.execute ( "ip rule add fwmark %s table %s" % ( hex(table_out), table_out ))
	#create routing table with only a default device
	host.execute ( "ip route add table %s default dev %s" % ( table_in, bridge ))
	host.execute ( "ip route add table %s default dev %s" % ( table_out, tincname ))

def _teardownRouting(endpoint):
	host = endpoint.getHost()
	assert host
	id = endpoint.getId()
	assert id
	bridge = endpoint.getBridge()
	assert bridge
	assert getState(endpoint) != generic.State.CREATED
	tincname = _tincName(endpoint)
	#not disabling ip forwarding
	table_in = 1000 + 2 * id
	table_out = 1000 + 2 * id + 1
	host.execute ( "iptables -t mangle -D PREROUTING -i %s -j MARK --set-mark %s" % ( tincname, table_in ))
	host.execute ( "iptables -t mangle -D PREROUTING -i %s -j MARK --set-mark %s" % ( bridge, table_out ))
	host.execute ( "ip rule del fwmark %s table %s" % ( hex(table_in), table_in ))
	host.execute ( "ip rule del fwmark %s table %s" % ( hex(table_out), table_out ))
	host.execute ( "ip route del table %s default dev %s" % ( table_in, bridge ))
	host.execute ( "ip route del table %s default dev %s" % ( table_out, tincname ))
		
def _connectEndpoint(endpoint, mode):
	host = endpoint.getHost()
	assert host
	bridge = endpoint.getBridge()
	assert bridge
	if not ifaceutil.bridgeExists(host, bridge):
		ifaceutil.bridgeCreate(host, bridge)
	if mode == Mode.ROUTER:
		_setupRouting(endpoint)
	else:
		ifaceutil.ifup(host, bridge)
		ifaceutil.bridgeConnect(host, bridge, _tincName(endpoint))
		
def startNetwork(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	for ep in endpoints:
		_startEndpoint(ep)
		_connectEndpoint(ep, mode)

def getStartNetworkTasks(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	taskset = tasks.TaskSet()
	reverse = util.curry(_tryStopNetwork, [endpoints, mode])
	for ep in endpoints:
		id = ep.getId()
		assert id
		taskset.addTask(tasks.Task("start-endpoint-%s" % id, _startEndpoint, args=(ep,), reverseFn=reverse))
		taskset.addTask(tasks.Task("connect-endpoint-%s" % id, _connectEndpoint, args=(ep,mode), reverseFn=reverse, depends="start-endpoint-%s" % id))
	return taskset
		
def stopNetwork(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	for ep in endpoints:
		if mode == Mode.ROUTER:
			_teardownRouting(ep)
		_stopEndpoint(ep)

def _tryStopNetwork(endpoints, mode=Mode.SWITCH, *args):
	for ep in endpoints:
		if mode == Mode.ROUTER:
			try:
				_teardownRouting(ep)
			except:
				pass
		try:
			_stopEndpoint(ep)
		except:
			pass

def getStopNetworkTasks(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	taskset = tasks.TaskSet()
	reverse = util.curry(_tryStopNetwork, [endpoints, mode])
	for ep in endpoints:
		id = ep.getId()
		assert id
		if mode == Mode.ROUTER:
			taskset.addTask(tasks.Task("teardown-routing-%s" % id, _teardownRouting, args=(ep,), reverseFn=reverse))
		taskset.addTask(tasks.Task("stop-endpoint-%s" % id, _stopEndpoint, args=(ep,), reverseFn=reverse))
	return taskset

def prepareNetwork(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	connections = _determineConnections(endpoints)
	for ep in endpoints:
		_createHostFile(ep)
		_createConfigFile(ep, mode, connections)
	for ep in endpoints:
		_collectHostFiles(ep, connections)
	for ep in endpoints:
		_uploadFiles(ep)
		_removeTemporaryFiles(ep)

def _createConfigTask(task, ep, mode):
	connections = task.getDependency("determine-connections").getResult()
	_createHostFile(ep)
	_createConfigFile(ep, mode, connections)	

def _collectConfigTask(task, ep):
	connections = task.getDependency("determine-connections").getResult()
	_collectHostFiles(ep, connections)

def _useConfigTask(ep):
	_uploadFiles(ep)
	_removeTemporaryFiles(ep)

def getPrepareNetworkTasks(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	reverse = util.curry(_tryDestroyNetwork, [endpoints, mode])
	taskset = tasks.TaskSet()
	taskset.addTask(tasks.Task("determine-connections", _determineConnections, args=(endpoints,)))
	for ep in endpoints:
		id = ep.getId()
		assert id
		taskset.addTask(tasks.Task("create-config-%s" % id, _createConfigTask, args=(ep, mode,), callWithTask=True, reverseFn=reverse, depends="determine-connections"))
	alldeps = ["create-config-%s" % ep.getId() for ep in endpoints]
	alldeps.append("determine-connections")
	for ep in endpoints:		
		id = ep.getId()
		assert id
		taskset.addTask(tasks.Task("collect-config-%s" % id, _collectConfigTask, args=(ep,), callWithTask=True, reverseFn=reverse, depends=alldeps))
	alldeps = ["collect-config-%s" % ep.getId() for ep in endpoints]
	for ep in endpoints:		
		id = ep.getId()
		assert id
		taskset.addTask(tasks.Task("use-config-%s" % id, _useConfigTask, args=(ep,), reverseFn=reverse, depends=alldeps))
	return taskset

def destroyNetwork(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	for ep in endpoints:
		_deleteFiles(ep)

def _tryDestroyNetwork(endpoints, mode=Mode.SWITCH, *args):
	_tryStopNetwork(endpoints, mode)
	for ep in endpoints:
		try:
			_deleteFiles(ep)
		except:
			pass

def getDestroyNetworkTasks(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	reverse = util.curry(_tryDestroyNetwork, [endpoints, mode])
	taskset = tasks.TaskSet()
	for ep in endpoints:
		id = ep.getId()
		assert id
		taskset.addTask(tasks.Task("delete-files-%s" % id, _deleteFiles, reverseFn=reverse, args=(ep,)))
	return taskset
	
def _tmpPath(endpoint):
	return "%s/%s" % ( config.local_control_dir, _tincName(endpoint) )
	
def _createHostFile(endpoint):
	path = _tmpPath(endpoint)
	fileutil.mkdir(util.localhost, path+"/hosts")
	util.localhost.execute("openssl genrsa -out %s/rsa_key.priv" % path)
	hostFd = open("%s/hosts/%s" % (path, _tincName(endpoint)), "w")
	hostFd.write("Address=%s\n" % endpoint.getHost())
	hostFd.write("Port=%s\n" % endpoint.getPort())
	hostFd.write("Cipher=none\n")
	hostFd.write("Digest=none\n")
	for sn in endpoint.getSubnets():
		hostFd.write("Subnet=%s\n" % sn)
	util.localhost.execute("openssl rsa -pubout -in %s/rsa_key.priv -out %s/hosts/%s.pub" % (path, path, _tincName(endpoint)))
	hostPubFd = open("%s/hosts/%s.pub" % (path, _tincName(endpoint)), "r")
	shutil.copyfileobj(hostPubFd, hostFd)
	hostFd.close()
	hostPubFd.close()
	fileutil.delete(util.localhost, "%s/hosts/%s.pub" % (path, _tincName(endpoint)))
		
def _createConfigFile(endpoint, mode, connections):
	path = _tmpPath(endpoint)
	fileutil.mkdir(util.localhost, path)
	tincConfFd = open(path+"/tinc.conf", "w")
	tincConfFd.write ( "Mode=%s\n" % mode )
	tincConfFd.write ( "Name=%s\n" % _tincName(endpoint) )
	tincConfFd.write ( "AddressFamily=ipv4\n" )
	for (src, dst) in connections:
		if src == endpoint:
			tincConfFd.write ( "ConnectTo=%s\n" % _tincName(dst) )
	tincConfFd.close()

def _collectHostFiles(endpoint, connections):
	path = _tmpPath(endpoint)
	for (src, dst) in connections:
		if src == endpoint:
			path2 = _tmpPath(dst)
			shutil.copy("%s/hosts/%s" % (path2, _tincName(dst)), "%s/hosts/%s" % (path, _tincName(dst)))

def _removeTemporaryFiles(endpoint):
	fileutil.delete(util.localhost, _tmpPath(endpoint), recursive=True)

def _uploadFiles(endpoint):
	if getState(endpoint) == generic.State.PREPARED:
		_deleteFiles(endpoint)
	assert getState(endpoint) == generic.State.CREATED, "endpoint was not created: %s: %s" % (endpoint, getState(endpoint))
	endpoint.getHost().filePut(_tmpPath(endpoint)+"/", _configDir(endpoint))

def _deleteFiles(endpoint):
	assert getState(endpoint) != generic.State.STARTED
	fileutil.delete(endpoint.getHost(), _configDir(endpoint), recursive=True)
	
def estimateDiskUsage(numNodes):
	# for each node:
	# - 1 block for base directory
	# - 1 block for hosts directory
	# - 1 block for private key
	# - 1 block for config file
	# - 1 block for own host file
	# for each connection (nodes * (CLUSTER_SIZE +1)):
	# - 1 block for host file
	return len(numNodes) * ( CLUSTER_SIZE + 6 ) * 4096

def estimateMemoryUsage(numNodes):
	# each instanse on tinc estimated to 1.5 MB
	return len(numNodes) * 1500