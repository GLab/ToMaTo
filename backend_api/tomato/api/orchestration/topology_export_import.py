from ..topology import topology_create, topology_modify, topology_remove, topology_info
from ..elements import element_create, element_modify
from ..connections import connection_create, connection_modify
from ...lib.error import UserError

def topology_import(data):
	# this function may change the values of data.
	UserError.check('file_information' in data, code=UserError.INVALID_VALUE, message="Data lacks field file_information")
	info = data['file_information']
	UserError.check('version' in info, code=UserError.INVALID_VALUE, message="File information lacks field version")
	version = info['version']

	if version == 3:
		UserError.check('topology' in data, code=UserError.INVALID_VALUE, message="Data lacks field topology")
		return _topology_import_v3(data["topology"])
	elif version == 4:
		UserError.check('topology' in data, code=UserError.INVALID_VALUE, message="Data lacks field topology")
		return _topology_import_v4(data['topology'])
	else:
		raise UserError(code=UserError.INVALID_VALUE, message="Unsupported topology version", data={"version": version})

def _topology_import_v3(top):
	# changes in data model from 3 to 4:
	# everything which was in the 'attrs' subdict is now directly in the root.
	# this is for the topology, all elements, and all connections.
	# thus, v3 topology data can easily be transformed to v4 data, and then the v4 data can be imported:

	for key, value in top['attrs'].iteritems():
		top[key] = value
	del top['attrs']
	for el in top['elements']:
		for key, value in el['attrs'].iteritems():
			el[key] = value
		del el['attrs']
	for conn in top['connections']:
		for key, value in conn['attrs'].iteritems():
			conn[key] = value
		del conn['attrs']

	return _topology_import_v4(top)

def _topology_import_v4(top):
	#this uses api stuff, so authorization is checked.
	top_id = None
	elementIds = {}
	connectionIds = {}
	errors = []

	# step 0: create new topology
	top_id = topology_create()['id']

	try:
		# step 1: apply all topology attributes
		attributes = {key: value for key, value in top.iteritems() if key != "elements" and key != "connections"}
		try:
			topology_modify(top_id, attributes)
		except:
			for key, value in attributes.iteritems():
				try:
					topology_modify(top_id, {key: value})
				except Exception, ex:
					errors.append(("topology", None, key, value, str(ex)))

		# step 2: create elements
		elements = [e for e in top["elements"]]
		maxRepeats = len(elements) * len(elements)  # assume: one element added per round. takes less than n^2 steps
		while len(elements) > 0 and maxRepeats > 0:
			maxRepeats -= 1
			el = elements.pop(0)
			if el['parent'] is None or el['parent'] in elementIds:  # the parent of this element exists (or there is no parent needed)

				parentId = elementIds.get(el.get('parent'))
				elId = element_create(top_id, el['type'], parent=parentId)['id']
				elementIds[el['id']] = elId
				attributes = {key: value for key, value in el.iteritems() if key != "parent" and key != "id" and key != "type"}
				try:
					element_modify(elId, attributes)
				except:
					for key, value in attributes.iteritems():
						try:
							element_modify(elId, {key: value})
						except Exception, ex:
							errors.append(("element", el['id'], key, value, str(ex)))

			else:  # append at the end of the list if parent isn't there yet
				elements.append(el)
		if len(elements) > 0:  # there are elements left where the parent has never been created
			for el in elements:
				errors.append(("element", el['id'], 'parent', el['parent'], "parent cannot be created."))

		for con in top["connections"]:
			el1 = elementIds.get(con["elements"][0])
			el2 = elementIds.get(con["elements"][1])
			conId = connection_create(el1, el2)['id']
			connectionIds[con['id']] = conId
			attributes = {key: value for key, value in con.iteritems() if key != "elements" and key != "id"}
			try:
				connection_modify(conId, attributes)
			except:
				for key, value in attributes.iteritems():
					try:
						connection_modify(conId, {key: value})
					except Exception, ex:
						errors.append(("connection", con['id'], key, value, str(ex)))
	except:
		topology_remove(top_id)
		raise
	return top_id, elementIds.items(), connectionIds.items(), errors


def topology_export(id): #@ReservedAssignment
	def reduceData(data):
		def reduceData_rec(data, blacklist):
			if isinstance(data, list):
				return [reduceData_rec(el, blacklist) for el in data]
			if isinstance(data, dict):
				return dict(filter(lambda (k, v): k not in blacklist, [(k, reduceData_rec(v, blacklist)) for k, v in data.iteritems()]))
			return data

		del data['id']
		del data['permissions']

		blacklist = ['usage', 'debug', 'bridge', 'capture_port', 'websocket_pid', 'vmid', 'vncpid',
					 'host', 'websocket_port', 'vncport', 'peers', 'pubkey', 'path', 'port',
					 'host_fileserver_port', 'capture_pid', 'topology', 'state', 'vncpassword',
					 'host_info', 'custom_template', 'timeout',
					 'ipspy_pid', 'last_sync',
					 'rextfv_supported', 'rextfv_status', 'rextfv_max_size', 'info_last_sync',
					 'diskspace', 'ram', 'cpus', 'restricted', 'state_max',
						'_debug_mode', '_initialized']
		blacklist_elements = ['children', 'connection']
		blacklist_connections = ['type']
		data = reduceData_rec(data, blacklist)
		data['elements'] = reduceData_rec(data['elements'], blacklist_elements)
		data['connections'] = reduceData_rec(data['connections'], blacklist_connections)
		return data

	#topology_info will handle authorization check
	top_full = topology_info(id, True)
	top = reduceData(top_full)
	return {'file_information': {'version': 4}, 'topology': top}