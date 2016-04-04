import time, zlib, threading, base64
from .db import *
from .lib import anyjson as json

from lib import service

import host
from . import scheduler
from .lib.error import InternalError, UserError, Error, TransportError  # @UnresolvedImport
from .lib.rpc.sslrpc import RPCError
from .lib import util
from .lib.userflags import Flags

from lib.settings import settings, Config

# Zero-th part: database stuff
class ErrorDump(EmbeddedDocument):
	source = StringField(required=True)
	dumpId = StringField(db_field='dump_id', required=True)  # not unique, different semantics on embedded documents
	description = DictField(required=True)
	data = StringField()
	dataAvailable = BooleanField(default=False, db_field='data_available')
	type = StringField(required=True)
	softwareVersion = DictField(db_field='software_version')
	timestamp = FloatField(required=True)
	meta = {
		'ordering': ['+timestamp'],
	}

	def getSource(self):
		return find_source_by_name(self.source)

	def modify_data(self, data, is_compressed=True):
		if data is None:
			self.data = None
			self.dataAvailable = False
			return
		if is_compressed:
			data_toinsert = data
		else:
			data_toinsert = base64.b64encode(zlib.compress(json.dumps(data), 9))
		self.data = data_toinsert
		self.dataAvailable = True

	def fetch_data_from_source(self):
		d = self.getSource().dump_fetch_with_data(self.dumpId, True)
		self.modify_data(d['data'], True)
		get_group(d['group_id']).save()

	def info(self, include_data=False):
		dump = {
			'source': self.source,
			'dump_id': self.dumpId,
			'description': self.description,
			'type': self.type,
			'software_version': self.softwareVersion,
			'timestamp': self.timestamp
		}
		if include_data:
			if not self.dataAvailable:
				self.fetch_data_from_source()
			dump['data'] = json.loads(zlib.decompress(base64.b64decode(self.data)))
		else:
			dump['data_available'] = self.dataAvailable
		return dump


class ErrorGroup(BaseDocument):
	"""
	:type dumps: list of ErrorDump
	"""
	groupId = StringField(db_field='group_id', required=True, unique=True)
	description = StringField(required=True)
	removedDumps = IntField(default=0, db_field='removed_dumps')
	dumps = ListField(EmbeddedDocumentField(ErrorDump))
	hidden = BooleanField(default=False)
	users_favorite = ListField(StringField())
	clientData = DictField(db_field='client_data')
	meta = {
		'collection': 'error_group',
		'ordering': ['groupId'],
		'indexes': [
			'groupId'
		]
	}

	LOCKS = {}
	LOCKS_LOCK = threading.RLock()

	GROUP_LIST_LOCK = threading.RLock()
	"""
	to be used when accessing the list of groups (adding, deleting)
	"""

	@property
	def lock(self):
		key = self.groupId
		with self.LOCKS_LOCK:
			lock = self.LOCKS.get(key)
			if not lock:
				lock = threading.RLock()
				self.LOCKS[key] = lock
			return lock

	def add_favorite_user(self, username):
		if username not in self.users_favorite:
			self.users_favorite.append(username)
			self.save()

	def remove_favorite_user(self, username):
		if username in self.users_favorite:
			self.users_favorite.remove(username)
			self.save()

	def modify(self, attrs):
		for k, v in attrs.iteritems():
			if k == "description":
				self.description = v
			elif k.startswith("_"):
				self.clientData[k[1:]] = v
			else:
				raise UserError(code=UserError.UNSUPPORTED_ATTRIBUTE,
											message="Unsupported attribute for error group", data={'key': k, 'value': v})
		self.save()

	def shrink(self):
		oldLen = len(self.dumps)
		if oldLen <= 10:
			return

		# first and last 5 dumps are kept under any circumstance.
		#            first 5          last 5
		dumps_keep = self.dumps[:5] + self.dumps[-5:]
		# all except first and last 5
		toremove = self.dumps[5:-5]

		tokeep = []  # dumps in toremove, that should be kept
		sources = set()  # sources that have been found in following loop
		versions = []  # versions that have been found in following loop

		for d in dumps_keep + toremove:  # prioritize those that are kept under any circumstance.
			keep = False
			if d.source not in sources:  # this source has not been found in a previous loop cycle
				sources.add(d.source)
				keep = True
			if d.softwareVersion not in versions:  # this version has not been found in a previous loop cycle
				versions.append(d.softwareVersion)
				keep = True
			if keep and (d in toremove):  # source or version haven't been found in previous cycle.
				# Also make sure that tokeep is a subset of toremove
				tokeep.append(d)

		#            first 5                   last 5
		self.dumps = self.dumps[:5] + tokeep + self.dumps[-5:]
		# before:    self.dumps[:5] + toremove + self.dumps[-5:]
		self.removedDumps += oldLen - len(self.dumps)
		self.save()

	def info(self):
		res = {
			'group_id': self.groupId,
			'description': self.description,
			'count': self.removedDumps,
			'last_timestamp': 0,
			'data_available': False,
			'dump_contents': {}
		}

		select_unique_values = ['softwareVersion', 'source', 'type', 'description']
		for val in select_unique_values:
			res['dump_contents'][val] = []

		res['count'] += len(self.dumps)
		for dump in self.dumps:
			if dump.dataAvailable:
				res['data_available'] = True
			if dump.timestamp > res['last_timestamp']:
				res['last_timestamp'] = dump.timestamp
			for val in select_unique_values:
				if not dump[val] in res['dump_contents'][val]:
					res['dump_contents'][val].append(getattr(dump, val))

		for k, v in self.clientData.iteritems():
			res['_'+k] = v

		return res

	def hide(self):
		self.hidden = True
		self.save()

	def insert_dump(self, dump, source):
		dump_obj = ErrorDump(
			source=source.dump_source_name(),
			dumpId=dump['dump_id'],
			timestamp=dump['timestamp'],
			description=dump['description'],
			type=dump['type'],
			softwareVersion=dump['software_version']
		)
		self.hidden = False
		self.dumps.append(dump_obj)
		self.save()
		return dump_obj

	def remove(self):
		if self.id:
			self.delete()


def create_group(group_id, description=None):
	with ErrorGroup.GROUP_LIST_LOCK:
		desc = description or group_id
		if isinstance(desc, dict) and "message" in desc:
			desc = desc["message"]
		if not isinstance(desc, str):
			desc = str(desc)
		if len(desc) > 100:
			desc = desc[:100] + " ..."
		if not desc:
			desc = group_id
		grp = ErrorGroup(groupId=group_id, description=desc)
		grp.save()
		return grp



def get_group(group_id):
	"""
	:rtype :ErrorGroup or None
	"""
	try:
		with ErrorGroup.GROUP_LIST_LOCK:
			return ErrorGroup.objects.get(groupId=group_id)
	except ErrorGroup.DoesNotExist:
		return None


def getAll_group():
	return ErrorGroup.objects.all()


def remove_group(group_id):
	with ErrorGroup.GROUP_LIST_LOCK:
		grp = get_group(group_id)
		if grp is not None:
			grp.remove()
			del ErrorGroup.LOCKS[group_id]
			return True
		return False


def create_dump(dump, source, group_obj):
	return group_obj.insert_dump(dump, source)


# First part: fetching dumps from all the sources.

# this class should not be instantiated. There are two subclasses available: one that can connect to a host, and one that connects to this backend.
class DumpSource(object):
	# dump_last_fetch = None

	# to be implemented in subclass
	# fetches all dumps from the source, which were thrown after *after*.
	# after is a float and will be used unchanged.
	# if this throws an exception, the fetching is assumed to have been unsuccessful.
	def dump_fetch_list(self, after):
		raise NotImplemented()

	def dump_get_last_fetch(self):
		raise NotImplemented()

		# to be implemented in subclass
		# fetches all data about the given dump.
		# if this throws an exception, the fetching is assumed to have been unsuccessful.

	def dump_fetch_with_data(self, dump_id, keep_compressed=True):
		raise NotImplemented()

		# to be implemented in a subclass
		# if the source has its clock before the backend, and an error is thrown in exactly this difference,
		# the dump would be skipped.
		# Thus, use the known clock offset to fetch dumps that might have occurred in this phase (i.e., right after the last fetch)
		# returns a float. should be ==0 if the source's clock is ahead, and >0 if the source's clock is behind

	def dump_clock_offset(self):
		raise NotImplemented()

		# to be implemented in a subclass
		# returns a string to uniquely identify the source

	def dump_source_name(self):
		raise NotImplemented()

		# override for HostDumpSource. Return true if the given host is this one

	def dump_matches_host(self, host_obj):
		raise NotImplemented()

		# override in subclass

	def dump_set_last_fetch(self, last_fetch):
		raise NotImplemented()

	def dump_getUpdates(self):
		offset = self.dump_clock_offset()
		if offset is None:
			return []  # this is due to missing or incomplete host info. Do nothing in this case and wait for next try to fetch
		this_fetch_time = time.time() - offset

		try:
			fetch_results = self.dump_fetch_list(self.dump_get_last_fetch())
			if len(
					fetch_results) > 0:  # if the list is empty, no need to set this. However, if the list is empty for incorrect reasons (i.e., errors),
				# we may still be able to get the dumps when the error is resolved.
				self.dump_set_last_fetch(this_fetch_time)
			return fetch_results
		except Exception as exc:
			to_be_dumped = True
			if isinstance(exc, RPCError):
				if exc.category == RPCError.Category.NETWORK:
					to_be_dumped = False
			if isinstance(exc, Error):
				if exc.type == TransportError.TYPE:
					to_be_dumped = False
			if to_be_dumped:
				InternalError(code=InternalError.UNKNOWN, message="Failed to retrieve dumps: %s" % exc,
								data={"source": repr(self), "exception": repr(exc)}).dump()
			return []


# fetches from this backend
class LocalDumpSource(DumpSource):
	keyvaluestore_key = "dumpmanager:last_%s_fetch" % "backend_core"

	def dump_fetch_list(self, after):
		import dump

		return dump.getAll(after=after, list_only=False, include_data=False, compress_data=True)

	def dump_fetch_with_data(self, dump_id, keep_compressed=True):
		import dump

		dump = dump.get(dump_id, include_data=True, compress_data=True, dump_on_error=False)
		if not keep_compressed:
			dump['data'] = json.loads(zlib.decompress(base64.b64decode(dump['data'])))
		return dump

	def dump_clock_offset(self):
		return 0

	def dump_source_name(self):
		return "backend:backend_core"

	def dump_set_last_fetch(self, last_fetch):
		data.set(self.keyvaluestore_key, last_fetch)

	def dump_get_last_fetch(self):
		return data.get(self.keyvaluestore_key, 0)

class APIDumpSource(DumpSource):

	def __init__(self, component_name, proxy):
		self.keyvaluestore_key = "dumpmanager:last_%s_fetch" % component_name
		self.serverProxy = proxy
		self.component_name = component_name

	def dump_fetch_list(self, after):
		return self.serverProxy.dump_list(after=after, list_only=False, include_data=False, compress_data=True)

	def dump_fetch_with_data(self, dump_id, keep_compressed=True):
		dump = self.serverProxy.dump_info(dump_id, include_data=True, compress_data=True, dump_on_error=False)
		if not keep_compressed:
			dump['data'] = json.loads(zlib.decompress(base64.b64decode(dump['data'])))
		return dump

	def dump_clock_offset(self):
		return 0  # fixme: actually determine this

	def dump_source_name(self):
		return "backend:%s" % self.component_name

	def dump_set_last_fetch(self, last_fetch):
		data.set(self.keyvaluestore_key, last_fetch)

	def dump_get_last_fetch(self):
		return data.get(self.keyvaluestore_key, 0)





def getDumpSources(include_disabled=False):
	sources = []
	for tomato_module in Config.TOMATO_MODULES:
		if include_disabled or settings.get_dumpmanager_enabled(tomato_module):
			if service.is_self(tomato_module):
				sources.append(LocalDumpSource())
			else:
				sources.append(_create_api_dumpsource_for_module(tomato_module))
	hosts = host.Host.getAll()
	for h in hosts:
		if include_disabled or h.enabled:
			sources.append(h)
	return sources


def find_source_by_name(source_name):
	for s in getDumpSources(include_disabled=True):
		if s.dump_source_name() == source_name:
			return s
	return None


def insert_dump(dump, source):
	source_name = source.dump_source_name()
	must_fetch_data = False

	# check whether the group ID already exists. If not, create it,
	# remember to fetch dump data in the end, and email developer users
	with ErrorGroup.GROUP_LIST_LOCK:
		group = get_group(dump['group_id'])
		if not group:
			must_fetch_data = True
			if isinstance(dump['description'], dict):
				if 'subject' in dump['description'] and 'type' in dump['description']:
					group_desc = str(dump['description']['type']) + ': ' + str(dump['description']['subject'])
				else:
					group_desc = str(dump['description'])
			else:
				group_desc = dump['description']
			group = create_group(dump['group_id'], group_desc)
			api = service.get_backend_users_proxy()
			api.broadcast_message(
				title="[ToMaTo Devs] New Error Group",  # fixme: this message should be configurable
				message="\n\n".join((
								"A new group of error has been found.",
								"Description: %s",
								"It has first been observed on %s.")) % (
								group_desc, source.dump_source_name()),
				ref=["errorgroup", dump['group_id']],
				subject_group="new_errorgroup",
				flag_filter=Flags.ErrorNotify
			)

	with group.lock:
		group = group.reload()
		# insert the dump.
		for d in group.dumps:
			if d.dumpId == dump['dump_id'] and d.source == source_name:
				return
		dump_db = create_dump(dump, source, group)

	# if needed, load data
	if must_fetch_data:
		dump_db.fetch_data_from_source()


def update_source(source):
	try:
		new_entries = source.dump_getUpdates()
		for e in new_entries:
			try:
				insert_dump(e, source)
			except:
				try:
					from dump import dumpException
					dumpException()
				except:
					pass  # better than losing all dumps in next for loop iterations...
	finally:
		for group in getAll_group():
			with group.lock:
				group = group.reload()
				group.shrink()

@util.wrap_task
def update_all(async=True):
	for s in getDumpSources():
		if async:
			scheduler.scheduleOnce(0, update_source, s)
		else:
			update_source(s)
	return len(getDumpSources())

@util.wrap_task
def scheduleUpdates():
	toSync = set(getDumpSources())
	syncTasks = {t.args[0]: tid for tid, t in scheduler.tasks.items() if t.fn == update_source}
	syncing = set(syncTasks.keys())
	for s in toSync - syncing:
		scheduler.scheduleRepeated(settings.get_dumpmanager_config()[Config.DUMPMANAGER_COLLECTION_INTERVAL], update_source, s)
	for s in syncing - toSync:
		scheduler.cancelTask(syncTasks[s])

def _create_api_dumpsource_for_module(tomato_module):
	proxy = service.get_tomato_inner_proxy(tomato_module)
	return APIDumpSource(tomato_module, proxy)

def init():
	scheduler.scheduleRepeated(settings.get_dumpmanager_config()[Config.DUMPMANAGER_COLLECTION_INTERVAL], scheduleUpdates, immediate=True)

# Second Part: Access to known dumps for API

def api_errorgroup_list(show_empty=False, as_user=None):
	res = []
	for grp in getAll_group():
		with grp.lock:
			if show_empty or (grp.dumps and (not grp.hidden)):
				info = grp.info()
				if as_user is not None:
					info['user_favorite'] = (as_user in grp.users_favorite)
				res.append(info)
	return res


def api_errorgroup_modify(group_id, attrs):
	grp = get_group(group_id)
	UserError.check(grp is not None, code=UserError.ENTITY_DOES_NOT_EXIST, message="error group does not exist",
					data={"group_id": group_id})
	with grp.lock:
		grp.modify(attrs)
		return grp.info()


def api_errorgroup_info(group_id, include_dumps=False):
	group = get_group(group_id)
	UserError.check(group is not None, code=UserError.ENTITY_DOES_NOT_EXIST, message="error group does not exist",
					data={"group_id": group_id})
	with group.lock:
		group = group.reload()
		res = group.info()
		if include_dumps:
			res['dumps'] = []
			for i in group.dumps:
				res['dumps'].append(i.info())
		return res


def api_errordump_info(group_id, source, dump_id, include_data=False):
	group = get_group(group_id)
	UserError.check(group, code=UserError.ENTITY_DOES_NOT_EXIST, message="error group does not exist",
					data={"group_id": group_id})
	with group.lock:
		group = group.reload()
		dump = None
		for d in group.dumps:
			if d.dumpId == dump_id and d.source == source:
				dump = d
				break
		UserError.check(dump, code=UserError.ENTITY_DOES_NOT_EXIST, message="error dump does not exist",
						data={"dump_id": dump_id, "source": source})
		return dump.info(include_data)


def api_errorgroup_remove(group_id):
	group = get_group(group_id)
	with group.lock:
		res = remove_group(group_id)
		UserError.check(res, code=UserError.ENTITY_DOES_NOT_EXIST, message="error group does not exist",
						data={"group_id": group_id})


def api_errordump_list(group_id, source=None, data_available=None):
	group = get_group(group_id)
	UserError.check(group, code=UserError.ENTITY_DOES_NOT_EXIST, message="error group does not exist",
					data={"group_id": group_id})
	with group.lock:
		group = group.reload()
		res = []
		for d in group.dumps:
			di = d.info(include_data=False)
			append_to_res = True
			if not source is None and di['source'] != source:
				append_to_res = False
			if not data_available is None and di['data_available'] != data_available:
				append_to_res = False
			if append_to_res:
				res.append(di)
		return res

def api_errorgroup_hide(group_id):
	group = get_group(group_id)
	with group.lock:
		group = group.reload()
		group.hide()

def api_force_refresh():
	return update_all(async=False)

def api_errorgroup_favorite(username, group_id, is_favorite):
	group = get_group(group_id)
	if is_favorite:
		group.add_favorite_user(username)
	else:
		group.remove_favorite_user(username)