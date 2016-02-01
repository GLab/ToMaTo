from mongoengine import *
import string, random, crypt, time
from mongoengine.errors import NotUniqueError


class Usage(EmbeddedDocument):
	memory = FloatField(default=0.0) #unit: bytes
	diskspace = FloatField(default=0.0) #unit: bytes
	traffic = FloatField(default=0.0) #unit: bytes
	cputime = FloatField(default=0.0) #unit: cpu seconds


class UsageRecord(EmbeddedDocument):
	begin = FloatField(required=True)
	end = FloatField(required=True)
	measurements = IntField(default=0)
	usage = EmbeddedDocumentField(Usage, required=True)
	meta = {
		'collection': 'usage_record',
		'ordering': ['type', 'end'],
		'indexes': [
			('type', 'end')
		]
	}


class UsageStatistics(Document):
	by5minutes = ListField(EmbeddedDocumentField(UsageRecord), db_field='5minutes')
	byHour = ListField(EmbeddedDocumentField(UsageRecord), db_field='hour')
	byDay = ListField(EmbeddedDocumentField(UsageRecord), db_field='day')
	byMonth = ListField(EmbeddedDocumentField(UsageRecord), db_field='month')
	byYear = ListField(EmbeddedDocumentField(UsageRecord), db_field='year')
	meta = {
		'collection': 'usage_statistics',
	}


class Organization(Document):
	name = StringField(unique=True, required=True)
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True, reverse_delete_rule=DENY)
	label = StringField(required=True)
	homepageUrl = URLField(db_field='homepage_url')
	imageUrl = URLField(db_field='image_url')
	description = StringField()
	meta = {
		'ordering': ['name'],
		'indexes': [
			'name'
		]
	}


class Quota(EmbeddedDocument):
	monthly = EmbeddedDocumentField(Usage, required=True)
	used = EmbeddedDocumentField(Usage, required=True)
	usedTime = FloatField(db_field='used_time', required=True)
	continousFactor = FloatField(db_field='continous_factor')


class User(Document):
	name = StringField(required=True, unique_with='origin')
	origin = StringField(required=True)
	organization = ReferenceField(Organization, required=True, reverse_delete_rule=DENY)
	password = StringField(required=True)
	passwordTime = FloatField(db_field='password_time', required=True)
	lastLogin = FloatField(db_field='last_login', required=True)
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True, reverse_delete_rule=DENY)
	quota = EmbeddedDocumentField(Quota, required=True)
	realname = StringField()
	email = EmailField()
	flags = ListField(StringField())
	clientData = DictField(db_field='client_data')
	meta = {
		'ordering': ['name'],
		'indexes': [
			'lastLogin', 'passwordTime', 'flags', 'organization', ('name', 'origin')
		]
	}

	def storePassword(self, password):
		saltchars = string.ascii_letters + string.digits + './'
		salt = "$1$"
		salt += ''.join([ random.choice(saltchars) for _ in range(8) ])
		self.password = crypt.crypt(password, salt)
		self.password_time = time.time()
		self.save()
		return self

DEFAULTS = {
	"kvmqm": {"ram": 512, "cpus": 1, "diskspace": 10240},
	"openvz": {"ram": 512, "cpus": 1, "diskspace": 10240},
	"repy": {"ram": 50, "cpus": 0.25},
}

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
	meta = {
		'ordering': ['tech', '+preference', 'name'],
		'indexes': [
			('tech', 'preference'), ('tech', 'name')
		]
	}


class Network(Document):
	kind = StringField(required=True, unique=True)
	preference = IntField(default=0, required=True)
	restricted = BooleanField(default=False)
	label = StringField()
	description = StringField()
	big_icon = BooleanField(default=False)
	show_as_common = BooleanField(default=False)
	meta = {
		'ordering': ['-preference', 'kind'],
		'indexes': [
			('kind', 'preference')
		]
	}


def migrate():
	try:
		org = Organization(name="others", label="Others", totalUsage=UsageStatistics().save()).save()
	except NotUniqueError:
		org = Organization.objects.get(name="others")
	try:
		User(name="admin", origin="", organization=org, password="", passwordTime=time.time(),
			lastLogin=time.time(), totalUsage=UsageStatistics().save(), email="mail@example.com",
			quota=Quota(monthly=Usage(cputime= 5.0 *(60*60*24*30), memory=10e9, diskspace=100e9, traffic=5.0e6 /8.0*(60*60*24*30)), used=Usage(), usedTime=time.time(), continousFactor=1.0),
			realname="Admin", flags=["global_admin", "global_host_manager", "debug", "nomails"]).save().storePassword("changeme")
	except NotUniqueError:
		pass
	for tech, defaults in DEFAULTS.items():
		try:
			Profile(tech=tech, name="normal", label="Normal", preference=10, ram=defaults['ram'], cpus=defaults['cpus'], diskspace=defaults.get('diskspace', 0)).save()
		except NotUniqueError:
			pass
	try:
		Network(kind="internet", preference=10, label="Internet", big_icon=True, show_as_common=True).save()
	except NotUniqueError:
		pass