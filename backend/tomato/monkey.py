def patch_xmlrpc_mongoengine():
	from xmlrpclib import Marshaller
	from mongoengine.base.datastructures import BaseDict, BaseList
	Marshaller.dispatch[BaseDict] = Marshaller.dump_struct
	Marshaller.dispatch[BaseList] = Marshaller.dump_array

def patch_all():
	patch_xmlrpc_mongoengine()