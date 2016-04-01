from ..lib.service import get_backend_core_proxy
from api_helpers import getCurrentUserInfo, checkauth
from ..lib.remote_info import get_profile_info

def profile_list(tech=None):
	"""
	Retrieves information about all resources.

	Parameter *tech*:
	  If *tech* is set, only resources with a matching tech will be returned.

	Return value:
	  A list with information entries of all matching profiles. Each list
	  entry contains exactly the same information as returned by
	  :py:func:`profile_info`. If no resource matches, the list is empty.
	"""
	return get_backend_core_proxy().profile_list(tech)


def profile_create(tech, name, attrs=None):
	"""
	Creates a profile of given tech and name, configuring it with the given attributes.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  profile techs.

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
	return get_backend_core_proxy().profile_create(tech, name, attrs)


def profile_modify(id, attrs):
	"""
	Modifies a profile, configuring it with the given attributes.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  profile techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the profile.

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

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  profile techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the profile.

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

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  profile techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the profile.

	Return value:
	  The return value of this method is a dict containing information
	  about this profile.

	Exceptions:
	  If the given profile does not exist an exception *profile does not
	  exist* is raised.
	"""
	return get_profile_info(id).remove()
