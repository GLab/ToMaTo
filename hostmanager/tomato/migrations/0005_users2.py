# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

	def forwards(self, orm):
		Users = orm["tomato.user"].objects
		for obj in orm["tomato.element"].objects.all():
			obj.owner = Users.get_or_create(name=obj.owner_str)
		for obj in orm["tomato.connection"].objects.all():
			obj.owner = Users.get_or_create(name=obj.owner_str)
		try:
			default_user = Users.all()[0]
		except:
			default_user = Users.create(name="default")
		for obj in orm["tomato.network"].objects.all():
			obj.owner = default_user
		for obj in orm["tomato.template"].objects.all():
			obj.owner = default_user

	def backwards(self, orm):
		pass

	models = {
		'tomato.bridge': {
			'Meta': {'object_name': 'Bridge', '_ormbases': ['tomato.Connection']},
			'connection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connection']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.connection': {
			'Meta': {'object_name': 'Connection'},
			'attrs': ('tomato.lib.db.JSONField', [], {}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'owner_str': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'connections'", 'null': 'False', 'to': "orm['tomato.User']"}),
			'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'usageStatistics': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'connection'", 'unique': 'True', 'null': 'True', 'to': "orm['tomato.UsageStatistics']"})
		},
		'tomato.element': {
			'Meta': {'object_name': 'Element'},
			'attrs': ('tomato.lib.db.JSONField', [], {}),
			'connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'null': 'True', 'to': "orm['tomato.Connection']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'owner_str': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'elements'", 'null': 'False', 'to': "orm['tomato.User']"}),
			'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['tomato.Element']"}),
			'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'timeout': ('django.db.models.fields.FloatField', [], {}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'usageStatistics': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'element'", 'unique': 'True', 'null': 'True', 'to': "orm['tomato.UsageStatistics']"})
		},
		'tomato.external_network': {
			'Meta': {'object_name': 'External_Network', '_ormbases': ['tomato.Element']},
			'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
			'network': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'instances'", 'null': 'True', 'to': "orm['tomato.Network']"})
		},
		'tomato.fixed_bridge': {
			'Meta': {'object_name': 'Fixed_Bridge', '_ormbases': ['tomato.Connection']},
			'connection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connection']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.kvmqm': {
			'Meta': {'object_name': 'KVMQM', '_ormbases': ['tomato.Element']},
			'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
			'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Template']", 'null': 'True'})
		},
		'tomato.kvmqm_interface': {
			'Meta': {'object_name': 'KVMQM_Interface', 'db_table': "'tomato_kvm_interface'", '_ormbases': ['tomato.Element']},
			'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.network': {
			'Meta': {'object_name': 'Network', '_ormbases': ['tomato.Resource']},
			'bridge': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
			'kind': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
			'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
			'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'networks'", 'null': 'False', 'to': "orm['tomato.User']"}),
			'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.openvz': {
			'Meta': {'object_name': 'OpenVZ', '_ormbases': ['tomato.Element']},
			'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
			'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Template']", 'null': 'True'})
		},
		'tomato.openvz_interface': {
			'Meta': {'object_name': 'OpenVZ_Interface', '_ormbases': ['tomato.Element']},
			'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.repy': {
			'Meta': {'object_name': 'Repy', '_ormbases': ['tomato.Element']},
			'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'}),
			'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Template']", 'null': 'True'})
		},
		'tomato.repy_interface': {
			'Meta': {'object_name': 'Repy_Interface', '_ormbases': ['tomato.Element']},
			'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
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
		'tomato.template': {
			'Meta': {'object_name': 'Template', '_ormbases': ['tomato.Resource']},
			'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
			'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
			'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Resource']", 'unique': 'True', 'primary_key': 'True'}),
			'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'templates'", 'null': 'False', 'to': "orm['tomato.User']"}),
			'tech': ('django.db.models.fields.CharField', [], {'max_length': '20'})
		},
		'tomato.tinc': {
			'Meta': {'object_name': 'Tinc', '_ormbases': ['tomato.Element']},
			'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.udp_tunnel': {
			'Meta': {'object_name': 'UDP_Tunnel', '_ormbases': ['tomato.Element']},
			'element_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Element']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.usagerecord': {
			'Meta': {'object_name': 'UsageRecord'},
			'begin': ('django.db.models.fields.FloatField', [], {}),
			'cputime': ('django.db.models.fields.FloatField', [], {}),
			'diskspace': ('django.db.models.fields.FloatField', [], {}),
			'end': ('django.db.models.fields.FloatField', [], {}),
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
			'begin': ('django.db.models.fields.FloatField', [], {}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
		},
		'tomato.user': {
			'Meta': {'object_name': 'User'},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '20', 'unique': 'True'})
		}
	}

	complete_apps = ['tomato']
	symmetrical = True
