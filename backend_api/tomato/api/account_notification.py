from api_helpers import getCurrentUserName, getCurrentUserInfo
from ..lib.service import get_backend_users_proxy
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
	Sends an email to the account
	"""
	if from_support:
		fromUser = None
	else:
		fromUser = getCurrentUserName()
	getCurrentUserInfo().check_may_send_message_to_user(get_user_info(name))
	api = get_backend_users_proxy()
	api.send_message(name, subject, message, fromUser=fromUser, ref=ref, subject_group=subject_group)

def broadcast_announcement(title, message, ref=None, show_sender=True, subject_group=None, organization_filter=None):
	getCurrentUserInfo().check_may_broadcast_messages(organization_filter)
	api = get_backend_users_proxy()
	api.broadcast_message(title, message, fromUser=(getCurrentUserName() if show_sender else None), ref=ref,
												subject_group=subject_group, organization_filter=organization_filter)