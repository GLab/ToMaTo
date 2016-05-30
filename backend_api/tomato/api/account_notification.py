from api_helpers import getCurrentUserInfo, getCurrentUserName, checkauth
from ..lib.service import get_backend_users_proxy, get_backend_core_proxy
from ..lib.remote_info import get_user_info

def account_notifications(include_read=False):
	"""
	List notifications for the currently logged in user.

	:param bool include_read: include read notifications. if False, only return unread ones.
	:return: list of Notification
	"""
	username = getCurrentUserName()
	api = get_backend_users_proxy()
	return api.notification_list(username, include_read)

def account_notification_set_read(notification_id, read):
	"""
	Modify the read status of a notification

	:param str notification_id: ID of the notification to modify
	:param bool read: new read status of the notification
	:return: None
	"""
	username = getCurrentUserName()
	api = get_backend_users_proxy()
	api.notification_set_read(username, notification_id, read)
	get_user_info(username).invalidate_info()

def account_send_notification(name, subject, message, ref=None, from_support=False, subject_group=None):
	"""
	Sends an email to the account and also sends a message via the internal message system
	:param str ref arbitrary string for referencing
	:param str subject_group arbitrary string to reference desired subject_group for this message
	"""
	if from_support:
		fromUser = None
	else:
		fromUser = getCurrentUserName()
	getCurrentUserInfo().check_may_send_message_to_user(get_user_info(name))
	api = get_backend_users_proxy()
	api.send_message(name, subject, message, fromUser=fromUser, ref=ref, subject_group=subject_group)

def broadcast_announcement(title, message, ref=None, show_sender=True, subject_group=None, organization_filter=None):
	"""
	takes a list of filters to broadcast a message.
	sends one message to each user who matches at least one filter.
	:param str title: message subject
	:param str message: message body
	:param NoneType or tuple(str, str) ref: ref pair
	:param bool show_sender Either sender is shown as sender or field is marked with 'None'
	:param NoneType or str subject_group: subject group
	:param NoneType or list(tuple) filters: list of pairs (organization, flag). if this is None, send to every user.
	"""
	getCurrentUserInfo().check_may_broadcast_messages(organization_filter)
	api = get_backend_users_proxy()
	api.broadcast_message(title, message, fromUser=(getCurrentUserName() if show_sender else None), ref=ref,
												subject_group=subject_group, organization_filter=organization_filter)

@checkauth
def notifyAdmins(subject, text, global_contact = True, issue="admin"):
	"""
	Request assistence by sending a notification to all AdminContact or HostContact users.
	:param subject: notification subject
	:param text: notification body
	:param global_contact: if True, send to Global*Contact. Otherwise to Orga*Contact.
	:param issue: if issue is "admin", the notification is sent to *AdminContact. Otherwise, it is sent to *HostContact.
	:return:
	"""
	user_orga = getCurrentUserInfo().get_organization_name()
	user_name = getCurrentUserName()
	get_backend_core_proxy().notifyAdmins(subject, text, global_contact, issue, user_orga, user_name)