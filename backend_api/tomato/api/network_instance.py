from api_helpers import getCurrentUserInfo, checkauth
from ..lib.remote_info import get_network_instance_info, get_network_instance_list, NetworkInstanceInfo

@checkauth
def network_instance_list(network=None, host=None):
	"""
	Retrieves information about all resources.

	Parameter *kind*:
	  If *kind* is set, only resources with a matching kind will be returned.

	Parameter *host*:
	  If *host* is set, only resources with a matching host will be returned.

	Return value:
	  A list with information entries of all matching network_instances. Each list
	  entry contains exactly the same information as returned by
	  :py:func:`network_instance_info`. If no resource matches, the list is empty.
	"""
	return get_network_instance_list(network, host)


@checkauth
def network_instance_create(network, host, attrs=None):
	"""
	Creates a network_instance of given kind and host, configuring it with the given attributes.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying one of the supported
	  network_instance kinds.

	Parameter *host*:
	  The parameter *host* must be a string giving a host for the network_instance.

	Parameter *attrs*:
	  The attributes of the network_instance can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes if given. Attributes can
	  later be changed using :py:func:`network_instance_modify`.

	Return value:
	  The return value of this method is the info dict of the new network_instance as
	  returned by :py:func:`resource_info`.
	"""
	getCurrentUserInfo().check_may_create_technical_resources()
	return NetworkInstanceInfo.create(network, host, attrs)


def network_instance_modify(id, attrs):
	"""
	Modifies a network_instance, configuring it with the given attributes.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying one of the supported
	  network_instance kinds.

	Parameter *host*:
	  The parameter *host* must be a string giving a host for the network_instance.

	Parameter *attrs*:
	  The attributes of the network_instance can be given as the parameter *attrs*.
	  This parameter must be a dict of attributes.

	Return value:
	  The return value of this method is the info dict of the resource as
	  returned by :py:func:`network_instance_info`. This info dict will reflect all
	  attribute changes.

	Exceptions:
	  If the given network_instance does not exist an exception *network_instance does not
	  exist* is raised.
	"""
	getCurrentUserInfo().check_may_modify_technical_resources()
	return get_network_instance_info(id).modify(attrs)


def network_instance_remove(id):
	"""
	Removes a network_instance.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying one of the supported
	  network_instance kinds.

	Parameter *host*:
	  The parameter *host* must be a string giving a host for the network_instance.

	Return value:
	  The return value of this method is ``None``.

	Exceptions:
	  If the given network_instance does not exist an exception *network_instance does not
	  exist* is raised.
	"""
	getCurrentUserInfo().check_may_remove_technical_resources()
	return get_network_instance_info(id).remove()


@checkauth
def network_instance_info(id):
	"""
	Retrieves information about a network_instance.

	Parameter *kind*:
	  The parameter *kind* must be a string identifying one of the supported
	  network_instance kinds.

	Parameter *host*:
	  The parameter *host* must be a string giving a host for the network_instance.

	Return value:
	  The return value of this method is a dict containing information
	  about this network_instance.

	Exceptions:
	  If the given network_instance does not exist an exception *network_instance does not
	  exist* is raised.
	"""
	return get_network_instance_info(id).info(update=True)
