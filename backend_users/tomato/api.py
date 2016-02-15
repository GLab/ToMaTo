from .lib.error import UserError
from .organization import Organization
from .user import User
import dump

def debug(method, args=None, kwargs=None, profile=None):
	func = globals().get(method)
	from .lib import debug
	result = debug.run(func, args, kwargs, profile)
	return result.marshal()

def dummy():
	return "Hello world!"

def _getOrganization(name):
	o = Organization.get(name)
	UserError.check(o, code=UserError.ENTITY_DOES_NOT_EXIST, message="Organization with that name does not exist", data={"name": name})
	return o

def _getUser(name):
	u = User.get(name)
	UserError.check(u, code=UserError.ENTITY_DOES_NOT_EXIST, message="User with that name does not exist", data={"name": name})
	return u

def organization_create(**args):
	org = Organization.create(**args)
	return org.name

def organization_list():
	return [o.info() for o in Organization.objects.all()]

def organization_info(name):
	orga = _getOrganization(name)
	return orga.info()

def organization_modify(name, **args):
	orga = _getOrganization(name)
	orga.modify(**args)
	return orga.info()

def organization_remove(name):
	orga = _getOrganization(name)
	orga.remove()
	return True

def user_list(organization=None):
	if organization:
		organization = _getOrganization(organization)
		return [u.info() for u in User.objects(organization=organization)]
	else:
		return [u.info() for u in User.objects.all()]

def user_info(name):
	user = _getUser(name)
	return user.info()

def user_create(**args):
	user = User.create(**args)
	return user.info()

def user_check_password(name, password):
	user = _getUser(name)
	return user.checkPassword(password)

def user_modify_password(name, password):
	user = _getUser(name)
	return user.modify_password(password)

def user_remove(name):
	user = _getUser(name)
	user.remove()

def notification_send(toUser, fromUser, **args):
	toUser = _getUser(toUser)
	if fromUser:
		fromUser = _getUser(fromUser)
	args["fromUser"] = fromUser
	return toUser.notification_add(fromUser=fromUser, **args)

def notification_list(user, includeRead=False):
	user = _getUser(user)
	return user.notification_list(includeRead)

def notification_get(user, notificationId):
	user = _getUser(user)
	return user.notification_get(notificationId).info()

def notification_read(user, notificationId):
	user = _getUser(user)
	return user.notification_read(notificationId)




def dump_count():
	"""
	returns the total number of error dumps
	"""
	return dump.getCount()

def dump_list(after=None,list_only=False,include_data=False,compress_data=True):
	"""
	returns a list of dumps.

	Parameter *after*:
      If set, only include dumps which have a timestamp after this time.

    Parameter *list_only*:
      If True, only include dump IDs.

    Parameter *include_data*:
      If True, include detailed data. This may be about 1M per dump.

    Parameter *compress_data*:
      If True and include_data, compress the detailed data before returning. It may still be around 20M per dump after compressing.
    """
	return dump.getAll(after=after, list_only=list_only, include_data=include_data, compress_data=compress_data)

def dump_info(dump_id, include_data=False, compress_data=True, dump_on_error=False):
	"""
	returns info of a single dump

	Parameter *dump_id*:
	  The internal id of the dump

	Parameter *include_data*:
      If True, include detailed data. This may be about 1M.

    Parameter *compress_data*:
      If True and include_data, compress the detailed data before returning. It may still be around 20M after compressing.

    Parameter *dump_on_error*:
      Set to False if you wish to create a dump if the given dump doesn't exist, i.e., this call is by the system.
	"""
	return dump.get(dump_id, include_data=include_data, compress_data=compress_data, dump_on_error=dump_on_error)
