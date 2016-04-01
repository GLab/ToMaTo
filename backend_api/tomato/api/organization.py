from ..lib.service import get_backend_users_proxy
from api_helpers import getCurrentUserInfo, checkauth

def organization_list():
	"""
	undocumented
	"""
	api = get_backend_users_proxy()
	return api.organization_list()

def organization_create(name, label="", attrs={}):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_create_organizations()
	api = get_backend_users_proxy()
	return api.organization_create(name, label, attrs)

def organization_info(name):
	"""
	undocumented
	"""
	api = get_backend_users_proxy()
	return api.organization_info(name)

def organization_modify(name, attrs):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_modify_organization(name)
	api = get_backend_users_proxy()
	return api.organization_modify(name, attrs)

def organization_remove(name):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_delete_organization(name)
	api = get_backend_users_proxy()
	api.organization_remove(name)

@checkauth
def organization_usage(name): #@ReservedAssignment
	#fixme: broken
	orga = _getOrganization(name)
	return orga.totalUsage.info()