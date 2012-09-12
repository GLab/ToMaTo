import datetime, time

from django.template.defaultfilters import timesince
from django import template

register = template.Library()

@register.filter
def mult(value, arg):
  return value * arg
  
@register.filter
def percentage(value, maxval):
  return "%.2f %%" % (float(value) / float(maxval) * 100.0)

@register.filter
def toduration(value):
  date = datetime.datetime.now() - datetime.timedelta(seconds=float(value)) 
  return timesince(date)
  
@register.filter
def todate(value):
  return datetime.datetime.utcfromtimestamp(float(value))
  
@register.filter
def age(value):
  return time.time()-float(value)