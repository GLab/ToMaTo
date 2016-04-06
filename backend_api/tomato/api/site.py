from ..lib.service import get_backend_core_proxy
from api_helpers import getCurrentUserInfo
from ..lib.remote_info import get_site_info

def site_list(organization=None):
	"""
	undocumented
	"""
	return get_backend_core_proxy().site_list(organization)

def site_create(name, organization, label="", attrs={}):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_create_sites(organization)
	return get_backend_core_proxy().site_create(name, organization, label, attrs)

def site_info(name):
	"""
	undocumented
	"""
	return get_site_info(name).info(update=True)

def site_modify(name, attrs):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_modify_site(get_site_info(name))
	return get_site_info(name).modify(attrs)

def site_remove(name):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_delete_site(get_site_info(name))
	return get_site_info(name).remove()