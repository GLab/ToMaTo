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

from fcntl import ioctl
import os, struct, socket, random, time
from . import net


def ip_checksum(data):
	if len(data) & 1:
		data = data + "\x00"
	words = struct.unpack("!%dH" % (len(data) / 2), data)
	sum = 0
	for w in words:
		sum += w ^ 0xffff
	while sum >> 16:
		sum = (sum >> 16) + (sum & 0xffff)
	sum ^= 0xffff
	return sum


def ip_to_str(ip):
	return ".".join([str(ord(b)) for b in ip])


def searchServer(ifname, maxWait=2.0):
	if net.bridgeExists(ifname):
		sock = net.BridgeAccess(ifname, "dhcp_probe%d", timeout=maxWait)
	else:
		sock = net.IfaceAccess(ifname, timeout=maxWait)
	with sock:
		mac = "\x02" + os.urandom(5)
		xid = os.urandom(4)
		# dhcp payload
		pkg = "\x01\x01\x06\x00" + xid + "\x00" * 20 + mac + "\x00" * 202 + "\x63\x82\x53\x63\x35\x01\x01\xff\x00"
		# udp header
		pkg = struct.pack("!HHHH", 68, 67, 8 + len(pkg), 0) + pkg
		# ipv4 header
		pkgh = struct.pack("!BBHHHBBH", 0x45, 0, 20 + len(pkg), 0, 0, 64, 17, 0) + "\00" * 4 + "\xff" * 4
		pkg = pkgh[0:10] + struct.pack("!H", ip_checksum(pkgh) ^ 0xffff) + pkgh[12:] + pkg
		# ethernet
		pkg = "\xff" * 6 + mac + "\x08\x00" + pkg
		sock.send(pkg)
		start = time.time()
		while time.time() - start < maxWait:
			pkg = sock.receive(1518)
			if not pkg:
				continue
			if not pkg[:6] == mac or not pkg[12:14] == "\x08\x00":
				continue  # not for me or not an ip packet
			pkg = pkg[14:]  # ip packet
			vihl, _, _, _, _, _, proto, _ = struct.unpack("!BBHHHBBH", pkg[0:12])
			version = vihl >> 4
			if not version == 4 or not proto == 17:
				continue  # not ipv4 or not udp
			ihl = vihl & 0x0f
			pkg = pkg[ihl * 4:]
			src, dst, length, _ = struct.unpack("!HHHH", pkg[0:8])
			if not src == 67 or not dst == 68:
				continue  # not a dhcp reply
			pkg = pkg[8:]
			op, htype, hlen = struct.unpack("!3B", pkg[0:3])
			xid2 = pkg[4:8]
			if not op == 2 or not htype == 1 or not hlen == 6 or not xid2 == xid:
				continue  # not a proper reply
			if not pkg[236:240] == "\x63\x82\x53\x63":
				continue  # no DHCP extension
			reply = {"ip": ip_to_str(pkg[16:20]),
			"next_server": ip_to_str(pkg[20:24]),
			"gateway": ip_to_str(pkg[24:28])}
			pkg = pkg[240:]
			options = {}
			pos = 0
			while pos < len(pkg):
				t = ord(pkg[pos])
				if t == 0x0ff:
					break
				l = ord(pkg[pos + 1])
				v = pkg[pos + 2:pos + 2 + l]
				pos += 2 + l
				options[t] = v
			if not 53 in options or not options[53] == "\x02":
				continue  # not a DHCP reply
			for t, v in options.iteritems():
				if t == 1:
					reply["subnet_mask"] = ip_to_str(v)
				elif t == 3:
					reply["gateway"] = ip_to_str(v)
				elif t == 6:
					reply["dns_servers"] = [ip_to_str(v[x:x + 4]) for x in range(0, len(v), 4)]
				elif t == 12:
					reply["hostname"] = v.strip("\x00")
				elif t == 15:
					reply["domainname"] = v.strip("\x00")
				elif t == 19:
					reply["ip_forward"] = bool(len(v) and v[0])
				elif t == 28:
					reply["broadcast"] = ip_to_str(v)
				elif t == 42:
					reply["ntp_servers"] = [ip_to_str(v[x:x + 4]) for x in range(0, len(v), 4)]
				elif t == 51:
					reply["lease_time"] = struct.unpack("!I", v)[0]
				elif t == 54:
					reply["server"] = ip_to_str(v)
				elif t == 58:
					reply["renewal_time"] = struct.unpack("!I", v)[0]
				elif t == 59:
					reply["rebind_time"] = struct.unpack("!I", v)[0]
				elif t == 53:
					pass
				else:
					reply["unknown_option_%d" % t] = v.encode("hex")
			return reply
		return None


if __name__ == "__main__":
	import sys
	print searchServer(sys.argv[1])