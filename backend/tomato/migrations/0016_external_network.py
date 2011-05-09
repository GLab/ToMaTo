# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
	
	def forwards(self, orm):
		db.rename_table('tomato_specialfeatureconnector', 'tomato_externalnetworkconnector')
		db.rename_column('tomato_externalnetworkconnector', 'used_feature_group_id', 'used_network_id')
		for con in orm["tomato.connector"].objects.filter(type="special"):
			con.type = "external"
			con.save()

		db.rename_table('tomato_specialfeature', 'tomato_externalnetworkbridge')
		db.rename_column('tomato_externalnetworkbridge', 'feature_group_id', 'network_id')

		db.rename_table('tomato_specialfeaturegroup', 'tomato_externalnetwork')
		db.rename_column('tomato_externalnetwork', 'group_name', 'group')
		db.rename_column('tomato_externalnetwork', 'feature_type', 'type')
	
	
	def backwards(self, orm):
		raise Exception("not implemented")
	
	
	models = {
		'tomato.attributeentry': {
			'Meta': {'object_name': 'AttributeEntry'},
			'attribute_set': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
			'value': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'})
		},
		'tomato.attributeset': {
			'Meta': {'object_name': 'AttributeSet'},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
		},
		'tomato.configuredinterface': {
			'Meta': {'object_name': 'ConfiguredInterface', '_ormbases': ['tomato.Interface']},
			'interface_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.connection': {
			'Meta': {'object_name': 'Connection'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
			'connector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Connector']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'interface': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True'})
		},
		'tomato.connector': {
			'Meta': {'object_name': 'Connector'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.device': {
			'Meta': {'object_name': 'Device'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
			'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']", 'null': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.emulatedconnection': {
			'Meta': {'object_name': 'EmulatedConnection', '_ormbases': ['tomato.Connection']},
			'connection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connection']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.error': {
			'Meta': {'object_name': 'Error'},
			'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
			'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
		},
		'tomato.externalnetwork': {
			'Meta': {'object_name': 'ExternalNetwork'},
			'avoid_duplicates': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
			'group': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'max_devices': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
		},
		'tomato.externalnetworkbridge': {
			'Meta': {'object_name': 'ExternalNetworkBridge'},
			'bridge': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'network': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.ExternalNetwork']"})
		},
		'tomato.externalnetworkconnector': {
			'Meta': {'object_name': 'ExternalNetworkConnector', '_ormbases': ['tomato.Connector']},
			'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'}),
			'used_network': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.ExternalNetwork']", 'null': 'True'})
		},
		'tomato.host': {
			'Meta': {'object_name': 'Host'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
			'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
			'group': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
		},
		'tomato.interface': {
			'Meta': {'object_name': 'Interface'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
			'device': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Device']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '5'})
		},
		'tomato.kvmdevice': {
			'Meta': {'object_name': 'KVMDevice', '_ormbases': ['tomato.Device']},
			'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.openvzdevice': {
			'Meta': {'object_name': 'OpenVZDevice', '_ormbases': ['tomato.Device']},
			'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.permission': {
			'Meta': {'object_name': 'Permission'},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'role': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'user': ('django.db.models.fields.CharField', [], {'max_length': '30'})
		},
		'tomato.physicallink': {
			'Meta': {'object_name': 'PhysicalLink'},
			'delay_avg': ('django.db.models.fields.FloatField', [], {}),
			'delay_stddev': ('django.db.models.fields.FloatField', [], {}),
			'dst_group': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'loss': ('django.db.models.fields.FloatField', [], {}),
			'src_group': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.template': {
			'Meta': {'object_name': 'Template'},
			'default': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
			'download_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '12'})
		},
		'tomato.tincconnection': {
			'Meta': {'object_name': 'TincConnection', '_ormbases': ['tomato.EmulatedConnection']},
			'emulatedconnection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.EmulatedConnection']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.tincconnector': {
			'Meta': {'object_name': 'TincConnector', '_ormbases': ['tomato.Connector']},
			'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.topology': {
			'Meta': {'object_name': 'Topology'},
			'attributes': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.AttributeSet']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
			'owner': ('django.db.models.fields.CharField', [], {'max_length': '30'})
		}
	}
	
	complete_apps = ['tomato']
