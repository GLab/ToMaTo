from .lib import hierarchy
from .lib.error import UserError
import user
import organization


# user

def user_exists(id_):
	return (user.User.get(id_) is not None)


def user_parents(id_):
	u = user.User.get(id_)
	UserError.check(u is not None, UserError.ENTITY_DOES_NOT_EXIST, message="entity doesn't exist.",
	                data={"class_name": hierarchy.ClassName.TOPOLOGY, "id_": id_})
	return [(hierarchy.ClassName.ORGANIZATION, u.organization.name)]



# organization

def orga_exists(id_):
	return (organization.Organization.get(id_) is not None)

def orga_parents(id_):
	return []


def init():
	hierarchy.register_class(hierarchy.ClassName.USER, user.User, user.User.get, user_exists, user_parents)
	hierarchy.register_class(hierarchy.ClassName.ORGANIZATION, organization.Organization, organization.Organization.get, orga_exists, orga_parents)
