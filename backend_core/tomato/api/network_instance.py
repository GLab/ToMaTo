from ..resources.network import NetworkInstance
from .network import _getNetwork
from .host import _getHost
from ..lib.error import UserError

def _getNetworkInstance(id_):
	res = NetworkInstance.objects.get(id=id_)
	UserError.check(res, code=UserError.ENTITY_DOES_NOT_EXIST, message="Network instance does not exist", data={"id": id_})
	return res


def network_instance_list(network=None, host=None):
	"""
	Retrieves information about all resources.

	Parameter *kind*:
	  If *kind* is set, only resources with a matching kind will be returned.

	Return value:
	  A list with information entries of all matching network_instances. Each list
	  entry contains exactly the same information as returned by
	  :py:func:`network_instance_info`. If no resource matches, the list is empty.
	"""
	res = NetworkInstance.objects
	if network:
		res = res.filter(network=_getNetwork(network))
	if host:
		res = res.filter(hosT=_getHost(host))
	return [r.info() for r in res]


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
	if not attrs: attrs = {}
	attrs = dict(attrs)
	attrs.update(host=host, network=network)
	res = NetworkInstance.create(attrs)
	return res.info()


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
	res = _getNetworkInstance(id)
	res.modify(attrs)
	return res.info()


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
	res = _getNetworkInstance(id)
	res.remove()
	return {}


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
	res = _getNetworkInstance(id)
	return res.info()
