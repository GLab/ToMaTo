from ..db import *
import fetching
import time

class ErrorDump(EmbeddedDocument):
	source = StringField(required=True)
	dumpId = StringField(db_field='dump_id', required=True)  # not unique, different semantics on embedded documents
	description = DictField(required=True)
	data = DictField()
	type = StringField(required=True)
	softwareVersion = DictField(db_field='software_version')
	timestamp = FloatField(required=True)
	meta = {
		'ordering': ['+timestamp'],
	}

	def getSource(self):
		return fetching.get_source_by_name(self.source)

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
			dump['data'] = self.data
		return dump

	@staticmethod
	def from_dict(dump_dict, source):
		return ErrorDump(
			source=source.dump_source_name(),
			dumpId=dump_dict.get('dump_id', str(time.time())),
			timestamp=dump_dict.get('timestamp', None),
			description=dump_dict.get('description', None),
			type=dump_dict.get('type', None),
			softwareVersion=dump_dict.get('software_version', None),
			data=dump_dict.get("data", None)
		)
