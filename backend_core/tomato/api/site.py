from ..host import Site
from ..lib.error import UserError

def _getSite(name):
	s = Site.get(name)
	UserError.check(s, code=UserError.ENTITY_DOES_NOT_EXIST, message="Site with that name does not exist", data={"name": name})
	return s

def site_list(organization=None):
	"""
	undocumented
	"""
	if organization:
		sites = Site.objects(organization=organization)
	else:
		sites = Site.objects.all()
	return [s.info() for s in sites]

def site_create(name, organization, label="", attrs=None):
	"""
	undocumented
	"""
	if attrs is None:
		attrs = {}

	s = Site.create(name, organization, label, attrs)
	return s.info()

def site_info(name):
	"""
	undocumented
	"""
	site = _getSite(name)
	return site.info()

def site_modify(name, attrs):
	"""
	undocumented
	"""
	site = _getSite(name)
	site.modify(attrs)
	return site.info()

def site_remove(name):
	"""
	undocumented
	"""
	site = _getSite(name)
	site.remove()
