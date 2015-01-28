dumps = None
loads = None
dump = None
load = None

import json as _json
orig = _json
try:
	import simplejson as _json
except ImportError:
	pass
#try:
#	import cjson as _json
#except ImportError:
#	pass
try:
	import ujson as _json
except ImportError:
	pass

dumps = dumps or _json.dumps
loads = loads or _json.loads
dump = dump or _json.dump
load = load or _json.load

if __name__ == "__main__":
	print _json.__name__