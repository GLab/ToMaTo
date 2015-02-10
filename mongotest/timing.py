import time

import tomato, tomato.models
tomato.setCurrentUser(True)

import main

def stopOnce(method):
	now = time.time()
	method()
	return time.time()-now

def stopMulti(method, n=100):
	times = []
	stopOnce(method)
	for _ in range(n):
		times.append(stopOnce(method))
	return sum(times)/len(times)

def topInfo(self, full=False):
	if full:
		elements = [el.info() for el in self.elements]
		connections = [con.info() for con in self.connections]
	else:
		elements = [el.id for el in self.elements.only('id')]
		connections = [con.id for con in self.connections.only('id')]
	has_prepared=self.elements(state='prepared').count() > 0
	has_started=self.elements(state='started').count() > 0
	usage = self.totalUsage.by5minutes[-1]
	attrs = {'name': self.name}
	attrs['site'] = self.site.name if self.site else None
	return {
		"id": self.id,
		"attrs": attrs,
		"permissions": dict([(str(p.user), p.role) for p in self.permissions]),
		"elements": elements,
		"connections": connections,
		"usage": usage.info() if usage else None,
		"timeout": self.timeout,
		"state_max": "started" if has_started else ('prepared' if has_prepared else 'created')
	}
main.Topology.info = topInfo

def elementInfo(self):
	info = {
		"id": self.id,
		"type": self.__class__.__name__,
		"topology": self.getFieldId('topology'),
		"parent": self.getFieldId('parent') if self.parent else None,
		"state": self.state,
		"attrs": {},
		"children": [ch.id for ch in self.children.only('id')],
		"connection": self.getFieldId('connection') if self.connection else None,
		"debug": {
				"host_elements": [(o.host.name, o.num) for o in self.hostElements],
				"host_connections": [(o.host.name, o.num) for o in self.hostConnections],
		}
	}
	return info
main.Element.info = elementInfo

def connectionInfo(self):
	info = {
		"id": self.id,
		"type": self.__class__.__name__,
		"state": self.state,
		"attrs": {},
		"elements": [self.getFieldId('elementFrom'), self.getFieldId('elementTo')], #sort elements so that first is from and second is to
		"debug": {
				"host_elements": [(o.host.name, o.num) for o in filter(bool, (self.connectionElementFrom, self.connectionElementTo))],
				"host_connections": [(o.host.name, o.num) for o in filter(bool, (self.connectionFrom, self.connectionTo))],
		}
	}
	h = self.connectionFrom.host if self.connectionFrom else None
	info["attrs"]["host"] = h.name if h else None
	info["attrs"]["host_info"] = {
		'address': h.address if h else None,
		'problems': h.problems() if h else None,
		'site': h.site.name if h else None,
		'fileserver_port': h.hostInfo.get('fileserver_port', None) if h else None
	}
	return info
main.Connection.info = connectionInfo

def usageRecordInfo(self):
	return {
		"begin": self.begin,
		"end": self.end,
		"measurements": self.measurements,
		"usage": self.usage.info()
	}
main.UsageRecord.info = usageRecordInfo

def usageInfo(self):
	return {
		"cputime": self.cputime,
		"diskspace": self.diskspace,
		"memory": self.memory,
		"traffic": self.traffic
	}
main.Usage.info = usageInfo

def usageStatisticsInfo(self):
	stats = {
		"5minutes": [rec.info() for rec in self.by5minutes],
		"hour": [rec.info() for rec in self.byHour],
		"day": [rec.info() for rec in self.byDay],
		"month": [rec.info() for rec in self.byMonth],
		"year": [rec.info() for rec in self.byYear],
	}
	return stats
main.UsageStatistics.info = usageStatisticsInfo


def doPostgres():
	print "Topology #171 info(full=True): %f" % stopMulti(lambda :tomato.models.Topology.objects.get(id=171).info(full=True))
	print "Topology #171 info(): %f" % stopMulti(lambda :tomato.models.Topology.objects.get(id=171).info())
	print "Topology #171 totalUsage.info(): %f" % stopMulti(lambda :tomato.models.Topology.objects.get(id=171).totalUsage.info())
	print "Topology list: %f" % stopMulti(lambda :[t.info() for t in tomato.models.Topology.objects.all()])

def doMongodb():
	print "Topology #171 info(full=True): %f" % stopMulti(lambda :main.Topology.objects(name='Huge Topology')[0].info(full=True))
	print "Topology #171 info(): %f" % stopMulti(lambda :main.Topology.objects(name='Huge Topology')[0].info())
	print "Topology #171 totalUsage.info(): %f" % stopMulti(lambda :main.Topology.objects(name='Huge Topology')[0].totalUsage.info())
	print "Topology list: %f" % stopMulti(lambda :[t.info() for t in main.Topology.objects])

if __name__ == "__main__":
	doPostgres()
	doMongodb()