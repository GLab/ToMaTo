
def debug(method, args=None, kwargs=None, profile=None):
	func = globals().get(method)
	from ..lib import debug
	result = debug.run(func, args, kwargs, profile)
	return result.marshal()

def dummy():
	# todo: this should be obsolete...
	return "Hello world!"

from auth import *
from dump import *
from organization import *
from user import *
