from ..user import User
from _shared import _getUser, _getOrganization
from ..lib.error import UserError
from ..lib.exceptionhandling import wrap_errors

def _user_list(organization=None, with_flag=None):
	if organization:
		organization = _getOrganization(organization)
		result = User.objects(organization=organization)
	else:
		result = User.objects.all()
	if with_flag:
		result = filter(lambda u: with_flag in u.flags, result)
	return result

def username_list(organization=None, with_flag=None):
	return [u.name for u in _user_list(organization, with_flag)]

def user_list(organization=None, with_flag=None):
	return [u.info() for u in _user_list(organization, with_flag)]

def user_exists(name):
	if _getUser(name):
		return True
	return False

def user_info(name):
	user = _getUser(name)
	return user.info()

@wrap_errors(errorcls_func=lambda e: UserError, errorcode=UserError.ALREADY_EXISTS)
def user_create(name, organization, email, password=None, attrs=None):
	user = User.create(name, organization, email, password, attrs)
	return user.info()

def user_modify_password(name, password):
	user = _getUser(name)
	return user.modify_password(password)

def user_remove(name):
	user = _getUser(name)
	user.remove()

def user_modify(name, attrs):
	user = _getUser(name)
	user.modify(**attrs)
