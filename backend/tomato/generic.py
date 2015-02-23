import threading, types
from .lib.error import UserError as Error
from .lib import schema

class Action:
	def __init__(self, fn, description=None, check=None, paramSchema=None):
		self.fn = fn
		self.description = description or fn.__doc__
		self.checkFn = check
		self.paramSchema = paramSchema
	def check(self, obj, **params):
		if self.paramSchema:
			try:
				self.paramSchema.check(params)
			except Error as err:
				err.data.update(data=params, schema=self.paramSchema, data_failed=err.data.get('data'),
					schema_failed=err.data['schema'])
				raise
		if self.checkFn:
			Error.check(self.checkFn(obj, **params), code=Error.INVALID_STATE, message="Check for action failed")
	def __call__(self, obj, **kwargs):
		self.check(obj, **kwargs)
		return self.fn(obj, **kwargs)
	def info(self):
		return {
			"description": self.description,
			"param_schema": self.paramSchema.describe() if self.paramSchema else None
		}

class Attribute:
	def __init__(self, field=None, get=None, set=None, check=None, readOnly=False, schema=None):
		self.getFn = get
		self.setFn = set
		self.checkFn = check
		self.readOnly = readOnly
		self.schema = schema
		self.field = field
	def check(self, obj, value):
		Error.check(not self.readOnly, code=Error.INVALID_CONFIGURATION, message="Attribute is read-only")
		if self.schema:
			try:
				self.schema.check(value)
			except Error as err:
				err.data.update(data=value, schema=self.schema, data_failed=err.data.get('data'),
					schema_failed=err.data.get('schema'))
				raise
		if self.checkFn:
			Error.check(self.checkFn(obj, value), code=Error.INVALID_STATE, message="Check for attribute failed")
	def set(self, obj, value):
		self.check(obj, value)
		if self.setFn:
			self.setFn(obj, value)
		elif self.field:
			self.field.__set__(obj, value)
	def get(self, obj):
		if self.getFn:
			return self.getFn(obj)
		elif self.field:
			return self.field.__get__(obj, obj.__class__)
	def info(self):
		return {
			"read_only": self.readOnly,
			"value_schema": self.schema.describe() if self.schema else None
		}

class ConstantAttribute(Attribute):
	def __init__(self, value):
		Attribute.__init__(self, readOnly=True, get=lambda obj: value, schema=schema.Constant(value))
		self.value = value

class IdAttribute(Attribute):
	def __init__(self):
		Attribute.__init__(self, readOnly=True, get=lambda obj: str(obj.id), schema=schema.String())

class Entity(object):
	ACTIONS = {}
	ATTRIBUTES = {}
	DEFAULT_ATTRIBUTES = {}
	REMOVE_ACTION = "(remove)"

	save = id = delete = None
	del save, id, delete

	@property
	def type(self):
		return self.__class__.__name__.lower()

	def init(self, attrs):
		toSet = {}
		toSet.update(self.DEFAULT_ATTRIBUTES)
		if attrs:
			toSet.update(attrs)
		self.modify(toSet)

	def checkUnknownAttribute(self, key, value):
		raise Error(code=Error.UNSUPPORTED_ATTRIBUTE, message="Unsupported attribute")

	def setUnknownAttributes(self, attrs):
		raise NotImplemented()

	def modify(self, attrs):
		ATTRIBUTES = self.ATTRIBUTES
		for key, value in attrs.items():
			attr = ATTRIBUTES.get(key)
			try:
				if attr:
					attr.check(self, value)
				else:
					self.checkUnknownAttribute(key, value)
			except Error as err:
				err.data.update(type=self.type, attribute=key, value=value)
				raise
		unknownAttrs = {}
		for key, value in attrs.items():
			attr = ATTRIBUTES.get(key)
			try:
				if attr:
					attr.set(self, value)
				else:
					unknownAttrs[key] = value
			except Error as err:
				err.data.update(type=self.type, attribute=key, value=value)
				raise
		if unknownAttrs:
			self.setUnknownAttributes(unknownAttrs)
		self.save()

	def checkUnknownAction(self, action, params=None):
		raise Error(code=Error.UNSUPPORTED_ACTION, message="Unsupported action")

	def executeUnknownAction(self, action, params=None):
		raise NotImplemented()

	def action(self, action, params=None):
		if not params: params = {}
		try:
			actn = self.ACTIONS.get(action)
			if actn:
				actn.check(self, **params)
				return actn(self, **params)
			else:
				self.checkUnknownAction(action, params)
				return self.executeUnknownAction(action, params)
		except Error as err:
			err.data.update(type=self.type, action=action)
			raise
		finally:
			self.save()

	def remove(self, params=None):
		self.action(self.REMOVE_ACTION, params)

	def info(self):
		return {key: attr.get(self) for key, attr in self.ATTRIBUTES.items()}

	@classmethod
	def capabilities(cls):
		return {
			"actions": {key: action.info() for key, action in cls.ACTIONS.items()},
			"attributes": {key: attr.info() for key, attr in cls.ATTRIBUTES.items()},
		}

class StatefulAction(Action):
	def __init__(self, fn, allowedStates=None, stateChange=None, **kwargs):
		Action.__init__(self, fn , **kwargs)
		self.allowedStates = allowedStates
		self.stateChange = stateChange
	def check(self, obj, **kwargs):
		Action.check(self, obj, **kwargs)
		if not self.allowedStates is None:
			Error.check(obj.state in self.allowedStates, Error.INVALID_STATE, "Action is not available in this state")
	def info(self):
		info = Action.info(self)
		info.update(allowed_states=self.allowedStates, state_change=self.stateChange)
		return info

class StatefulAttribute(Attribute):
	def __init__(self, writableStates=None, readableStates=None, **kwargs):
		Attribute.__init__(self, **kwargs)
		self.writableStates = writableStates
		self.readableStates = readableStates
	def check(self, obj, value):
		if not self.writableStates is None:
			Error.check(obj.state in self.writableStates, code=Error.INVALID_STATE, message="Attribute is not writable in this state")
		Attribute.check(self, obj, value)
	def info(self):
		info = Attribute.info(self)
		info.update(states_readable=self.readableStates, states_writable=self.writableStates)
		return info

class LockedEntity(Entity):
	LOCKS = {}
	LOCKS_LOCK = threading.RLock()

	LOCKED_MODIFY = True
	LOCKED_ACTIONS = True
	LOCKED_REMOVE = True
	LOCKED_INFO = False

	@property
	def lock(self):
		key = (self.type, self.id)
		with self.LOCKS_LOCK:
			lock = self.LOCKS.get(key)
			if not lock:
				lock = threading.RLock()
				self.LOCKS[key] = lock
			return lock

	@property
	def busy(self):
		if self.lock.acquire(False):
			self.lock.release()
			return False
		return True

	def __enter__(self):
		self.lock.acquire()

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.lock.release()

	@classmethod
	def locked(cls, func):
		def call(self, *args, **kwargs):
			with self.lock:
				return func(self, *args, **kwargs)
		call.__name__ = func.__name__
		call.__doc__ = func.__doc__
		return call

	def action(self, action, params=None):
		if self.LOCKED_ACTIONS:
			with self.lock:
				return super(LockedEntity, self).action(action, params)
		else:
			return super(LockedEntity, self).action(action, params)

	def modify(self, attrs):
		if self.LOCKED_MODIFY:
			with self.lock:
				return super(LockedEntity, self).modify(attrs)
		else:
			return super(LockedEntity, self).modify(attrs)

	def info(self):
		if self.LOCKED_INFO:
			with self.lock:
				return super(LockedEntity, self).info()
		else:
			return super(LockedEntity, self).info()

	def remove(self, params=None):
		if self.LOCKED_REMOVE:
			with self.lock:
				return super(LockedEntity, self).remove(params)
		else:
			return super(LockedEntity, self).remove(params)


class StatefulEntity(Entity):
	STATES = []
	DEFAULT_STATE = None

	state = setState =None
	del state, setState

	def init(self, attrs):
		self.setState(self.DEFAULT_STATE)
		super(StatefulEntity, self).init(attrs)

	@classmethod
	def capabilities(cls):
		return {
			"actions": {key: action.info() for key, action in cls.ACTIONS.items()},
			"attributes": {key: attr.info() for key, attr in cls.ATTRIBUTES.items()},
			"states": cls.STATES,
			"default_state": cls.DEFAULT_STATE
		}

	def info(self):
		info = {}
		for key, attr in self.ATTRIBUTES.items():
			if isinstance(attr, StatefulAttribute) and not attr.readableStates is None and not self.state in attr.readableStates:
				continue
			info[key] = attr.get(self)
		return info


class LockedStatefulEntity(LockedEntity, StatefulEntity):
	pass