from ..db import *
from ..lib import logging, error, util
from .. import scheduler

from . import HostObject
from .element import HostElement

class HostConnection(HostObject):
	elementFrom = ReferenceField(HostElement, db_field='element_from', required=True, reverse_delete_rule=NULLIFY)
	elementTo = ReferenceField(HostElement, db_field='element_to', required=True, reverse_delete_rule=NULLIFY)
	meta = {
		'collection': 'host_connection',
		'indexes': [
			('host', 'num')
		]
	}

	def modify(self, attrs):
		logging.logMessage("connection_modify", category="host", host=self.host.name, id=self.num, attrs=attrs)
		try:
			self.objectInfo = self.host.getProxy().connection_modify(self.num, attrs)
		except error.UserError, err:
			if err.code == error.UserError.ENTITY_DOES_NOT_EXIST:
				logging.logMessage("missing connection", category="host", host=self.host.name, id=self.num)
				self.remove()
			if err.code == error.UserError.INVALID_STATE:
				self.updateInfo()
			raise
		except:
			self.host.incrementErrors()
			raise
		logging.logMessage("connection_info", category="host", host=self.host.name, id=self.num, info=self.objectInfo)
		self.save()

	def action(self, action, params=None):
		if not params: params = {}
		logging.logMessage("connection_action begin", category="host", host=self.host.name, id=self.num, action=action,
						   params=params)
		try:
			res = self.host.getProxy().connection_action(self.num, action, params)
		except error.UserError, err:
			if err.code == error.UserError.ENTITY_DOES_NOT_EXIST:
				logging.logMessage("missing connection", category="host", host=self.host.name, id=self.num)
				self.remove()
			if err.code == error.UserError.INVALID_STATE:
				self.updateInfo()
			raise
		except:
			self.host.incrementErrors()
			raise
		logging.logMessage("connection_action begin", category="host", host=self.host.name, id=self.num, action=action,
						   params=params, result=res)
		self.updateInfo()
		return res

	def remove(self):
		try:
			logging.logMessage("connection_remove", category="host", host=self.host.name, id=self.num)
			self.host.getProxy().connection_remove(self.num)
		except error.UserError, err:
			if err.code != error.UserError.ENTITY_DOES_NOT_EXIST:
				self.host.incrementErrors()
		except:
			self.host.incrementErrors()
		if self.id:
			self.delete()

	def getElements(self):
		return [self.elementFrom, self.elementTo]

	def updateInfo(self):
		try:
			self.objectInfo = self.host.getProxy().connection_info(self.num)
			self.state = self.objectInfo["state"]
		except error.UserError, err:
			if err.code == error.UserError.ENTITY_DOES_NOT_EXIST:
				logging.logMessage("missing connection", category="host", host=self.host.name, id=self.num)
				self.remove()
			raise
		except:
			self.host.incrementErrors()
			raise
		logging.logMessage("connection_info", category="host", host=self.host.name, id=self.num, info=self.objectInfo)
		self.save()

	def info(self):
		return self.objectInfo

	def getAttrs(self):
		return self.objectInfo["attrs"]

	@property
	def capabilities(self):
		return self.host.getConnectionCapabilities(self.type)

	def synchronize(self):
		try:
			if not self.topologyElement and not self.topologyConnection:
				self.remove()
				return
			self.updateInfo()
		except error.UserError, err:
			if err.code == error.UserError.ENTITY_DOES_NOT_EXIST:
				logging.logMessage("missing connection", category="host", host=self.host.name, id=self.num)
				self.remove()
			if err.code != error.UserError.UNSUPPORTED_ATTRIBUTE:
				raise
		except:
			logging.logException(host=self.host.address)

HostConnection.register_delete_rule(HostElement, "connection", NULLIFY)

def list():
	return [e.id for e in HostConnection.objects.all()]
@util.wrap_task
def synchronize(id_):
	HostConnection.objects.get(id=id_).synchronize()
scheduler.scheduleMaintenance(3600, list, synchronize)
