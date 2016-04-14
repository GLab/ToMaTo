from ..db import *
from .errordump import ErrorDump
import threading
from ..lib.error import UserError
from ..lib.exceptionhandling import wrap_and_handle_current_exception
from ..lib.service import get_backend_users_proxy
from ..lib.userflags import Flags
from ..lib import util

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
		with self.lock:
			if username not in self.users_favorite:
				# fixme: regularly remove non-existent users
				self.users_favorite.append(username)

	def remove_favorite_user(self, username):
		with self.lock:
			if username in self.users_favorite:
				self.users_favorite.remove(username)

	def modify(self, attrs):
		with self.lock:
			for k, v in attrs.iteritems():
				if k == "description":
					self.description = v
				elif k.startswith("_"):
					self.clientData[k[1:]] = v
				else:
					raise UserError(code=UserError.UNSUPPORTED_ATTRIBUTE,
												message="Unsupported attribute for error group", data={'key': k, 'value': v})

	def shrink(self):
		with self.lock:
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

	def info(self, as_user=None):
		with self.lock:
			res = {
				'group_id': self.groupId,
				'description': self.description,
				'count': self.removedDumps,
				'last_timestamp': 0,
				'dump_contents': {}
			}

			select_unique_values = ['softwareVersion', 'source', 'type', 'description']
			for val in select_unique_values:
				res['dump_contents'][val] = []

			res['count'] += len(self.dumps)
			for dump in self.dumps:
				if dump.timestamp > res['last_timestamp']:
					res['last_timestamp'] = dump.timestamp
				for val in select_unique_values:
					if not dump[val] in res['dump_contents'][val]:
						res['dump_contents'][val].append(getattr(dump, val))

			for k, v in self.clientData.iteritems():
				res['_'+k] = v

			if as_user is not None:
				res['user_favorite'] = (as_user in self.users_favorite)

			return res

	def get_dumps(self, source_filter=None):
		"""
		:rtype: list(ErrorDump)
		"""
		with self.lock:
			return [d for d in self.dumps if ((source_filter is None) or (d.source == source_filter))]

	def get_dump(self, dump_id, source_name):
		"""
		:rtype: ErrorDump
		"""
		with self.lock:
			for d in self.dumps:
				if d.dumpId == dump_id and d.source == source_name:
					return d
			raise UserError(UserError.ENTITY_DOES_NOT_EXIST, message="no such dump", data={"group_id": self.groupId, "dump_id": dump_id, "source_name": source_name})

	def hide(self):
		with self.lock:
			self.hidden = True

	def insert_dump(self, dump_obj):
		with self.lock:
			for d in self.dumps:
				if d.dumpId == dump_obj.dumpId and d.source == dump_obj.source:
					return None  # this dump is already in this group.
			self.hidden = False
			self.dumps.append(dump_obj)
			return dump_obj

	def remove(self):
		with ErrorGroup.GROUP_LIST_LOCK:
			with self.lock:
				if self.id:
					self.delete()

	@staticmethod
	def create(group_id, dump_source_name, description=None):
		with ErrorGroup.GROUP_LIST_LOCK:
			desc = description or group_id
			if isinstance(desc, dict):
				if "message" in desc:
					desc = desc["message"]
				elif "subject" in desc:
					desc = desc["subject"]
			if not isinstance(desc, str):
				desc = str(desc)
			if len(desc) > 100:
				desc = desc[:100] + "..."
			if not desc:
				desc = group_id
			grp = ErrorGroup(groupId=group_id, description=desc)

			try:
				get_backend_users_proxy().broadcast_message(
					title="[ToMaTo Devs] New Error Group",  # fixme: this message should be configurable
					message="\n\n".join((
						"A new group of error has been found.",
						"Description: %s",
						"It has first been observed on %s.")) % (
										grp.description, dump_source_name),
					ref=["errorgroup", grp.groupId],
					subject_group="new_errorgroup",
					flag_filter=Flags.ErrorNotify
				)
			except:
				wrap_and_handle_current_exception(re_raise=False)

			return grp

def get_group(group_id, create_if_notexists=False, description=None, dump_source_name=None):
	"""
	get the group with the given ID
	:param str group_id: group_id of target group
	:param bool create_if_notexists: if True, create the group if it doesn't exist.
	:param str description: if create_if_notexists, this is used as description if the group has to be created.
	:param str dump_source_name: if create_if_notexists, this is used as the dump source name for notifying admins.
	:return: ErrorGroup, or None if it doesn't exist
	:rtype :ErrorGroup or None
	"""
	with ErrorGroup.GROUP_LIST_LOCK:
		try:
			return ErrorGroup.objects.get(groupId=group_id)
		except ErrorGroup.DoesNotExist:
			if create_if_notexists:
				return ErrorGroup.create(group_id=group_id, description=description, dump_source_name=dump_source_name)
			else:
				return None
