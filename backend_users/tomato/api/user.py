from ..user import User
from _shared import _getUser, _getOrganization

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