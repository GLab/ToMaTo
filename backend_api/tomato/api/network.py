from ..lib.service import get_backend_core_proxy
from api_helpers import getCurrentUserInfo, checkauth
from ..lib.remote_info import get_network_info

def network_list():
	"""
	Retrieves information about all resources.

	Return value:
	  A list with information entries of all matching networks. Each list
	  entry contains exactly the same information as returned by
	  :py:func:`network_info`. If no resource matches, the list is empty.
	"""
	return get_backend_core_proxy().network_list()


def network_create(kind, attrs=None):
	"""
	Creates a network of given tech and name, configuring it with the given attributes.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying the kind of the network.

	Parameter *attrs*:
	  The attributes of the network can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes if given. Attributes can
	  later be changed using :py:func:`network_modify`.

	Return value:
	  The return value of this method is the info dict of the new network as
	  returned by :py:func:`resource_info`.
	"""
	getCurrentUserInfo().check_may_create_technical_resources()
	return get_backend_core_proxy().network_create(kind, attrs)


def network_modify(id, attrs):
	"""
	Modifies a network, configuring it with the given attributes.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying the kind of the network.

	Parameter *attrs*:
	  The attributes of the network can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes.

	Return value:
	  The return value of this method is the info dict of the resource as
	  returned by :py:func:`network_info`. This info dict will reflect all
	  attribute changes.

	Exceptions:
	  If the given network does not exist an exception *network does not
	  exist* is raised.
	"""
	getCurrentUserInfo().check_may_modify_technical_resources()
	return get_network_info(id).modify(attrs)


def network_remove(id):
	"""
	Removes a network.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying the kind of the network.

	Return value:
	  The return value of this method is ``None``.

	Exceptions:
	  If the given network does not exist an exception *network does not
	  exist* is raised.
	"""
	getCurrentUserInfo().check_may_remove_technical_resources()
	return get_network_info(id).remove()


@checkauth
def network_info(id): #@ReservedAssignment
	"""
	Retrieves information about a network.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying the kind of the network.

	Return value:
	  The return value of this method is a dict containing information
	  about this network.

	Exceptions:
	  If the given network does not exist an exception *network does not
	  exist* is raised.
	"""
	return get_network_info(id).info(update=True)
