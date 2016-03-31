from ..lib.cache import cached
from ..user import User
import time

@cached(timeout=3600)
def statistics():
	return {
		'usage': {
			'users': User.objects.count(),
			'users_active_30days': User.objects.filter(lastLogin__gte = time.time() - 30*24*60*60).count()
		}
	}
