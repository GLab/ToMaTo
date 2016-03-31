from ..organization import Organization
from ..user import User
from _shared import _getOrganization

def organization_exists(name):
	if _getOrganization(name):
		return True
	return False

def organization_create(**args):
	org = Organization.create(**args)
	return org.name

def organization_list(user_list_filter=None):
	if user_list_filter is not None:
		orga_list = []
		for user in user_list_filter:
			user_orga=User.get("organization")
			if user_orga not in orga_list:
				orga_list.append(user_orga)
		return orga_list
	return [o.info() for o in Organization.objects.all()]

def organization_info(name):
	orga = _getOrganization(name)
	return orga.info()

def organization_modify(name, **args):
	orga = _getOrganization(name)
	orga.modify(**args)
	return orga.info()

def organization_remove(name):
	orga = _getOrganization(name)
	orga.remove()
	return True