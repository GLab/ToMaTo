from mongoengine import *
import string, random, crypt, time
from mongoengine.errors import NotUniqueError

class Host(Document):
        name = StringField(required=True, unique=True)
        address = StringField(required=True)
        rpcurl = StringField(required=True, unique=True)
        site = DynamicField()
        elementTypes = DictField(db_field='element_types')
        connectionTypes = DictField(db_field='connection_types')
        hostInfo = DictField(db_field='host_info')
        hostInfoTimestamp = FloatField(db_field='host_info_timestamp', required=True)
        accountingTimestamp = FloatField(db_field='accounting_timestamp', required=True)
        lastResourcesSync = FloatField(db_field='last_resource_sync', required=True)
        enabled = BooleanField()
        componentErrors = IntField(db_field='component_errors')
        problemAge = FloatField(db_field='problem_age')
        problemMailTime = FloatField(db_field='problem_mail_time')
        availability = FloatField()
        description = StringField()
        hostNetworks = ListField(db_field='host_networks')
        templates = DynamicField()


def migrate():
        for h in Host.objects():
                del h.templates
                h.save()