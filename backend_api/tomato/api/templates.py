from ..lib.service import get_backend_core_proxy
from api_helpers import checkauth, getCurrentUserInfo
from ..lib.remote_info import get_template_info, get_template_list, TemplateInfo

@checkauth
def template_list(tech=None):
	"""
	Retrieves information about all resources.

	Parameter *tech*:
	  If *tech* is set, only resources with a matching tech will be returned.

	Return value:
	  A list with information entries of all matching templates. Each list
	  entry contains exactly the same information as returned by
	  :py:func:`template_info`. If no resource matches, the list is empty.
	"""
	return get_template_list(tech)

def template_create(tech, name, attrs=None):
	"""
	Creates a template of given tech and name, configuring it with the given attributes.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  template techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the template.

	Parameter *attrs*:
	  The attributes of the template can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes if given. Attributes can
	  later be changed using :py:func:`template_modify`.

	Return value:
	  The return value of this method is the info dict of the new template as
	  returned by :py:func:`resource_info`.
	"""
	getCurrentUserInfo().check_may_create_user_resources()
	return TemplateInfo.create(tech, name, attrs)

def template_modify(id, attrs):
	"""
	Modifies a template, configuring it with the given attributes.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  template techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the template.

	Parameter *attrs*:
	  The attributes of the template can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes.

	Return value:
	  The return value of this method is the info dict of the resource as
	  returned by :py:func:`template_info`. This info dict will reflect all
	  attribute changes.

	Exceptions:
	  If the given template does not exist an exception *template does not
	  exist* is raised.
	"""
	getCurrentUserInfo().check_may_modify_user_resources()
	return get_template_info(id).modify(attrs)

def template_remove(id):
	"""
	Removes a template.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  template techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the template.

	Return value:
	  The return value of this method is ``None``.

	Exceptions:
	  If the given template does not exist an exception *template does not
	  exist* is raised.
	"""
	getCurrentUserInfo().check_may_remove_user_resources()
	return get_template_info(id).remove()

@checkauth
def template_info(id, include_torrent_data=False): #@ReservedAssignment
	"""
	Retrieves information about a template.

	Parameter *tech*:
	  The parameter *tech* must be a string identifying one of the supported
	  template techs.

	Parameter *name*:
	  The parameter *name* must be a string giving a name for the template.

	Parameter *include_torrent_data*:
	  boolean
	  if true, the return value includes the base64-encoded torrent file.
	  This may throw an error when a user without access to it tries to access a restricted template.

	Return value:
	  The return value of this method is a dict containing information
	  about this template.

	Exceptions:
	  If the given template does not exist an exception *template does not
	  exist* is raised.
	"""
	templ = get_template_info(id)
	if include_torrent_data:
		getCurrentUserInfo().check_may_get_template_torrent_data(templ)
		return get_backend_core_proxy().template_info(id, include_torrent_data)
	else:
		return templ.info(update=True)
