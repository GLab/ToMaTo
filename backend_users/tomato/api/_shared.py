from ..user import User
from ..lib.error import UserError
from ..organization import Organization

def _getOrganization(name):
	o = Organization.get(name)
	UserError.check(o, code=UserError.ENTITY_DOES_NOT_EXIST, message="Organization with that name does not exist", data={"name": name})
	return o

def _getUser(name):
	u = User.get(name)
	UserError.check(u, code=UserError.ENTITY_DOES_NOT_EXIST, message="User with that name does not exist", data={"name": name})
	return u
