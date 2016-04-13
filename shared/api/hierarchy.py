from ..lib import hierarchy

def object_exists(class_name, id_):
	return hierarchy.exists(class_name, id_)

def object_parents(class_name, id_):
	return hierarchy.get_parents(class_name, id_)

def objects_available():
	return hierarchy.available_objects()
