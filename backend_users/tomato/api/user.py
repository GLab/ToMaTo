from ..user import User
from _shared import _getUser, _getOrganization

def user_list(organization=None, with_flag=None):
	if organization:
		organization = _getOrganization(organization)
		result = [u.info() for u in User.objects(organization=organization)]
	else:
		result = [u.info() for u in User.objects.all()]
	if with_flag:
		filter(lambda u: with_flag in u['flags'], result)
	return result
	# old code from backend_core
	#
	# if organization:
	# 	organization = _getOrganization(organization)
	# if currentUser().hasFlag(Flags.GlobalAdmin):
	# 	accounts = getAllUsers(organization=organization, with_flag=with_flag) if organization else getAllUsers(with_flag=with_flag)
	# 	return [acc.info(True) for acc in accounts]
	# elif currentUser().hasFlag(Flags.OrgaAdmin):
	# 	UserError.check(organization == currentUser().organization, code=UserError.DENIED,
	# 		message="Not enough permissions")
	# 	return [acc.info(True) for acc in getAllUsers(organization=currentUser().organization, with_flag=with_flag)]
	# else:
	# 	raise UserError(code=UserError.DENIED, message="Not enough permissions")

def user_info(name):
	user = _getUser(name)
	return user.info()

def user_create(**args):
	#fixme: explicit arguments
	user = User.create(**args)
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
