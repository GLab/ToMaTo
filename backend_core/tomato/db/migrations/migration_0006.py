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
	hosts = ListField(StringField())
	icon = StringField()

class Profile(Document):
	tech = StringField(required=True)
	name = StringField(required=True, unique_with='tech')
	preference = IntField(default=0, required=True)
	label = StringField()
	description = StringField()
	restricted = BooleanField(default=False)
	ram = IntField(min_value=0)
	cpus = FloatField(min_value=0)
	diskspace = IntField(min_value=0)


def _mig_resource(obj):
	if obj.tech == "openvz":
		obj.tech = "container"
		obj.save()
	elif obj.tech == "kvmqm":
		obj.tech = "full"
		obj.save()

def migrate():
	for t in Template.objects():
		_mig_resource(t)
	for p in Profile.objects():
		_mig_resource(p)
	#fixme: migrate elements