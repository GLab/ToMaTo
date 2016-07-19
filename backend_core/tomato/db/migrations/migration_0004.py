from mongoengine import *
import string, random, crypt, time
from mongoengine.errors import NotUniqueError

class Template(Document):
	tech = StringField(required=True)
	name = StringField(required=True, unique_with='tech')
	popularity = FloatField(default=0)
	preference = IntField(default=0)
	urls = ListField()
	host_urls = ListField()
	checksum = StringField()
	size = IntField()
	label = StringField()
	description = StringField()
	restricted = BooleanField(default=False)
	subtype = StringField()
	kblang = StringField(default='en-us')
	nlXTPInstalled = BooleanField(db_field='nlxtp_installed')
	showAsCommon = BooleanField(db_field='show_as_common')
	creationDate = FloatField(db_field='creation_date', required=False)
	hosts = ListField(DynamicField())
	icon = StringField()


def migrate():
	for t in Template.objects():
		t.hosts = []
		t.save()