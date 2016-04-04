from ..db import *
import fetching

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