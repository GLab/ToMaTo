from _shared import _getUser

def user_check_password(name, password):
	user = _getUser(name)
	return user.checkPassword(password)
