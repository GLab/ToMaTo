import datetime, time

from django.template.defaultfilters import timesince
from django import template
from ..lib import getapi, getVersion
from django.utils.safestring import mark_safe
from django.utils import simplejson



register = template.Library()

@register.filter
def jsonify(o):
	return mark_safe(simplejson.dumps(o))

@register.simple_tag
def aupurl():
    api = getapi()
    return api.server_info()['external_urls']['aup']
    
@register.simple_tag
def impressumurl():
    api = getapi()
    return api.server_info()['external_urls']['impressum']
    
@register.simple_tag
def projecturl():
    api = getapi()
    return api.server_info()['external_urls']['project']

@register.simple_tag
def backend_version():
	api = getapi()
	return api.server_info()['version']

@register.simple_tag
def frontend_version():
	return getVersion()

@register.simple_tag
def helpurl():
	api = getapi()
	return api.server_info()['external_urls']['help']

@register.filter
def mult(value, arg):
	return float(value or "0.0") * arg
	
@register.filter
def div(value, arg):
	return float(value or "0.0") / arg

@register.filter
def minus(value, arg):
	return float(value or "0.0") - float(arg or "0.0")

@register.filter
def percentage(value, maxval=1.0):
	return "%.2f %%" % (float(value or "0.0") / float(maxval or "0.0") * 100.0)

@register.filter
def toduration(value):
	date = datetime.datetime.now() - datetime.timedelta(seconds=float(value or "0.0")) 
	return timesince(date)
	
@register.filter
def todate(value):
	return datetime.datetime.utcfromtimestamp(float(value or "0.0"))
	
@register.filter
def age(value):
	return time.time()-float(value or "0.0")
	
@register.filter
def get(h, key):
	return h[key]

@register.filter
def simpletags(value, tags="b a i ul ol li em strong"):
	import re
	tags = [re.escape(tag) for tag in tags.split()]
	pattern = re.compile(r'\[(\/?(%s)(\s+[^\]]*)?/?)\]' % '|'.join(tags))
	return pattern.sub('<\g<1>>', value)
	
@register.filter
def call(obj, methodName):
	method = getattr(obj, methodName)
	if obj.__dict__.has_key("__callArg"):
		ret = method(*obj.__callArg)
		del obj.__callArg
		return ret
	return method()

@register.filter
def args(obj, arg):
	if not obj.__dict__.has_key("__callArg"):
		obj.__callArg = []
	obj.__callArg += [arg]
	return obj