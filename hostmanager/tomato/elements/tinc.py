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

import os, shutil, hashlib, base64
from .. import connections, elements, config
from ..lib import util, cmd #@UnresolvedImport
from ..lib.attributes import Attr #@UnresolvedImport
from ..lib.cmd import process, net, path #@UnresolvedImport
from ..lib.error import UserError, InternalError

DOC="""
Element type: ``tinc``

Description:
	This element type represents one endpoint of a Tinc VPN network. The 
	endpoint will connect to all configured peers and will form a peer-to-peer
	VPN with them, forwarding the packets where they belong to.
	Note: The unique name of each endpoint is determined by decoding the public
	key (base64-encoded PEM format) and calculating the md5 sum of that value.
	
Possible parents: None

Possible children: None

Default state: *created*

Removable in states: *created*

Connection concepts: *interface*

States:
	*created*: In this state, the endpoint is known but not active.
	*started*: In this state, the endpoint is active and ready to send/receive packets. 

Attributes:
	*peers*: list of dicts, changeable in state *created*, default: ``[]``
		The list of peers to connect to/accept connections from. Each peer must
		be a key/value map with the following attributes:
		
			*host* (str):
			  the hostname/ip address of the peer
			*port* (int):
			  the port of the peer
			*pubkey* (str):
			  the public key of the peer in PEM format  
			  
	*mode*: str, changeable in state *created*, default: ``switch`` 
		The mode the endpoint operates in. This attribute can either be 
		"switch" or "hub". In the switch mode the endpoint will learn MAC 
		addresses and forward packets directly to the associated endpoint if 
		possible. If a packet for an unknown MAC address is seen, it will be
		broadcasted to all other endpoints. In the hub mode the endpoint will
		broadcast all packets and not learn any MAC addreses.
		Note: All endpoints in one VPN should operate in the same mode, 
		otherwise strange behaviour can result.		
	*port*: int, read-only
		The port on this host on which the endpoint is listening in state 
		started.
	*pubkey*: str, read-only
		The public key of this endpoint.
		
		
Actions:
	*start*, callable in state *created*, next state: *started*
	 	Starts the endpoint so that it is ready to send/receive packets.
	*stop*, callable in state *started*, next state: *created*
	 	Stops the endpoint.
"""


ST_CREATED = "created"
ST_STARTED = "started"

class Tinc(elements.Element):
	port_attr = Attr("port", type="int")
	port = port_attr.attribute()
	path_attr = Attr("path")
	path = path_attr.attribute()
	mode_attr = Attr("mode", desc="Mode", states=[ST_CREATED], options={"hub": "Hub (broadcast)", "switch": "Switch (learning)"}, default="switch")
	mode = mode_attr.attribute()
	privkey_attr = Attr("privkey", desc="Private key")
	privkey = privkey_attr.attribute()
	pubkey_attr = Attr("pubkey", desc="Public key")
	pubkey = pubkey_attr.attribute()
	peers_attr = Attr("peers", desc="Peers", states=[ST_CREATED], default=[])
	peers = peers_attr.attribute()

	TYPE = "tinc"
	CAP_ACTIONS = {
		"start": [ST_CREATED],
		"stop": [ST_STARTED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CAP_NEXT_STATE = {
		"start": ST_STARTED,
		"stop": ST_CREATED,
	}	
	CAP_ATTRS = {
		"mode": mode_attr,
		"peers": peers_attr,
		"timeout": elements.Element.timeout_attr
	}
	CAP_CHILDREN = {}
	CAP_PARENT = [None]
	CAP_CON_CONCEPTS = [connections.CONCEPT_INTERFACE]
	DEFAULT_ATTRS = {"mode": "switch"}
	DOC = DOC
	__doc__ = DOC
	
	class Meta:
		db_table = "tomato_tinc"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		self.port = self.getResource("port")
		self.path = self.dataPath()
		self.privkey = cmd.run(["openssl", "genrsa"], ignoreErr=True)
		self.pubkey = cmd.run(["openssl", "rsa", "-pubout"], ignoreErr=True, input=self.privkey)

	def _interfaceName(self):
		return "tinc%d" % self.id

	def interfaceName(self):
		return self._interfaceName() if self.state == ST_STARTED else None

	def _name(self, pubkey):
		# decode pubkey so two same keys are binary equivalent
		pubkey = base64.b64decode("".join(map(lambda s: "" if "-----" in s else s.strip(), pubkey.splitlines())))
		return hashlib.md5(pubkey).hexdigest()
				
	def modify_mode(self, val):
		self.mode = val

	def modify_peers(self, val):
		for peer in val:
			UserError.check("host" in peer, UserError.INVALID_VALUE, "Peer does not contain host")
			UserError.check("port" in peer, UserError.INVALID_VALUE, "Peer does not contain port")
			UserError.check("pubkey" in peer, UserError.INVALID_VALUE, "Peer does not contain pubkey")
		self.peers = val

	def action_start(self):
		# clean path 
		if os.path.exists(self.path):
			shutil.rmtree(self.path)
		os.makedirs(self.path)
		hostPath = os.path.join(self.path, "hosts")
		os.mkdir(hostPath)
		myName = self._name(self.pubkey)
		with open(os.path.join(self.path, "rsa.priv"), "w") as fp:
			# private key -> rsa.priv 
			fp.write(self.privkey)
		with open(os.path.join(self.path, "tinc.conf"), "w") as fp:
			fp.write("Interface=%s\n" % self._interfaceName())
			fp.write("DeviceType=tap\n")
			fp.write("Mode=%s\n" % self.mode)
			fp.write("Name=%s\n" % myName)
			fp.write("PrivateKeyFile=%s\n" % os.path.join(self.path, "rsa.priv"))
			for peer in self.peers:
				fp.write("ConnectTo=%s\n" % self._name(peer["pubkey"]))
		with open(os.path.join(hostPath, myName), "w") as fp:
			# own host entry -> hosts/[myname]
			fp.write("Port=%d\n" % self.port)
			fp.write("Cipher=none\n")
			fp.write("Digest=none\n")
			# public key -> hosts/[myname]
			fp.write(self.pubkey)
		for peer in self.peers:
			name = self._name(peer["pubkey"])
			with open(os.path.join(hostPath, name), "w") as fp:
				# peer host entry -> hosts/[name]
				fp.write("Address=%s %d\n" % (peer["host"], peer["port"]))
				fp.write("Cipher=none\n")
				fp.write("Digest=none\n")
				# peer public key -> hosts/[name]
				fp.write(peer["pubkey"])
		cmd.run(["tincd", "-c", self.path, "--pidfile=%s" % os.path.join(self.path, "tinc.pid")])
		self.setState(ST_STARTED)
		ifName = self._interfaceName()
		InternalError.check(util.waitFor(lambda :net.ifaceExists(ifName)), InternalError.ASSERTION,
			"Interface did not start properly", data={"interface": ifName})
		net.ifUp(ifName)
		con = self.getConnection()
		if con:
			con.connectInterface(self._interfaceName())

	def action_stop(self):
		con = self.getConnection()
		if con:
			con.disconnectInterface(self._interfaceName())
		cmd.runUnchecked(["tincd", "-k", "-c", self.path, "--pidfile=%s" % os.path.join(self.path, "tinc.pid")])
		self.setState(ST_CREATED)
		if path.exists(self.path):
			path.remove(self.path, recursive=True)

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		if "privkey" in info["attrs"]:
			del info["attrs"]["privkey"] #no need to expose this information
		return info

	def _getPid(self):
		pidFile = os.path.join(self.path, "tinc.pid")
		if not os.path.exists(pidFile):
			return None
		with open(pidFile) as fp:
			return int(fp.readline().strip())

	def updateUsage(self, usage, data):
		if not self.path:
			return
		if path.exists(self.path):
			usage.diskspace = path.diskspace(self.path)
		if self.state == ST_STARTED:
			return
		pid = self._getPid()
		if pid:
			usage.memory = process.memory(pid)
			cputime = process.cputime(pid)
			usage.updateContinuous("cputime", cputime, data)
			trafficA, trafficB = net.trafficInfo(self.interfaceName())
			if not trafficA is None and not trafficB is None:
				traffic = trafficA + trafficB
				usage.updateContinuous("traffic", traffic, data)
			
if not config.MAINTENANCE:
	tincVersion = cmd.getDpkgVersion("tinc")
	if [1, 0] <= tincVersion <= [2, 0]:
		elements.TYPES[Tinc.TYPE] = Tinc
	else:
		print "Warning: Tinc not supported for tinc version %s, disabled" % tincVersion