from django.db import models
from . import attributes, db  # @UnresolvedImport
from django.template.defaultfilters import default

class KeyValuePair(attributes.Mixin, models.Model):
    key = models.CharField(max_length=255, primary_key=True)
    attrs = db.JSONField(default={})
    value = attributes.attribute("data", unicode, default="")
    
    def set(self, value):
        self.value = value
        self.save()
        
    def remove(self):
        self.delete()
    
def get(key, alt=None):
    res = KeyValuePair.objects.get(key=key)
    if res:
        return res
    return alt

def set(key, value):
    res = get(key)
    if res:
        res.set(value)
    else:
        KeyValuePair.create(key=key, value=value).save()

def delete(key):
    res = get(key)
    if res:
        res.remove()