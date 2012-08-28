# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'OpenVZ_Interface.element'
        db.add_column('tomato_openvz_interface', 'element', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostElement'], null=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'OpenVZ_Interface.element'
        db.delete_column('tomato_openvz_interface', 'element_id')


    models = {
        'tomato.connection': {
            'Meta': {'object_name': 'Connection'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permissions': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Permissions']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'connections'", 'to': "orm['tomato.Topology']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'usageStatistics': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'connection'", 'unique': 'True', 'null': 'True', 'to': "orm['tomato.UsageStatistics']"})
        },
        'tomato.element': {
            'Meta': {'object_name': 'Element'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'null': 'True', 'to': "orm['tomato.Connection']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['tomato.Element']"}),
            'permissions': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Permissions']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'to': "orm['tomato.Topology']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'usageStatistics': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'element'", 'unique': 'True', 'null': 'True', 'to': "orm['tomato.UsageStatistics']"})
        },
        'tomato.host': {
            'Meta': {'object_name': 'Host'},
            'address': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': "orm['tomato.Site']"})
        },
        'tomato.hostconnection': {
            'Meta': {'unique_together': "(('host', 'num'),)", 'object_name': 'HostConnection'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'connections'", 'to': "orm['tomato.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num': ('django.db.models.fields.IntegerField', [], {})
        },
        'tomato.hostelement': {
            'Meta': {'unique_together': "(('host', 'num'),)", 'object_name': 'HostElement'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'to': "orm['tomato.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num': ('django.db.models.fields.IntegerField', [], {})
        },
        'tomato.network': {
            'Meta': {'object_name': 'Network', '_ormbases': ['tomato.Resource']},
            'bridge': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.openvz': {
            'Meta': {'object_name': 'OpenVZ', '_ormbases': ['tomato.Element']},
            'element': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.HostElement']", 'null': 'True'}),
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Site']", 'null': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Resource']", 'null': 'True'})
        },
        'tomato.openvz_interface': {
            'Meta': {'object_name': 'OpenVZ_Interface', '_ormbases': ['tomato.Element']},
            'element': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.HostElement']", 'null': 'True'}),
            'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.permissionentry': {
            'Meta': {'unique_together': "(('user', 'set'),)", 'object_name': 'PermissionEntry'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'set': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entries'", 'to': "orm['tomato.Permissions']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.User']"})
        },
        'tomato.permissions': {
            'Meta': {'object_name': 'Permissions'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'tomato.resource': {
            'Meta': {'object_name': 'Resource'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.resourceinstance': {
            'Meta': {'unique_together': "(('num', 'type'),)", 'object_name': 'ResourceInstance'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num': ('django.db.models.fields.IntegerField', [], {}),
            'ownerConnection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Connection']", 'null': 'True'}),
            'ownerElement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Element']", 'null': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.site': {
            'Meta': {'object_name': 'Site'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'})
        },
        'tomato.template': {
            'Meta': {'object_name': 'Template', '_ormbases': ['tomato.Resource']},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'}),
            'tech': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.topology': {
            'Meta': {'object_name': 'Topology'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permissions': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Permissions']"})
        },
        'tomato.usagerecord': {
            'Meta': {'object_name': 'UsageRecord'},
            'begin': ('django.db.models.fields.DateTimeField', [], {}),
            'cputime': ('django.db.models.fields.FloatField', [], {}),
            'diskspace': ('django.db.models.fields.FloatField', [], {}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'measurements': ('django.db.models.fields.IntegerField', [], {}),
            'memory': ('django.db.models.fields.FloatField', [], {}),
            'statistics': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'records'", 'to': "orm['tomato.UsageStatistics']"}),
            'traffic': ('django.db.models.fields.FloatField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'tomato.usagestatistics': {
            'Meta': {'object_name': 'UsageStatistics'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'tomato.user': {
            'Meta': {'ordering': "['name', 'origin']", 'unique_together': "(('name', 'origin'),)", 'object_name': 'User'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'origin': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'password_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        }
    }

    complete_apps = ['tomato']
