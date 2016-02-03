from .lib.error import UserError
from .organization import Organization
from .user import User

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