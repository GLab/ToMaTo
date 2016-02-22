from _shared import _getUser
from ..lib.error import InternalError

def send_message(self, toUser, title, message, fromUser=None, ref=None, subject_group=None):
	toUser = _getUser(toUser)
	if fromUser:
		fromUser = _getUser(fromUser)
	return toUser.send_message(toUser=toUser, fromUser=fromUser, title=title, message=message,
														 ref=ref, subject_group=subject_group)

def broadcast_message(title, message, fromUser=None, ref=None, subject_group=None, organization_filter=None, flag_filter=None):
	#fixme: implement
	pass

def notification_list(username, includeRead=False):
	user = _getUser(username)
	return user.notification_list(includeRead)

def notification_get(username, notificationId):
	user = _getUser(username)
	return user.notification_get(notificationId).info()

def notification_set_read(username, notificationId, read=True):
	user = _getUser(username)
	return user.notification_set_read(notificationId, read)
