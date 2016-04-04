from ..lib.cache import cached

@cached(timeout=3600)
def statistics():
	return {}
