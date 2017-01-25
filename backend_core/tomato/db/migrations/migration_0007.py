from mongoengine import *



# resources

class Template(Document):
	meta = {"auto_indexes": False}
	type = StringField(required=False)
	tech = StringField(required=False)
	name = StringField(required=True)
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
	meta = {"auto_indexes": False}
	type = StringField(required=False)
	tech = StringField(required=False)
	name = StringField(required=True)
	preference = IntField(default=0, required=True)
	label = StringField()
	description = StringField()
	restricted = BooleanField(default=False)
	ram = IntField(min_value=0)
	cpus = FloatField(min_value=0)
	diskspace = IntField(min_value=0)


def _mig_resource(obj):
	"""
	migrates a template or profile
	:param obj:
	:return:
	"""
	if obj.tech:
		obj.type = obj.tech
		obj.tech = None
		obj.save()

def migrate_resources():
	Template._get_collection().drop_indexes()
	Profile._get_collection().drop_indexes()
	for t in Template.objects():
		_mig_resource(t)
	for p in Profile.objects():
		_mig_resource(p)

def migrate():
	migrate_resources()
