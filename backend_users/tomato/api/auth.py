from _shared import _getUser

def user_check_password(name, password, notify_activity=True):
	user = _getUser(name)
	if user.checkPassword(password):
		if notify_activity:
			user.register_activity()
		return True
	else:
		return False
