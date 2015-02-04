# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'User.name'
        db.alter_column(u'tomato_user', 'name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255))

    def backwards(self, orm):

        # Changing field 'User.name'
        db.alter_column(u'tomato_user', 'name', self.gf('django.db.models.fields.CharField')(max_length=20, unique=True))

    models = {
        'tomato.bridge': {
            'Meta': {'object_name': 'Bridge', '_ormbases': [u'tomato.Connection']},
            u'connection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Connection']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'tomato.connection': {
            'Meta': {'object_name': 'Connection'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'connections'", 'to': u"orm['tomato.User']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'usageStatistics': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'connection'", 'unique': 'True', 'null': 'True', 'to': u"orm['tomato.UsageStatistics']"})
        },
        u'tomato.element': {
            'Meta': {'object_name': 'Element'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'null': 'True', 'to': u"orm['tomato.Connection']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'to': u"orm['tomato.User']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': u"orm['tomato.Element']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'timeout': ('django.db.models.fields.FloatField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'usageStatistics': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'element'", 'unique': 'True', 'null': 'True', 'to': u"orm['tomato.UsageStatistics']"})
        },
        'tomato.external_network': {
            'Meta': {'object_name': 'External_Network', '_ormbases': [u'tomato.Element']},
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'network': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'instances'", 'null': 'True', 'to': "orm['tomato.Network']"})
        },
        'tomato.fixed_bridge': {
            'Meta': {'object_name': 'Fixed_Bridge', '_ormbases': [u'tomato.Connection']},
            u'connection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Connection']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.kvmqm': {
            'Meta': {'object_name': 'KVMQM', '_ormbases': [u'tomato.Element']},
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Template']", 'null': 'True'})
        },
        'tomato.kvmqm_interface': {
            'Meta': {'object_name': 'KVMQM_Interface', 'db_table': "'tomato_kvm_interface'", '_ormbases': [u'tomato.Element']},
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.network': {
            'Meta': {'unique_together': "(('bridge', 'owner'),)", 'object_name': 'Network', '_ormbases': [u'tomato.Resource']},
            'bridge': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'networks'", 'to': u"orm['tomato.User']"}),
            'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.openvz': {
            'Meta': {'object_name': 'OpenVZ', '_ormbases': [u'tomato.Element']},
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Template']", 'null': 'True'})
        },
        'tomato.openvz_interface': {
            'Meta': {'object_name': 'OpenVZ_Interface', '_ormbases': [u'tomato.Element']},
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.repy': {
            'Meta': {'object_name': 'Repy', '_ormbases': [u'tomato.Element']},
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Template']", 'null': 'True'})
        },
        'tomato.repy_interface': {
            'Meta': {'object_name': 'Repy_Interface', '_ormbases': [u'tomato.Element']},
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'tomato.resource': {
            'Meta': {'object_name': 'Resource'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'tomato.resourceinstance': {
            'Meta': {'unique_together': "(('num', 'type'),)", 'object_name': 'ResourceInstance'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num': ('django.db.models.fields.IntegerField', [], {}),
            'ownerConnection': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.Connection']", 'null': 'True'}),
            'ownerElement': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tomato.Element']", 'null': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.template': {
            'Meta': {'unique_together': "(('tech', 'name', 'owner'),)", 'object_name': 'Template', '_ormbases': [u'tomato.Resource']},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'templates'", 'to': u"orm['tomato.User']"}),
            'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'}),
            'tech': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'tomato.tinc': {
            'Meta': {'object_name': 'Tinc', '_ormbases': [u'tomato.Element']},
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        'tomato.udp_tunnel': {
            'Meta': {'object_name': 'UDP_Tunnel', '_ormbases': [u'tomato.Element']},
            u'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'tomato.usagerecord': {
            'Meta': {'object_name': 'UsageRecord'},
            'begin': ('django.db.models.fields.FloatField', [], {}),
            'cputime': ('django.db.models.fields.FloatField', [], {}),
            'diskspace': ('django.db.models.fields.FloatField', [], {}),
            'end': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'measurements': ('django.db.models.fields.IntegerField', [], {}),
            'memory': ('django.db.models.fields.FloatField', [], {}),
            'statistics': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'records'", 'to': u"orm['tomato.UsageStatistics']"}),
            'traffic': ('django.db.models.fields.FloatField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'tomato.usagestatistics': {
            'Meta': {'object_name': 'UsageStatistics'},
            'attrs': ('tomato.lib.db.JSONField', [], {}),
            'begin': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'tomato.user': {
            'Meta': {'object_name': 'User'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['tomato']