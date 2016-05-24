from ..resources.network import Network
from ..lib.error import UserError
from ..lib.exceptionhandling import wrap_errors


@wrap_errors(errorcls_func=lambda e: UserError, errorcode=UserError.ENTITY_DOES_NOT_EXIST)
def _getNetwork(id_):
	res = Network.objects.get(id=id_)
	UserError.check(res, code=UserError.ENTITY_DOES_NOT_EXIST, message="Network does not exist", data={"id": id_})
	return res


def network_list():
	"""
	Retrieves information about all resources.

	Return value:
	  A list with information entries of all matching networks. Each list
	  entry contains exactly the same information as returned by
	  :py:func:`network_info`. If no resource matches, the list is empty.
	"""
	res = Network.objects()
	return [r.info() for r in res]


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
	if not attrs: attrs = {}
	attrs = dict(attrs)
	attrs.update(kind=kind)
	res = Network.create(attrs)
	return res.info()


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
	res = _getNetwork(id)
	res.modify(attrs)
	return res.info()


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
	res = _getNetwork(id)
	res.remove()
	return {}


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
	res = _getNetwork(id)
	return res.info()