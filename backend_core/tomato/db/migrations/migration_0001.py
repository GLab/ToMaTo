from mongoengine import *
import string, random, crypt, time
from mongoengine.errors import NotUniqueError


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
	for tech, defaults in DEFAULTS.items():
		try:
			Profile(tech=tech, name="normal", label="Normal", preference=10, ram=defaults['ram'], cpus=defaults['cpus'], diskspace=defaults.get('diskspace', 0)).save()
		except NotUniqueError:
			pass
	try:
		Network(kind="internet", preference=10, label="Internet", big_icon=True, show_as_common=True).save()
	except NotUniqueError:
		pass