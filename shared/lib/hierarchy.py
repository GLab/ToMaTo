from error import InternalError, UserError

class ClassName:
	HOST_ELEMENT = "host_element"
	HOST_CONNECTION = "host_connection"
	ELEMENT = "element"
	CONNECTION = "connection"
	TOPOLOGY = "topology"
	USER = "user"
	ORGANIZATION = "organization"

_translations = {}

def register_class(class_name, cls, get_func, exists_func, parents_func):
	"""
	Register a hierarchy class.

	:param str class_name: name of the class. Should be in ClassName.
	:param cls: class object.
	:param get_func: function which takes an identifier as input and returns an instance of cls, or None if not (may also throw an error in this case).
	:param exists_func: function which takes an identifier as input and returns True iff get_func would find an instance.
	:param parents_func: function which takes an identifier as input and returns a list of (class_name, id) tuples. Should throw UserError.ENTITY_DOES_NOT_EXIST if this doesn't exist.
	"""
	_translations[class_name] = {
		'class': cls,
		'get': get_func,
		'exists': exists_func,
		'parents': parents_func
	}

def get(class_name, id_):
	InternalError.check(class_name in _translations, code=InternalError.ASSERTION,
	                    message="tried to access a not-managed class in hierarchy", data={"class_name": class_name})
	obj = _translations[class_name]['get'](id_)
	UserError.check(obj is not None, UserError.ENTITY_DOES_NOT_EXIST, message="entity doesn't exist.",
	                data={"class_name": class_name, "id_": id_})
	return obj

def exists(class_name, id_):
	InternalError.check(class_name in _translations, code=InternalError.ASSERTION,
	                    message="tried to access a not-managed class in hierarchy", data={"class_name": class_name})
	return _translations[class_name]['exists'](id_)

def get_parents(class_name, id_):
	InternalError.check(class_name in _translations, code=InternalError.ASSERTION,
	                    message="tried to access a not-managed class in hierarchy", data={"class_name": class_name})
	return _translations[class_name]['parents'](id_)

def available_objects():
	return _translations.keys()
