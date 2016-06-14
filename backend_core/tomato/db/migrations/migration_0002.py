from mongoengine import *
import string, random, crypt, time
from mongoengine.errors import NotUniqueError

class Template(Document):
	tech = StringField(required=True)
	name = StringField(required=True, unique_with='tech')
	preference = IntField(default=0)
	torrentData = StringField(db_field='torrent_data')
	label = StringField()
	description = StringField()
	restricted = BooleanField(default=False)
	subtype = StringField()
	kblang = StringField(default='en-us')
	nlXTPInstalled = BooleanField(db_field='nlxtp_installed')
	showAsCommon = BooleanField(db_field='show_as_common')
	creationDate = FloatField(db_field='creation_date', required=False)
	icon = StringField()
	popularity = FloatField(default=0)
	urls = ListField()
	checksum = StringField()
	size = IntField()


def migrate():
	for templ in Template.objects():
		del templ.torrentData
		templ.save()
