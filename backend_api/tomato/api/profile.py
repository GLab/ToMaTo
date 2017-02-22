from api_helpers import getCurrentUserInfo, checkauth
from ..lib.remote_info import get_profile_info, get_profile_list, ProfileInfo

def profile_list(type=None):
	"""
	Retrieves information about all resources.

	Parameter *type*:
	  If *type* is set, only resources with a matching type will be returned.

	Return value:
	  A list with information entries of all matching profiles. Each list
	  entry contains exactly the same information as returned by
	  :py:func:`profile_info`. If no resource matches, the list is empty.
	"""
	return get_profile_list(type)


def profile_create(type, name, attrs=None):
	"""
	Creates a profile of given type and name, configuring it with the given attributes.

	Parameter *type*:
	  The parameter *type* must be a string identifying one of the supported
	  profile type.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the profile.

	Parameter *attrs*:
	  The attributes of the profile can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes if given. Attributes can
	  later be changed using :py:func:`profile_modify`.

	Return value:
	  The return value of this method is the info dict of the new profile as
	  returned by :py:func:`resource_info`.
	"""
	getCurrentUserInfo().check_may_create_user_resources()
	return ProfileInfo.create(type, name, attrs)


def profile_modify(id, attrs):
	"""
	Modifies a profile, configuring it with the given attributes.

	Parameter *id*:
	  The parameter *id* must be a string identifying one of the existing
	  profiles.

	Parameter *attrs*:
	  The attributes of the profile can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes.

	Return value:
	  The return value of this method is the info dict of the resource as
	  returned by :py:func:`profile_info`. This info dict will reflect all
	  attribute changes.

	Exceptions:
	  If the given profile does not exist an exception *profile does not
	  exist* is raised.
	"""
	getCurrentUserInfo().check_may_modify_user_resources()
	return get_profile_info(id).modify(attrs)


def profile_remove(id):
	"""
	Removes a profile.

	Parameter *id*:
	  The parameter *id* must be a string identifying one of the existing
	  profiles.

	Return value:
	  The return value of this method is ``None``.

	Exceptions:
	  If the given profile does not exist an exception *profile does not
	  exist* is raised.
	"""
	getCurrentUserInfo().check_may_remove_user_resources()
	return get_profile_info(id).remove()


@checkauth
def profile_info(id):
	"""
	Retrieves information about a profile.

	Parameter *id*:
	  The parameter *id* must be a string identifying one of the existing
	  profiles.

	Return value:
	  The return value of this method is a dict containing information
	  about this profile.

	Exceptions:
	  If the given profile does not exist an exception *profile does not
	  exist* is raised.
	"""
	return get_profile_info(id).info(update=True)
