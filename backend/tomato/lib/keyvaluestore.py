from django.db import models
from . import attributes, db  # @UnresolvedImport

class KeyValuePair(attributes.Mixin, models.Model):
    
    class Meta:
        db_table = "tomato_keyvaluepair"
        app_label = 'tomato'
        pass

    key = models.CharField(max_length=255, unique=True)
    attrs = db.JSONField(default={})
    value = attributes.attribute("data")
    
    def set(self, value):
        self.value = value
        self.save()
        
    def get(self):
        return self.value
        
    def remove(self):
        self.delete()
        
def getObj(key):
    try:
        return KeyValuePair.objects.get(key=key)
    except:
        return None
    
    
    
def get(key, alt=None):
    res = getObj(key)
    if res is not None:
        return res.get()
    return alt

def set(key, value):
    res = getObj(key)
    if res is not None:
        res.set(value)
    else:
        KeyValuePair.objects.create(key=key, value=value).save()

def delete(key):
    res = getObj(key)
    if res is not None:
        res.remove()
