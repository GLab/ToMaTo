from api_helpers import getCurrentUserInfo
from ..lib.remote_info import get_organization_info, get_organization_list, OrganizationInfo

def organization_list():
	"""
	undocumented
	"""
	return get_organization_list()

def organization_create(name, label="", attrs=None):
	"""
	undocumented
	"""
	if attrs is None: attrs = {}
	getCurrentUserInfo().check_may_create_organizations()
	return OrganizationInfo.create(name, label, attrs)

def organization_info(name):
	"""
	undocumented
	"""
	return get_organization_info(name).info(update=True)

def organization_modify(name, attrs):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_modify_organization(name)
	return get_organization_info(name).modify(attrs)

def organization_remove(name):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_delete_organization(name)
	get_organization_info(name).remove()

def organization_usage(name): #@ReservedAssignment
	getCurrentUserInfo().check_may_view_organization_usage(name)
	return get_organization_info(name).get_usage()