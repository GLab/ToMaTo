import datetime, time

from django.template.defaultfilters import timesince
from django import template

register = template.Library()

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
def percentage(value, maxval):
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