from ..lib.userflags import flags, categories
from ..lib.cache import cached
from ..lib.topology_role import role_descriptions

#fixme: these functions should be removed, since they are now available via lib...


@cached(36000000)
def account_flags():
	"""
	Returns the dict of all account flags and their short descriptions.

	Return value:
	  A list of all available account flags.
	"""
	return flags

#deprecated
@cached(36000000)
def account_flag_categories():
	"""
	Returns a dict which puts flags into different categories
	"""
	res = {}
	for cat in categories:
		res[cat['title']] = cat['flags']
	return res

@cached(36000000)
def account_flag_configuration():
	return {
		'flags': flags,
		'categories': categories
		}

@cached(36000000)
def topology_permissions():
	return role_descriptions()