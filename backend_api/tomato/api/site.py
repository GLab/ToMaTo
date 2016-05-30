from api_helpers import getCurrentUserInfo
from ..lib.remote_info import get_site_info, get_site_list, SiteInfo,get_organization_list
from ..lib.error import UserError

def site_list(organization=None):
	"""
	Returns a list of all site. If an organization is given, the list is filtered and only contains sites which belong to the given organization
	:param organization: Filter
	:return: List of sites
	"""
	orga_exists = False
	for orga in get_organization_list():
		if orga["name"] == organization:
			orga_exists = True

	if not orga_exists and organization is not None:
		raise UserError(UserError.ENTITY_DOES_NOT_EXIST, message="Organization with that name does not exist")
	return get_site_list(organization)

def site_create(name, organization, label="", attrs=None):
	"""
	Creates a site and returns site_info for the newly created site
	:param name: Name for the new site. May not be a duplicate of an existing site
	:param organization: The organization to which this site belongs
	:param label: An optional label for this site
	:param attrs: Optional attributes for this site
	:return: Site_info for the newly created site
	"""
	if attrs is None: attrs = {}

	getCurrentUserInfo().check_may_create_sites(organization)
	return SiteInfo.create(name, organization, label, attrs)

def site_info(name):
	"""
	Returns the site_info for the site with the given name. If no site with this name exists, an error will be raised
	:param name: Name of the site
	:return: Site info for the site with the given name
	"""
	return get_site_info(name).info(update=True)

def site_modify(name, attrs):
	"""
	Modifies the given attributes of the site with the given name
	:param name: Name of the site which should be modified
	:param attrs: Attributes which should be modified
	:return: Site_info of the modified site
	"""
	getCurrentUserInfo().check_may_modify_site(get_site_info(name))
	return get_site_info(name).modify(attrs)

def site_remove(name):
	"""
	Removes site with given name
	:param name: Name of the site which should be removed
	:return: null
	"""
	getCurrentUserInfo().check_may_delete_site(get_site_info(name))
	return get_site_info(name).remove()