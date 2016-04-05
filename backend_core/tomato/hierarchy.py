from .lib import hierarchy
from .lib.error import UserError
import elements
import host.element as hostelement
import connections
import host.connection as hostconnection
import topology



# HostElement

def hostelement_get(id_):
	hostelement.HostElement.objects.get(id=id_)

def hostelement_exists(id_):
	try:
		hostelement.HostElement.objects.get(id=id_)
		return True
	except:
		return None

def hostelement_parents(id_):
	hel = hostelement.HostElement.objects.get(id=id_)
	UserError.check(hel is not None, UserError.ENTITY_DOES_NOT_EXIST, message="entity doesn't exist.",
	                data={"class_name": hierarchy.ClassName.TOPOLOGY, "id_": id_})
	return [(hierarchy.ClassName.ELEMENT, hel.hostElement.id)]


# Element

def element_exists(id_):
	return (elements.Element.get(id_) is not None)

def element_parents(id_):
	el = elements.Element.get(id_)
	UserError.check(el is not None, UserError.ENTITY_DOES_NOT_EXIST, message="entity doesn't exist.",
	                data={"class_name": hierarchy.ClassName.TOPOLOGY, "id_": id_})
	return [(hierarchy.ClassName.TOPOLOGY, el.topology.id)]




# HostConnection

def hostconnection_get(id_):
	hostconnection.HostConnection.objects.get(id=id_)

def hostconnection_exists(id_):
	try:
		hostconnection.HostConnection.objects.get(id=id_)
		return True
	except:
		return None

def hostconnection_parents(id_):
	hconn = hostconnection.HostConnection.objects.get(id=id_)
	UserError.check(hconn is not None, UserError.ENTITY_DOES_NOT_EXIST, message="entity doesn't exist.",
	                data={"class_name": hierarchy.ClassName.TOPOLOGY, "id_": id_})
	return [(hierarchy.ClassName.ELEMENT, hconn.hostConnection.id)]




# Connection

def connection_exists(id_):
	return (connections.Connection.get(id_) is not None)

def connection_parents(id_):
	conn = connections.Connection.get(id_)
	UserError.check(conn is not None, UserError.ENTITY_DOES_NOT_EXIST, message="entity doesn't exist.",
	                data={"class_name": hierarchy.ClassName.TOPOLOGY, "id_": id_})
	return [(hierarchy.ClassName.TOPOLOGY, conn.topology.id)]


# topology

def topology_exists(id_):
	try:
		return (topology.get(id_) is not None)
	except:
		return False


def topology_parents(id_):
	topl = topology.get(id_)
	UserError.check(topl is not None, UserError.ENTITY_DOES_NOT_EXIST, message="entity doesn't exist.",
	                data={"class_name": hierarchy.ClassName.TOPOLOGY, "id_": id_})
	return [(hierarchy.ClassName.USER, perm.user) for perm in topl.permissions]


def init():
	hierarchy.register_class(hierarchy.ClassName.ELEMENT, elements.Element, elements.Element.get, element_exists, element_parents)
	hierarchy.register_class(hierarchy.ClassName.HOST_ELEMENT, hostelement.HostElement, hostelement_get, hostelement_exists, hostelement_parents)
	hierarchy.register_class(hierarchy.ClassName.CONNECTION, connections.Connection, connections.Connection.get, connection_exists, connection_parents)
	hierarchy.register_class(hierarchy.ClassName.HOST_CONNECTION, hostconnection.HostConnection, hostconnection_get, hostconnection_exists, hostconnection_parents)
	hierarchy.register_class(hierarchy.ClassName.TOPOLOGY, topology.Topology, topology.get, topology_exists, topology_parents)
