def waitForTask(task, assertSuccess=False):
	import time
	while task_status(task)["status"] == "waiting":
		time.sleep(0.25)
	while task_status(task)["active"]:
		time.sleep(0.25)
	ts = task_status(task)
	assert not assertSuccess or ts["status"] == "succeeded", "Task failed: %s" % ts["name"]
	return ts

def jsonToMods(data):
	import simplejson as json, zlib, base64
	try:
		top = json.loads(data)
	except:
		data = zlib.decompress(base64.b64decode(data))
		top = json.loads(data)
	mods = []
	mods.append({"type": "topology-rename", "element": None, "subelement": None, "properties": {"name": top["attrs"]["name"]}})
	for devname, dev in top["devices"].iteritems():
		mods.append({"type": "device-create", "element": None, "subelement": None, "properties": dev["attrs"]})
		for iface in dev["interfaces"].values():
			mods.append({"type": "interface-create", "element": devname, "subelement": None, "properties": iface["attrs"]})
	for conname, con in top["connectors"].iteritems():
		mods.append({"type": "connector-create", "element": None, "subelement": None, "properties": con["attrs"]})
		for c in con["connections"].values():
			mods.append({"type": "connection-create", "element": conname, "subelement": None, "properties": c["attrs"]})
	return mods

def link_info(top, dev, ip, samples=10, maxWait=5, oneWayAdapt=False):
	res = top_action(top, "execute", "device", dev, attrs={"cmd": "ping -A -c %d -n -q -w %d %s; true" % (samples, maxWait, ip)})
	if not res:
		return
	import re
	spattern = re.compile("(\d+) packets transmitted, (\d+) received(, \+(\d+) errors)?, (\d+)% packet loss, time (\d+)(m?s)")
	dpattern = re.compile("rtt min/avg/max/mdev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+) (m?s)(, pipe \d+)?, ipg/ewma (\d+\.\d+)/(\d+\.\d+) (m?s)")
	summary = False
	details = False
	for line in res.splitlines():
		if spattern.match(line):
			(transmitted, received, dummy, errors, loss, total, unit) = spattern.match(line).groups()
			(transmitted, received, errors, loss, total) = (int(transmitted), int(received), int(errors) if errors else None, float(loss)/100.0, float(total))
			summary = True
		if dpattern.match(line):
			(rttmin, rttavg, rttmax, rttstddev, rttunit, dummy, ipg, ewma, ipg_ewma_unit) = dpattern.match(line).groups()
			(rttmin, avg, rttmax, stddev, ipg, ewma) = (float(rttmin), float(rttavg), float(rttmax), float(rttstddev), float(ipg), float(ewma))
			details = True
	if not summary or not details or errors:
		return
	if oneWayAdapt:
		import math
		loss = 1.0 - math.sqrt(1.0 - loss)
		avg = avg / 2.0
		stddev = stddev / 2.0
	if rttunit == "s":
		avg = avg * 1000.0
		stddev = stddev * 1000.0
	return {"lossratio": loss, "delay": avg, "delay_stddev": stddev}
	
def link_check(top, dev, ip, tries=5, waitBetween=5):
	import time
	while tries>0 and not link_info(top, dev, ip):
		tries -= 1
		time.sleep(waitBetween)
	return tries > 0
	
def link_config(top, con, c, attrs):
	top_modify(top, [{"type": "connection-configure", "element": con, "subelement": c, "properties": attrs}], True)
	
def errors_print():
	for err in errors_all():
		print err["message"] + "\n\n"
		
def download(url, file):
	import urllib
	urllib.urlretrieve(url, file)

def is_superset(obj1, obj2, path=""):
	#checks whether obj1 is a superset of obj2
	if obj2 is None:
		return (True, None)
	if isinstance(obj1, dict):
		if not isinstance(obj2, dict):
			return (False, "Type mismatch: %s" % path)
		for key in obj2:
			if not key in obj1:
				return (False, "Key %s missing: %s" % (key, path))
			(res, msg) = is_superset(obj1[key], obj2[key], path+"."+key)
			if not res:
				return (False, msg)
	elif isinstance(obj1, list):
		if not isinstance(obj2, list):
			return (False, "Type mismatch: %s" % path)
		for el in obj2:
			if not el in obj1:
				return (False, "Element %s missing: %s" % (el, path))
	else:
		return (obj1 == obj2, "Value mismatch: %s" % path)
	return (True, None)
	
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