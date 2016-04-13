from ..resources.profile import Profile
from ..lib.error import UserError

def _getProfile(id_):
	res = Profile.objects.get(id=id_)
	UserError.check(res, code=UserError.ENTITY_DOES_NOT_EXIST, message="Profile does not exist", data={"id": id_})
	return res


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
	res = Profile.objects(tech=tech) if tech else Profile.objects()
	return [r.info() for r in res]


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
	if not attrs: attrs = {}
	attrs = dict(attrs)
	attrs.update(name=name, tech=tech)
	res = Profile.create(attrs)
	return res.info()


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
	res = _getProfile(id)
	res.modify(attrs)
	return res.info()


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
	res = _getProfile(id)
	res.remove()
	return {}

def profile_id(tech, name):
	"""
	translate tech and name to a template id
	"""
	return str(Profile.objects.get(tech=tech, name=name).id)

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
	res = _getProfile(id)
	return res.info()
