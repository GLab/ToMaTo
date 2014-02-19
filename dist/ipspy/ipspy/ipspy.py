#!/usr/bin/env python

import pcap, sys, time, json, socket, optparse

def getSrcIp(pkt):
	for offset in [12, 16, 20, 24]:
		if pkt[offset:offset+2] == "\x08\x00": #IPv4
			return socket.inet_ntop(socket.AF_INET, pkt[offset+2+12:offset+2+16])
		elif pkt[offset:offset+2] == "\x86\xdd": #IPv6
			return socket.inet_ntop(socket.AF_INET6, pkt[offset+2+8:offset+2+24])

class Stats:
	def __init__(self):
		self.data = {}
	def seenIp(self, ip):
		if not ip: return
		if ip in self.data:
			self.data[ip].seen()
		else:
			self.data[ip] = Entry(ip)
	def printTo(self, outfile):
		with open(outfile, "w") as fp:
			json.dump(dict([(key, {"pkg_count": value.count, "first_seen": value.first, "last_seen": value.last}) for key, value in self.data.items()]), fp, indent=2)

class Entry:
	def __init__(self, ip):
		self.ip = ip
		self.first = time.time()
		self.last = time.time()
		self.count = 1
	def seen(self):
		self.last = time.time()
		self.count += 1


if __name__ == "__main__":
	parser = optparse.OptionParser()
	parser.add_option("-i", "--interface", dest="interface", help="interface to capture on")
	parser.add_option("-o", "--output", dest="output", help="output file to write to")
	parser.add_option("--direction", dest="direction", type="choice", help="outbound or inbound", choices=["inbound", "outbound", "both"], default="inbound")
	parser.add_option("--pause", dest="pause", type=float, help="pause between handling packets in seconds", default=0.1)
	parser.add_option("--interval", dest="interval", type=float, help="pause between writing stats to output file", default=1.0)
	(options, args) = parser.parse_args()
	if not options.interface or not options.output:
		parser.error("interface and output must be given")
	
	pc = pcap.pcap(options.interface, snaplen=64)
	if options.direction == "both":
		pc.setfilter('ip or ip6')
	else:
		pc.setfilter('%s and (ip or ip6)' % options.direction)
	stats = Stats()
	lastPrint = time.time()
	for ts, pkt in pc:
		ip = getSrcIp(pkt)
		time.sleep(options.pause)
		stats.seenIp(ip)
		if time.time() - lastPrint > options.interval:
			lastPrint = time.time()
			stats.printTo(options.output)