
def link_info(id, ip, samples=10, maxWait=5, oneWayAdapt=False):
	"""
	Pings a target IP address from a certain device and returns the results.
	The number of samples and the maximum wait time for responds can be set.
	Also a one-way adaption of the results is possible. 


	Parameter *id*:
		ID of device which should be used.
		
	Parameter *ip*:
		IP address of the ping target.

	Parameter *samples*:
		Number of messages to send.
		
	Parameter *maxWait*:
		Time to wait for a responds in seconds.
		
	Parameter *oneWayAdapt*:
		Change results to a one-way adaption.
		
	Return value:
	  The return value of this method is a dict containing information
	  about the route between the link and the destination. 

	``lossratio``
	  The loss ratio of the route between the link and the destination.
	  
	``delay``
	  The average round-trip time.
	  
	``delay_stddev``
	  The average standard deviation for the delay.	
	"""
	
	res = element_action(id, "execute", {"cmd": "ping -A -c %d -n -q -w %d %s; true" % (samples, maxWait, ip)})
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
	
def link_check(id, ip, tries=5, waitBetween=5):
	"""
	Checks the availability of a link by trying to reach him a certain number of tries. 

		
	Parameter *id*:
		ID of device which should be reached
		
	Parameter *ip*:
		IP address of the ping target

	Parameter *tries*:
		Number of tries

	Parameter *waitBetween*:
		Time between each try
		
	Return value:
	  Returns a boolean which is true, if the link was available within the number of tries, false otherwise.
	
	"""
	import time
	while tries>0 and not link_info(id,ip):
		tries -= 1
		time.sleep(waitBetween)
	return tries > 0
	
def link_config(top, con, c, attrs):
	"""
	Configures an link by modifying the certain attributes
	
	Parameter *top*:
		Topology in which the link can be found
		
	Parameter *con*:
		Link which should be modified
		
	Parameter *c*:
		Target interface
		
	Parameter *attrs*:
		Key value pair of attributes which should be configured 
	"""
	top_modify(top, [{"type": "connection-configure", "element": con, "subelement": c, "properties": attrs}], True)	

def is_superset(obj1, obj2, path=""):
	"""
	Checks whether obj1 is a superset of obj2.

	Parameter *obj1*:
		Superset object
	
	Parameter *obj2*:
		Subset object
		
	Parameter *path*:
		Should be "" in initial call
	
	Return value:
	  Returns a tuple with 2 arguments. The first argument is a boolean which is true, if obj1 is superset of obj2, false otherwise.
	  The second argument returns a string if the first argument is false. The string contains the reason why obj1 is not a superset of obj2. 
	
	"""
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
