import types, re
from .error import UserError as Error

class Common:
	def __init__(self, options=None, optionsDesc=None, minValue=None, maxValue=None, null=False):
		self.options = options
		self.optionsDesc = optionsDesc
		self.minValue = minValue
		self.maxValue = maxValue
		self.null = null
	def _error(self, reason, value):
		raise Error(code=Error.INVALID_VALUE, message=reason, data={"value": value, "schema": self.describe()})
	def check(self, value):
		if not self.null and value is None:
			self._error("Value must not be null", value)
		if value is None:
			return
		if not self.options is None and not value in self.options:
			self._error("Value must be one of the given options", value)
		if not self.minValue is None and value < self.minValue:
			self._error("Value must not be below minimum", value)
		if not self.maxValue is None and value > self.maxValue:
			self._error("Value must not be above maximum", value)
	def describe(self):
		desc = {"null": self.null}
		if not self.options is None:
			desc['options'] = self.options
		if not self.optionsDesc is None:
			desc['options_desc'] = self.optionsDesc
		if not self.minValue is None:
			desc['min_value'] = self.minValue
		if not self.maxValue is None:
			desc['max_value'] = self.maxValue
		return desc
	def matches(self, value):
		try:
			self.check(value)
			return True
		except Error:
			return False

class Any(Common):
	pass

class Constant(Common):
	def __init__(self, value):
		Common.__init__(self, options=[value])

class Type(Common):
	TYPES = ()
	TYPE_NAMES = []
	def check(self, value):
		if not value is None and not isinstance(value, self.TYPES):
			self._error("Type must match allowed types", value)
		Common.check(self, value)
	def describe(self):
		desc = Common.describe(self)
		desc.update(types=self.TYPE_NAMES)
		return desc

class Number(Type):
	TYPES = (types.IntType, types.LongType, types.FloatType)
	TYPE_NAMES = ["int", "float"]

	def __init__(self, unit=None, **kwargs):
		Type.__init__(self, **kwargs)
		self.unit = unit
	def describe(self):
		desc = Type.describe(self)
		desc['unit'] = self.unit
		return desc

class Int(Number):
	TYPES = (types.IntType, types.LongType)
	TYPE_NAMES = ["int"]

class Bool(Type):
	TYPES = (types.BooleanType,)
	TYPE_NAMES = ["bool"]

class Sequence(Type):
	TYPES = types.StringTypes + (types.ListType, types.TupleType, types.BufferType)
	TYPE_NAMES = ["string", "list", "tuple"]
	def __init__(self, minLength=None, maxLength=None, **kwargs):
		Type.__init__(self, **kwargs)
		self.minLength = minLength
		self.maxLength = maxLength
	def check(self, value):
		Type.check(self, value)
		if value is None:
			return
		length = len(value)
		if not self.minLength is None and length < self.minLength:
			self._error("Sequence must not be shorter than minimum length", value)
		if not self.maxLength is None and length > self.maxLength:
			self._error("Sequence must not be longer than maximum length", value)
	def describe(self):
		desc = Type.describe(self)
		if not self.minLength is None:
			desc["min_length"] = self.minLength
		if not self.maxLength is None:
			desc["max_length"] = self.maxLength
		return desc

class String(Sequence):
	TYPES = types.StringTypes
	TYPE_NAMES = ["string"]
	def __init__(self, regex=None, **kwargs):
		Sequence.__init__(self, **kwargs)
		self.regex = regex
	def check(self, value):
		Sequence.check(self, value)
		if value is None or self.regex is None:
			return
		if not re.match("^%s$" % self.regex, value):
			self._error("String must match regular expression", value)
	def describe(self):
		desc = Sequence.describe(self)
		if not self.regex is None:
			desc['regex'] = self.regex
		return desc

class Identifier(String):
	def __init__(self, strict=False, **kwargs):
		minLength = kwargs.pop('minLength', 3)
		maxLength = kwargs.pop('maxLength', 100)
		if strict:
			regex = kwargs.pop('regex', "[a-zA-Z_][a-zA-Z0-9_]*")
		else:
			regex = kwargs.pop('regex', "[a-zA-Z0-9_\./\-]+")
		String.__init__(self, regex=regex, minLength=minLength, maxLength=maxLength, **kwargs)

class URL(String):
	def __init__(self, **kwargs):
		String.__init__(self, regex="[a-z]+:[A-Za-z0-9_:/.$\-?]+", **kwargs)

class List(Sequence):
	TYPES = (types.ListType, types.TupleType)
	TYPE_NAMES = ["list", "tuple"]
	def __init__(self, items=None, **kwargs):
		Sequence.__init__(self, **kwargs)
		self.items = items
	def check(self, value):
		Sequence.check(self, value)
		if value is None or self.items is None:
			return
		for item in value:
			self.items.check(item)
	def describe(self):
		desc = Sequence.describe(self)
		if not self.items is None:
			desc["items"] = self.items.describe()
		return desc

class StringMap(Sequence):
	TYPES = (types.DictType,)
	TYPE_NAMES = ["map"]
	KEYS = String()
	def __init__(self, items=None, required=None, additional=False, **kwargs):
		Sequence.__init__(self, **kwargs)
		self.items = items or {}
		self.required = required or []
		self.additional = additional
	def check(self, value):
		Sequence.check(self, value)
		if value is None:
			return
		for key, val in value.items():
			self.KEYS.check(key)
			schema = self.items.get(key)
			if schema is None and not self.additional:
				self._error("Map must not include additional fields", value)
			if schema:
				schema.check(val)
		for req in self.required:
			if not req in value:
				self._error("Map must contain required fields", value)
	def describe(self):
		desc = Sequence.describe(self)
		desc.update(items={key: val.describe() for key, val in self.items.items()}, required=self.required,
			additional=self.additional)
		return desc
