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

import random, math, shutil

from tomato import generic, config

import process, fileutil, ifaceutil, util, tasks, exceptions

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
	def getGateways(self):
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

Number of connections is bounded by: N*(k+3)
Proof sketch:
- A network of N nodes contains N/k clusters containing nodes and about N/(k*(k-1)) clusters consisting of clusters.
- The node clusters have:
  - k*(k-1) internal connections
  - 2*(k-1) external connections to other node clusters
- The cluster clusters have:
  - 2*k*(k-1) internal connections
  - 2*(k-1) external connections to other cluster clusters  

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
  - Every cluster has an outgoing and an incoming connection to other sibling clusters
  
Some nice properties:
- The shortest path between nodes on different sites will not contain nodes on a third site
- The shortest path between nodes on the same site will be completely within this site
- The shortest path between nodes on different hosts will not contain nodes on a third host
- The shortest path between nodes on the same host will be completely within this host
=> Latencies stay routhly the same as in a full mesh
=> Traffic is stays local if possible
"""

CLUSTER_SIZE=5

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
		host = _getHostName(n)
		if not host in clusters:
			clusters[host] = []
		clusters[host].append(n)
	return _cluster([_cluster(c) for c in clusters.values()])

def _clusterBySite(nodes):
	if len(nodes) <= CLUSTER_SIZE:
		return nodes
	clusters = {}
	for n in nodes:
		site = _getSiteName(n)
		if not site in clusters:
			clusters[site] = []
		clusters[site].append(n)
	return _cluster([_clusterByHost(c) for c in clusters.values()])

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
	if not allnodes:
		return connections
	assert _isConnected(allnodes, connections), "Clustering resulted in unconnected graph"
	assert len(connections) <= len(allnodes) * (CLUSTER_SIZE+3), "Clustering produced too many connections: %d devices but %d connections" % (len(allnodes), len(connections))
	diameter = _diameter(allnodes, connections)
	assert diameter <= 4 * ( math.log(len(allnodes), CLUSTER_SIZE) + 2 ), "Clustering produced a network with too big diameter: %d devices, %f diameter" % (len(allnodes), diameter)
	maxDegree = _maxDegree(allnodes, connections)
	assert maxDegree <= 2 * (CLUSTER_SIZE-1) * ( math.log(len(allnodes), CLUSTER_SIZE) + 2 ), "Clustering produced a network with too big maximal degree: %d devices, %d maximal degree" % (len(allnodes), maxDegree)
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
	if not nodes:
		return True
	nTodo.append(_randomNode(list(nodes)))
	while nTodo:
		n = random.choice(nTodo)
		nTodo.remove(n)
		nIn.add(n)
		if n in map:
			for n2 in map[n]:
				if not n2 in nIn and not n2 in nTodo:
					nTodo.append(n2)
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
	
def interfaceName(endpoint):
	return _tincName(endpoint)
	
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
	state = getState(endpoint)
	assert state != generic.State.CREATED
	if state == generic.State.STARTED:
		_stopEndpoint(endpoint)
	host = endpoint.getHost()
	assert host
	if not process.portFree(host, endpoint.getPort()):
		process.killPortUser(host, endpoint.getPort())
	iface = _tincName(endpoint)
	host.execute("tincd --net=%s" % iface )
	util.waitFor(lambda :ifaceutil.interfaceExists(host, iface))
	assert ifaceutil.interfaceExists(host, iface), "Tinc deamon did not start"
	ifaceutil.ifup(host, iface)

def _stopEndpoint(endpoint):
	state = getState(endpoint)
	if state != generic.State.STARTED:
		return
	host = endpoint.getHost()
	assert host
	try:
		host.execute("tincd --net=%s -k" % _tincName(endpoint))
	except exceptions.CommandError, exc:
		if exc.errorCode != 1: #tincd was not running
			raise
	util.waitFor(lambda :getState(endpoint) != generic.State.STARTED, 2.0)
	if getState(endpoint) == generic.State.STARTED:
		process.killPidfile(host, _pidFile(endpoint), force=True)
	assert getState(endpoint) != generic.State.STARTED

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
	#add gateway addresses
	for gw in endpoint.getGateways():
		ifaceutil.addAddress(host, bridge, gw)
	#set bridge up
	ifaceutil.ifup(host, bridge)
	ifaceutil.connectInterfaces(host, bridge, tincname, id, endpoint.getGateways())
	for gw in endpoint.getGateways():
		ip = gw.split("/")[0]
		util.waitFor(lambda :ifaceutil.reachable(host, ip, iface=bridge))
		assert ifaceutil.reachable(host, ip, iface=bridge), "Cannot reach %s in interface %s" % (ip, bridge)

def _teardownRouting(endpoint, mode):
	if mode != Mode.ROUTER:
		return
	host = endpoint.getHost()
	assert host
	id = endpoint.getId()
	assert id
	try:
		bridge = endpoint.getBridge()
	except:
		return
	assert getState(endpoint) != generic.State.CREATED
	tincname = _tincName(endpoint)
	ifaceutil.disconnectInterfaces(host, bridge, tincname, id)
		
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

def _startEndpointTask(endpoint, mode=Mode.SWITCH):
	_startEndpoint(endpoint)
	_connectEndpoint(endpoint, mode)

def getStartNetworkTasks(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	taskset = tasks.TaskSet()
	for ep in endpoints:
		id = ep.getId()
		assert id
		start_ep = tasks.Task("start-endpoint-%s" % id, _startEndpointTask, args=(ep,mode))
		taskset.add(start_ep)
	return taskset
		
def stopNetwork(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	for ep in endpoints:
		_teardownRouting(ep, mode)
		_stopEndpoint(ep)

def _stopEndpointTask(endpoint, mode=Mode.SWITCH):
	_teardownRouting(endpoint, mode)
	_stopEndpoint(endpoint)

def getStopNetworkTasks(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	taskset = tasks.TaskSet()
	for ep in endpoints:
		id = ep.getId()
		assert id
		stop_ep = tasks.Task("stop-endpoint-%s" % id, _stopEndpointTask, args=(ep,mode,))
		taskset.add(stop_ep)
	return taskset

def prepareNetwork(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	_prepareFiles(endpoints, mode)
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

def _prepareEndpointTask(ep):
	state = getState(ep)
	if state == generic.State.STARTED:
		_stopEndpoint(ep)
	_uploadFiles(ep)
	_removeTemporaryFiles(ep)

def _prepareFiles(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	connections = _determineConnections(endpoints)
	for ep in endpoints:
		_createHostFile(ep)
		_createConfigFile(ep, mode, connections)
	for ep in endpoints:
		_collectHostFiles(ep, connections)

def getPrepareNetworkTasks(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	taskset = tasks.TaskSet()
	prepare_files = tasks.Task("prepare-files", _prepareFiles, args=(endpoints,mode,))
	taskset.add(prepare_files)
	for ep in endpoints:		
		id = ep.getId()
		assert id
		taskset.add(tasks.Task("prepare-endpoint-%s" % id, _prepareEndpointTask, args=(ep,), after=prepare_files))
	return taskset

def destroyNetwork(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	for ep in endpoints:
		_deleteFiles(ep)

def getDestroyNetworkTasks(endpoints, mode=Mode.SWITCH):
	assert _areEndpoints(endpoints)
	taskset = tasks.TaskSet()
	for ep in endpoints:
		id = ep.getId()
		assert id
		taskset.add(tasks.Task("delete-files-%s" % id, _deleteFiles, args=(ep,)))
	return taskset
	
def _tmpPath(endpoint):
	return "%s/%s" % ( config.LOCAL_TMP_DIR, _tincName(endpoint) )
	
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
	if getState(endpoint) == generic.State.STARTED:
		_stopEndpoint(endpoint)
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
	return numNodes * ( CLUSTER_SIZE + 6 ) * 4096

def estimateMemoryUsage(numNodes):
	# each instanse on tinc estimated to 1.5 MB
	return numNodes * 1500