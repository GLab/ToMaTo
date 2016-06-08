from .. import Error
import re

class ParamError(Error):
	CODE_NOT_NULL="param.not_null"
	CODE_CONVERSION="param.conversion"
	CODE_CHECK="param.check"
	CODE_ONE_OF="param.one-of"
	CODE_LT="param.lower_than"
	CODE_LTE="param.lower_than_equal"
	CODE_GT="param.greater_than"
	CODE_GTE="param.greater_than_equal"
	CODE_REGEX="param.regex_mismatch"
	CODE_MISSING="param.missing"
	CODE_ADDITIONAL="param.additional"

def convert(value, null=False, convert=None, check=None, oneOf=None, regExp=None, gt=None, lt=None, gte=None, lte=None):
	if value is None:
		if not null:
			raise ParamError(ParamError.CODE_NOT_NULL, "Invalid value, must not be null", {"value": value})
		return None
	try:
		if convert:
			value = convert(value)
	except Exception, exc:
		raise ParamError(ParamError.CODE_CONVERSION, "Invalid value, failed to convert", {"value": value, "convert": convert, "error": exc})
	try:
		if check:
			if not check(value):
				raise ParamError(ParamError.CODE_CHECK, "Invalid value, failed check", {"value": value})
	except ParamError:
		raise
	except Exception, exc:
		raise ParamError(ParamError.CODE_CHECK, "Invalid value, failed check", {"value": value, "error": exc})
	if oneOf and not value in oneOf:
		raise ParamError(ParamError.CODE_ONE_OF, "Invalid value, must be one of a set", {"value": value, "oneOf": oneOf})
	if not lt is None and not value < lt:
		raise ParamError(ParamError.CODE_LT, "Invalid value, too big", {"value": value, "bound": lt})
	if not lte is None and not value <= lte:
		raise ParamError(ParamError.CODE_LTE, "Invalid value, too big", {"value": value, "bound": lte})
	if not gt is None and not value > gt:
		raise ParamError(ParamError.CODE_GT, "Invalid value, too small", {"value": value, "bound": gt})
	if not gte is None and not value >= gte:
		raise ParamError(ParamError.CODE_GTE, "Invalid value, too small", {"value": value, "bound": gte})
	if regExp and not re.match(regExp, value):
		raise ParamError(ParamError.CODE_REGEX, "Invalid value, must match pattern", {"value": value, "regex": regExp})
	return value

def convertMulti(valueMap, conventions=None, required=None, allowAdditional=False):
	if not required: required = []
	if not conventions: conventions = {}
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
			raise ParamError(ParamError.CODE_ADDITIONAL, "Additional parameters not allowed", {"key": key, "value": value, "allowed": conventions.keys()})
	missing = set(required) - set(res.keys())
	if missing:
		raise ParamError(ParamError.CODE_MISSING, "Missing parameters", {"missing": missing})
	return res