def patch_xmlrpc_mongoengine():
	from xmlrpclib import Marshaller
	from mongoengine.base.datastructures import BaseDict, BaseList
	from bson.binary import Binary
	Marshaller.dispatch[BaseDict] = Marshaller.dump_struct
	Marshaller.dispatch[BaseList] = Marshaller.dump_array
	Marshaller.dispatch[Binary] = Marshaller.dump_string

def patch_all():
	patch_xmlrpc_mongoengine()