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
											  organization_filter=None, flag_filter=None):
	broadcast_message_multifilter(title=title, message=message, ref=ref, subject_group=subject_group,
																filters=[(organization_filter, flag_filter)])

def broadcast_message_multifilter(title, message, fromUser=None, ref=None, subject_group=None,
																	filters=None):
	"""
	takes a list of filters to broadcast a message.
	sends one message to each user who matches at least one filter.
	:param str title: message subject
	:param str message: message body
	:param NoneType or str fromUser: sending user
	:param NoneType or tuple(str, str) ref: ref pair
	:param NoneType or str subject_group: subject group
	:param NoneType or list(tuple) filters: list of pairs (organization, flag). if this is None, send to every user.
	"""
	if filters is None:
		filters = [(None, None)]

	target_users = set()
	for filter_pair in filters:

		if filter_pair[0]:
			organization = _getOrganization(filter_pair[0])
			users = User.objects(organization=organization)
		else:
			users = User.objects.all()

		if filter_pair[1]:
			users = filter(lambda u: filter_pair[1] in u.flags, users)

		target_users.update([u.name for u in users])

	for username in target_users:
		_getUser(username).send_message(fromUser=fromUser, subject=title, message=message,
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
