from ..organization import Organization
from ..user import User
from _shared import _getOrganization
from ..lib.error import UserError

def organization_exists(name):
	if Organization.get(name):
		return True
	return False

def organization_create(name, **args):
	args['name'] = name
	UserError.check(not organization_exists(name), code=UserError.ALREADY_EXISTS, message="Organization with that name already exists", data={"name": name})
	org = Organization.create(**args)
	return org.name

def organization_list(user_list_filter=None):
	if user_list_filter is not None:
		orgas = {}
		for username in user_list_filter:
			user_orga = User.get(username).organization
			orgas[user_orga.name] = user_orga  # this eliminates duplicate organizations
		return [o.info for o in orgas.itervalues()]
	return [o.info() for o in Organization.objects.all()]

def organization_info(name):
	orga = _getOrganization(name)
	return orga.info()

def organization_modify(name, args):
	orga = _getOrganization(name)
	orga.modify(**args)
	return orga.info()

def organization_remove(name):
	orga = _getOrganization(name)
	orga.remove()
	return True