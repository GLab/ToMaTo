from django import template

register = template.Library()

@register.filter
def mult(value, arg):
  return value * arg
  
@register.filter
def percentage(value, max):
  return "%.2f %%" % (value / max * 100.0)