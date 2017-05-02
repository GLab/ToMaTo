def patch_xmlrpc_mongoengine():
	from xmlrpclib import Marshaller
	from mongoengine.base.datastructures import BaseDict, BaseList
	from bson.binary import Binary
	from bson.int64 import Int64
	Marshaller.dispatch[BaseDict] = Marshaller.dump_struct
	Marshaller.dispatch[BaseList] = Marshaller.dump_array
	Marshaller.dispatch[Binary] = Marshaller.dump_string
	Marshaller.dispatch[Int64] = lambda m, v, w: m.dump_string(str(v), w)

def patch_mongoengine_from_son():
	from mongoengine.base.document import BaseDocument
	orig = getattr(BaseDocument, '_from_son')
	def from_son(cls, *args, **kwargs):
		meth = orig.__func__.__get__(cls) # rebind original method to cls
		obj = meth(*args, **kwargs)
		try:
			if hasattr(obj, '_changed_fields'):
				changed = getattr(obj, '_changed_fields')
				for name in list(changed):
					if name in obj._db_field_map:
						db_field = obj._db_field_map[name]
						changed.remove(name)
						changed.append(db_field)
				setattr(obj, '_changed_fields', changed)
		except:
			import traceback
			traceback.print_exc()
		return obj

	# noinspection PyUnresolvedReferences
	BaseDocument._from_son = classmethod(from_son)

def patch_all():
	patch_xmlrpc_mongoengine()
	patch_mongoengine_from_son()