from ..lib.userflags import flags, categories

#fixme: these functions should be removed, since they are now available via lib...


def account_flags():
	"""
	Returns the dict of all account flags and their short descriptions.

	Return value:
	  A list of all available account flags.
	"""
	return flags

#deprecated
def account_flag_categories():
	"""
	Returns a dict which puts flags into different categories
	"""
	res = {}
	for cat in categories:
		res[cat['title']] = cat['flags']
	return res

def account_flag_configuration():
	return {
		'flags': flags,
		'categories': categories
		}
