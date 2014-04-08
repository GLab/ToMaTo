# coding=utf-8

def tcpPortOpen(host, port):
    from socket import socket, AF_INET, SOCK_STREAM
    s = socket(AF_INET, SOCK_STREAM)
    result = s.connect_ex((host, port))
    s.close()
    return not result

def download(url, file):
    import urllib
    urllib.urlretrieve(url, file)
    
def upload(url, file, name="upload"):
    import httplib, urlparse, os
    parts = urlparse.urlparse(url)
    conn = httplib.HTTPConnection(parts.netloc)
    req = parts.path
    if parts.query:
        req += "?" + parts.query
    conn.putrequest("POST",req)
    filename = os.path.basename(file)
    filesize = os.path.getsize(file)
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    prepend = "--" + BOUNDARY + CRLF + 'Content-Disposition: form-data; name="%s"; filename="%s"' % (name, filename) + CRLF + "Content-Type: application/data" + CRLF + CRLF 
    append = CRLF + "--" + BOUNDARY + "--" + CRLF + CRLF 
    conn.putheader("Content-Length", len(prepend) + filesize + len(append))
    conn.putheader("Content-Type", 'multipart/form-data; boundary=%s' % BOUNDARY)
    conn.endheaders()
    conn.send(prepend)
    fd = open(file, "r")
    data = fd.read(8192)
    while data:
        conn.send(data)
        data = fd.read(8192)
    fd.close()
    conn.send(append)
    resps = conn.getresponse()
    data = resps.read()
    
def testCase(name, topologyName=None):
	def wrap(method):
		def call(automated=False, *args, **kwargs):
			import time
			topId = None
			print "=" * 50
			print "Test case: %s" % name
			print "-" * 50
			success = False
			start = time.time()
			try:
				print "Creating topology..."
				topInfo = topology_create()
				topId = topInfo["id"]
				print "Topology ID: %d" % topId
				topology_modify(topId, {"name": topologyName or "Test: %s" % name})
				method(topId, *args, **kwargs)
				success = True
			except:
				print "-" * 50
				import traceback
				traceback.print_exc()
				if not automated:
					raw_input("Press enter to remove topology")
			finally:
				if topId:
					print "Destroying topology..."
					topology_action(topId, "destroy")
					print "Removing topology..."
					topology_remove(topId)
					print "Done"
			print "-" * 50
			print "Test succeeded" if success else "TEST FAILED", "duration: %.1f sec" % (time.time() - start)
			print "=" * 50
			return success
		return call
	return wrap

def testSuite(tests, automated=False):
	import time
	failed = 0
	start = time.time()
	for test in tests:
		result = test(automated=automated)
		failed += int(not result)
		print
	print "*" * 50
	print "Tests complete, %d of %d tests failed, total duration: %.1f sec" % (failed, len(tests), time.time() - start)
	print "*" * 50
	
def createStarTopology(topId, nodeCount=3, nodeType="openvz", prepare=False, start=False):
	print "Creating star topology of %d nodes of type %s..." % (nodeCount, nodeType)
	switch = element_create(topId, "tinc_vpn")
	switch_ports = []
	nodes = []
	ifaces = []
	connections = []
	for _ in xrange(0, nodeCount):
		node = element_create(topId, nodeType)
		nodes.append(node)
		iface = element_create(topId, "%s_interface" % nodeType, node["id"])
		ifaces.append(iface)
		switch_port = element_create(topId, "tinc_endpoint", switch["id"])
		switch_ports.append(switch_port)
		con = connection_create(iface["id"], switch_port["id"])
		connections.append(con)
	if prepare:
		topology_action(topId, "prepare")
	if start:
		topology_action(topId, "start")
	return nodes, ifaces, switch, switch_ports, connections

def isSuperset(obj1, obj2, path=""):
	#checks whether obj1 is a superset of obj2
	if obj2 is None:
		return (True, None)
	if isinstance(obj1, dict):
		if not isinstance(obj2, dict):
			return (False, "Type mismatch: %s, is dict instead of %s" % (path, type(obj2)))
		for key in obj2:
			if not key in obj1:
				return (False, "Key %s missing: %s" % (key, path))
			(res, msg) = is_superset(obj1[key], obj2[key], path+"."+key)
			if not res:
				return (False, msg)
	elif isinstance(obj1, list):
		if not isinstance(obj2, list):
			return (False, "Type mismatch: %s, is list instead of %s" % (path, type(obj2)))
		for el in obj2:
			if not el in obj1:
				return (False, "Element %s missing: %s" % (el, path))
	else:
		return (obj1 == obj2, "Value mismatch: %s, is %s instead of %s" % (path, repr(obj1), repr(obj2)))
	return (True, None)

def checkSuperset(obj1, obj2):
	res, error = isSuperset(obj1, obj2)
	assert res, error
	
unicodeStrings = {
	"russian": u"По оживлённым берегам",
	"ancient_greek": u"Ἰοὺ ἰού· τὰ πάντʼ ἂν ἐξήκοι σαφῆ.",
	"sanskrit": u"पशुपतिरपि तान्यहानि कृच्छ्राद्",
	"chinese": u"子曰：「學而時習之，不亦說乎？有朋自遠方來，不亦樂乎？",
	"tamil": u"ஸ்றீனிவாஸ ராமானுஜன் ஐயங்கார்",
	"arabic": u"بِسْمِ ٱللّٰهِ ٱلرَّحْمـَبنِ ٱلرَّحِيمِ"
}
unicodeTestString = "".join(unicodeStrings.values())