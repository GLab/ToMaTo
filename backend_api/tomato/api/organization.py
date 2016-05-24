from api_helpers import getCurrentUserInfo
from ..lib.remote_info import get_organization_info, get_organization_list, OrganizationInfo
from ..lib.error import UserError

def organization_list():
	"""
	Returns a list of all existing organizations
	:return: list of organization infos
	"""
	return get_organization_list()

def organization_create(name, label=None, attrs=None):
	"""
	Creates an organization with the provided name, label and attributes.
	:param name: Needed. If an organization with this name already exists, an error will be raised
	:param label: Display name. May be omitted and will then be set to the 'name'
	:param attrs: Optional parameter which may contain additional attributes like
		'homepage_url',
		'image_url' and
		'description'

	:return: Returns the organization info of the newly created organization
	"""
	if attrs is None:
		attrs = {}
	if label is None:
		label = name
	getCurrentUserInfo().check_may_create_organizations()
	for orga in organization_list():
		if orga["name"]==name:
			raise UserError(UserError.ALREADY_EXISTS, message="Organization already exists")
	return OrganizationInfo.create(name, label, attrs)

def organization_info(name):
	"""
	Returns the 'organization_info' of the organization with the provided name if it exists. Otherwise an error will be raised
	:param name: Name of the organization for which the organization_info is requested
	:return: 'organization_info' of the organization with the provided name
	"""
	return get_organization_info(name).info(update=True)

def organization_modify(name, attrs):
	"""
	This function provides a convenient way of modifying attributes of an existing organization.
	:param name: Name of the organization which should be modified
	:param attrs: Dict with attributes that should be changed for the given organization
	:return: 'organization_info' of the organization with the provided name
	"""
	getCurrentUserInfo().check_may_modify_organization(name)
	return get_organization_info(name).modify(attrs)

def organization_remove(name):
	"""
	Removes the organization with the given name, if no user and no site still exist which belong to this organization
	:param name: Name of the organization
	:return: null
	"""
	getCurrentUserInfo().check_may_delete_organization(name)
	get_organization_info(name).remove()

def organization_usage(name): #@ReservedAssignment
	getCurrentUserInfo().check_may_view_organization_usage(name)
	return get_organization_info(name).get_usage(hide_no_such_record_error=True)
