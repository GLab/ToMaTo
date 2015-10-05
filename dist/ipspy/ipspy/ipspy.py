#!/usr/bin/env python

import pcap, sys, time, json, socket, optparse, os

def getSrcIp(pkt):
	offset = 12
	while pkt[offset:offset+2] == "\x81\x00": #support vlans
		offset += 4
	if pkt[offset:offset+2] == "\x08\x00": #IPv4
		return socket.inet_ntop(socket.AF_INET, pkt[offset+2+12:offset+2+16])
	elif pkt[offset:offset+2] == "\x86\xdd": #IPv6
		return socket.inet_ntop(socket.AF_INET6, pkt[offset+2+8:offset+2+24])

def getDhcpAddress(pkt):
	offset = 12
	while pkt[offset:offset+2] == "\x81\x00": #support vlans
		offset += 4
	if not pkt[offset:offset+2] == "\x08\x00": return #not IPv4
	offset += 2 #start of IP header
	if not pkt[offset+9] == "\x11": return #not UDP
	offset += (ord(pkt[offset]) % 16) * 4 #start of UDP header
	if not pkt[offset:offset+4] == "\x00\x44\x00\x43": return #not Bootp
	offset += 8 #start of dhcp header
	if not pkt[offset] == "\x01": return #not Bootp request
	if not pkt[offset+236:offset+240] == "\x63\x82\x53\x63": return #not DHCP
	offset += 240 #start of dhcp options
	while offset+1 < len(pkt) and pkt[offset] != "\xff": #end of dhcp options
		if pkt[offset] == "\x32": #requested address
			return socket.inet_ntop(socket.AF_INET, pkt[offset+2:offset+2+ord(pkt[offset+1])])
		if pkt[offset] == "\x35" and not pkt[offset+2] == "\x03": #message type is not DHCP request after an offer
			return
		offset += 2 + ord(pkt[offset+1]) #go to next option

class Stats:
	def __init__(self):
		self.data = {}
	def seenIp(self, ip, ts):
		if not ip: return
		if ip in self.data:
			self.data[ip].seen(ts)
		else:
			self.data[ip] = Entry(ip, ts)
	def timeout(self, timeout):
		bar = time.time() - timeout
		remove = []
		for ip, data in self.data.items():
			if data.last < bar:
				remove.append(ip)
		for ip in remove:
			del self.data[ip]
	def printTo(self, outfile):
		with open(outfile+".tmp", "w") as fp:
			json.dump(dict([(key, {"pkg_count": value.count, "first_seen": value.first, "last_seen": value.last}) for key, value in self.data.items()]), fp, indent=2)
		os.rename(outfile+".tmp", outfile)

class Entry:
	def __init__(self, ip, ts):
		print ip
		self.ip = ip
		self.first = ts
		self.last = ts
		self.count = 1
	def seen(self, ts):
		self.last = ts
		self.count += 1


if __name__ == "__main__":
	parser = optparse.OptionParser()
	parser.add_option("-i", "--interface", dest="interface", help="interface to capture on")
	parser.add_option("-o", "--output", dest="output", help="output file to write to")
	parser.add_option("--direction", dest="direction", type="choice", help="outbound or inbound", choices=["inbound", "outbound", "both"], default="inbound")
	parser.add_option("--pause", dest="pause", type=float, help="pause between handling packets in seconds", default=0.1)
	parser.add_option("--interval", dest="interval", type=float, help="pause between writing stats to output file", default=1.0)
	parser.add_option("--timeout", dest="timeout", type=float, help="timeout for seen addresses", default=24*3600.0)
	parser.add_option("--dhcp", dest="dhcp", action="store_true", help="also try to detect addresses assigned via dhcp")
	(options, args) = parser.parse_args()
	if not options.interface or not options.output:
		parser.error("interface and output must be given")
	
	pc = pcap.pcap(options.interface, snaplen=576) #maximum DHCP length
	if options.direction == "both":
		pc.setfilter('ip or ip6')
	else:
		pc.setfilter('%s and (ip or ip6)' % options.direction)
		
	stats = Stats()
	stats.printTo(options.output)
	lastPrint = 0.0
	for ts, pkt in pc:
		try:
			ip = getSrcIp(pkt)
			if not ip in ["0.0.0.0", "::"]: #neutral source addresses
				stats.seenIp(ip, ts)
			if options.dhcp:
				ip = getDhcpAddress(pkt)
				if ip:
					stats.seenIp("dhcp,"+ip, ts)
		except Exception, exc:
			print >>sys.stderr, "Failed to parse packet: %s" % exc
		if time.time() - lastPrint > options.interval:
			stats.timeout(options.timeout)
			stats.printTo(options.output)
			lastPrint = time.time()
		time.sleep(options.pause)
