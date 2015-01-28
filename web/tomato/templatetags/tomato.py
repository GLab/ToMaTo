import datetime, time

from django.template.defaultfilters import timesince
from django import template
from ..lib import getVersion, serverInfo, security_token
from django.utils.safestring import mark_safe
from ..lib import anyjson as json



register = template.Library()

@register.filter
def jsonify(o, pretty=False):
	if pretty:
		return mark_safe(json.orig.dumps(o, indent=True))
	else:
		return mark_safe(json.dumps(o))

@register.simple_tag
@register.filter
def externalurl(name):
	return serverInfo()['external_urls'].get(name, "")
	
@register.simple_tag
def backend_version():
	return serverInfo()['version']

@register.simple_tag
def frontend_version():
	return getVersion()

@register.simple_tag
def button(style='default', icon=None, title=""):
	glyphicon = '<span class="glyphicon glyphicon-%s"></span> ' % icon if icon else ""
	return '<a href="#" class="btn btn-%(style)s">%(glyphicon)s%(title)s</a>' % {'style': style, 'title': title, 'glyphicon': glyphicon}

@register.filter
def absolute(value):
	if value<0:
		return -value
	return value
	
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
	return datetime.datetime.fromtimestamp(float(value or "0.0"))
	
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

@register.filter
def newsitem_bettertime(value):
	v = value.split(" ")
	return v[0]+" "+v[1]+" "+v[2]+" "+v[3]

register.filter(security_token)
