from .. import Error
import re

class ParamError(Error):
	CATEGORY="parameter"
	TYPE_NOT_NULL="not_null"
	TYPE_CONVERSION="conversion"
	TYPE_CHECK="check"
	TYPE_ONE_OF="one-of"
	TYPE_LT="lower_than"
	TYPE_LTE="lower_than_equal"
	TYPE_GT="greater_than"
	TYPE_GTE="greater_than_equal"
	TYPE_REGEX="regex_mismatch"
	TYPE_MISSING="missing"
	TYPE_ADDITIONAL="additional"
	def __init__(self, type, message, data=None):
		Error.__init__(self, category=ParamError.CATEGORY, type=type, message=message, data=data)

def convert(value, null=False, convert=None, check=None, oneOf=None, regExp=None, gt=None, lt=None, gte=None, lte=None):
	if value is None:
		if not null:
			raise ParamError(ParamError.TYPE_NOT_NULL, "Invalid value: %r, must not be null" % value, {"value": value})
		return None
	try:
		if convert:
			value = convert(value)
	except Exception, exc:
		raise ParamError(ParamError.TYPE_CONVERSION, "Invalid value: %r, failed to convert via %r: %s" % (value, convert, exc), {"value": value, "convert": convert, "error": exc})
	try:
		if check:
			if not check(value):
				raise ParamError(ParamError.TYPE_CHECK, "Invalid value: %r, failed check" % value, {"value": value})
	except ParamError:
		raise
	except Exception, exc:
		raise ParamError(ParamError.TYPE_CHECK, "Invalid value: %r, failed check: %s" % (value, exc), {"value": value, "error": exc})
	if oneOf and not value in oneOf:
		raise ParamError(ParamError.TYPE_ONE_OF, "Invalid value: %r, must be one of %r" % (value, options), {"value": value, "oneOf": oneOf})
	if not lt is None and not value < lt:
		raise ParamError(ParamError.TYPE_LT, "Invalid value: %r, must be < %r" % (value, lt), {"value": value, "bound": lt})
	if not lte is None and not value <= lte:
		raise ParamError(ParamError.TYPE_LTE, "Invalid value: %r, must be <= %r" % (value, lte), {"value": value, "bound": lte})
	if not gt is None and not value > gt:
		raise ParamError(ParamError.TYPE_GT, "Invalid value: %r, must be > %r" % (value, gt), {"value": value, "bound": gt})
	if not gte is None and not value >= gte:
		raise ParamError(ParamError.TYPE_GTE, "Invalid value: %r, must be >= %r" % (value, gte), {"value": value, "bound": gte})
	if regExp and not re.match(regExp, value):
		raise ParamError(ParamError.TYPE_REGEX, "Invalid value: %r, must match %r" % (value, regExp), {"value": value, "regex": regExp})
	return value

def convertMulti(valueMap, conventions={}, required=[], allowAdditions=False):
	res = {}
	for key, value in valueMap.iteritems():
		pkey = key
		if not pkey in conventions:
			for pat in conventions.keys():
				if re.match(pat, key):
					pkey = pat
		if pkey in conventions:
			res[key] = convert(value, **conventions[pkey])
		elif not allowAdditional:
			raise ParamError(ParamError.TYPE_ADDITIONAL, "Additional parameters not allowed: %r" % key, {"key": key, "value": value, "allowed": conventions.keys()})
	missing = set(required) - set(res.keys())
	if missing:
		raise ParamError(ParamError.TYPE_MISSING, "Missing parameters: %r" % missing, {"missing": missing})
	return res