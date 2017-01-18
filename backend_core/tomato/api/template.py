from ..resources.template import Template
from ..lib.error import UserError
from ..lib.exceptionhandling import wrap_errors

@wrap_errors(errorcls_func=lambda e: UserError, errorcode=UserError.ENTITY_DOES_NOT_EXIST)
def _getTemplate(id_):
	res = Template.objects.get(id=id_)
	UserError.check(res, code=UserError.ENTITY_DOES_NOT_EXIST, message="Template does not exist", data={"id": id_})
	return res



def template_list(tech_type=None):
	"""
	Retrieves information about all resources.

	Parameter *tech_type*:
	  If *tech_type* is set, only resources with a matching tech_type will be returned.

	Return value:
	  A list with information entries of all matching templates. Each list
	  entry contains exactly the same information as returned by
	  :py:func:`template_info`. If no resource matches, the list is empty.
	"""
	res = Template.objects(tech_type=tech_type) if tech_type else Template.objects()
	return [r.info() for r in res]


def template_create(tech_type, name, attrs=None):
	"""
	Creates a template of given tech and name, configuring it with the given attributes.

	Parameter *tech_type*:
	  The parameter *tech_type* must be a string identifying one of the supported
	  template tech_types.

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
	if not attrs: attrs = {}
	attrs = dict(attrs)
	attrs.update(name=name, tech_type=tech_type)
	res = Template.create(**attrs)
	return res.info()


def template_modify(id, attrs):
	"""
	Modifies a template, configuring it with the given attributes.

	Parameter *id*:
	  The parameter *id* must be a string identifying one of the existing
	  templates.

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
	res = _getTemplate(id)
	res.modify(**attrs)
	return res.info()


def template_remove(id):
	"""
	Removes a template.

	Parameter *id*:
	  The parameter *id* must be a string identifying one of the existing
	  templates.

	Return value:
	  The return value of this method is ``None``.

	Exceptions:
	  If the given template does not exist an exception *template does not
	  exist* is raised.
	"""
	res = _getTemplate(id)
	res.remove()
	return {}

@wrap_errors(errorcls_func=lambda e: UserError, errorcode=UserError.ENTITY_DOES_NOT_EXIST)
def template_id(tech_type, name):
	"""
	translate tech_type and name to a template id
	"""
	return str(Template.objects.get(tech_type=tech_type, name=name).id)

@wrap_errors(errorcls_func=lambda e: UserError, errorcode=UserError.ENTITY_DOES_NOT_EXIST)
def template_info(id): #@ReservedAssignment
	"""
	Retrieves information about a template.

	Parameter *id*:
	  The parameter *id* must be a string identifying one of the existing
	  templates.

	Return value:
	  The return value of this method is a dict containing information
	  about this template.

	Exceptions:
	  If the given template does not exist an exception *template does not
	  exist* is raised.
	"""
	res = _getTemplate(id)
	return res.info()
