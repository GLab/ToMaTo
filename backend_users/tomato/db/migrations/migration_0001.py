from mongoengine import *
import string, random, crypt, time
from mongoengine.errors import NotUniqueError


class Usage(EmbeddedDocument):
	memory = FloatField(default=0.0) #unit: bytes
	diskspace = FloatField(default=0.0) #unit: bytes
	traffic = FloatField(default=0.0) #unit: bytes
	cputime = FloatField(default=0.0) #unit: cpu seconds


class Organization(Document):
	name = StringField(unique=True, required=True)
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


def migrate():
	try:
		org = Organization(name="others", label="Others").save()
	except NotUniqueError:
		org = Organization.objects.get(name="others")
	try:
		User(name="admin", origin="", organization=org, password="", passwordTime=time.time(),
			lastLogin=time.time(), email="mail@example.com",
			quota=Quota(monthly=Usage(cputime= 5.0 *(60*60*24*30), memory=10e9, diskspace=100e9, traffic=5.0e6 /8.0*(60*60*24*30)), used=Usage(), usedTime=time.time(), continousFactor=1.0),
			realname="Admin", flags=["global_admin", "global_host_manager", "debug", "nomails"]).save().storePassword("changeme")
	except NotUniqueError:
		pass