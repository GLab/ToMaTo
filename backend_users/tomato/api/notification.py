from _shared import _getUser, _getOrganization
from ..user import User, Flags
from ..lib.error import UserError

def send_message(toUser, subject, message, fromUser=None, ref=None, subject_group=None):
	toUser = _getUser(toUser)
	if fromUser:
		fromUser = _getUser(fromUser)
	return toUser.send_message(toUser=toUser, fromUser=fromUser, subject=subject, message=message,
														 	ref=ref, subject_group=subject_group)

def broadcast_message(title, message, fromUser=None, ref=None, subject_group=None,
											  organization_filter=None, flag_filter=None, limit_range_to_fromUser_permissions=True):
	if organization_filter:
		organization = _getOrganization(organization_filter)
		receivers = User.objects(organization=organization)
	else:
		receivers = User.objects.all()
	if flag_filter:
		filter(lambda u: flag_filter in u['flags'], receivers)

	for user in receivers:
		user.send_message(toUser=user, fromUser=fromUser, title=title, message=message,
												ref=ref, subject_group=subject_group)

def notification_list(username, includeRead=False):
	user = _getUser(username)
	return user.notification_list(includeRead)

def notification_get(username, notificationId):
	user = _getUser(username)
	return user.notification_get(notificationId).info()

def notification_set_read(username, notificationId, read=True):
	user = _getUser(username)
	return user.notification_set_read(notificationId, read)
