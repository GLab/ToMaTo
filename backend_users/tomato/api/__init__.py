
def debug(method, args=None, kwargs=None, profile=None):
	func = globals().get(method)
	from ..lib import debug
	result = debug.run(func, args, kwargs, profile)
	return result.marshal()

def dummy():
	# todo: this should be obsolete...
	return "Hello world!"

from auth import user_check_password

from dump import dump_count, dump_info, dump_list

from notification import notification_get, notification_list, notification_set_read, send_message, broadcast_message

from organization import organization_remove, organization_modify, organization_list,\
	organization_info, organization_create, organization_exists

from user import user_create, user_exists, user_info, user_list, user_modify, user_modify_password,\
	user_remove, username_list
