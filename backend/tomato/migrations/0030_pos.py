# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):
	
	def forwards(self, orm):
		for o in list(orm.Topology.objects.all()) + list(orm.Device.objects.all()) + \
		list(orm.Connector.objects.all()) + list(orm.Interface.objects.all()) + \
		list(orm.Connection.objects.all()):
			if "pos" in o.attrs:
				o.attrs["_pos"] = o.attrs["pos"]
				del o.attrs["pos"]
				o.save()
	
	def backwards(self, orm):
		for o in list(orm.Topology.objects.all()) + list(orm.Device.objects.all()) + \
		list(orm.Connector.objects.all()) + list(orm.Interface.objects.all()) + \
		list(orm.Connection.objects.all()):
			if "_pos" in o.attrs:
				o.attrs["pos"] = o.attrs["_pos"]
				del o.attrs["_pos"]
				o.save()
	
	models = {
		'tomato.configuredinterface': {
			'Meta': {'object_name': 'ConfiguredInterface', '_ormbases': ['tomato.Interface']},
			'interface_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.connection': {
			'Meta': {'unique_together': "(('connector', 'interface'),)", 'object_name': 'Connection'},
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'bridge_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
			'connector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Connector']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'interface': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True'})
		},
		'tomato.connector': {
			'Meta': {'unique_together': "(('topology', 'name'),)", 'object_name': 'Connector'},
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.device': {
			'Meta': {'unique_together': "(('topology', 'name'),)", 'object_name': 'Device'},
			'attrs': ('tomato.lib.db.JSONField', [], {}),
			'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']", 'null': 'True'}),
			'hostgroup': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
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
			'Meta': {'unique_together': "(('group', 'type'),)", 'object_name': 'ExternalNetwork'},
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
			'network_group': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
			'network_type': ('django.db.models.fields.CharField', [], {'default': "'internet'", 'max_length': '20'}),
			'used_network': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.ExternalNetwork']", 'null': 'True'})
		},
		'tomato.host': {
			'Meta': {'object_name': 'Host'},
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
			'group': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
		},
		'tomato.interface': {
			'Meta': {'unique_together': "(('device', 'name'),)", 'object_name': 'Interface'},
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'device': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Device']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '5'})
		},
		'tomato.kvmdevice': {
			'Meta': {'object_name': 'KVMDevice', '_ormbases': ['tomato.Device']},
			'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
			'template': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
			'vmid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
			'vnc_port': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
		},
		'tomato.openvzdevice': {
			'Meta': {'object_name': 'OpenVZDevice', '_ormbases': ['tomato.Device']},
			'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
			'template': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
			'vmid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
			'vnc_port': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
		},
		'tomato.permission': {
			'Meta': {'unique_together': "(('topology', 'user'),)", 'object_name': 'Permission'},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'role': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.User']"})
		},
		'tomato.physicallink': {
			'Meta': {'unique_together': "(('src_group', 'dst_group'),)", 'object_name': 'PhysicalLink'},
			'delay_avg': ('django.db.models.fields.FloatField', [], {}),
			'delay_stddev': ('django.db.models.fields.FloatField', [], {}),
			'dst_group': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'loss': ('django.db.models.fields.FloatField', [], {}),
			'src_group': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.progdevice': {
			'Meta': {'object_name': 'ProgDevice', '_ormbases': ['tomato.Device']},
			'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
			'template': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
			'vnc_port': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
		},
		'tomato.template': {
			'Meta': {'unique_together': "(('name', 'type'),)", 'object_name': 'Template'},
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'default': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '12'})
		},
		'tomato.tincconnection': {
			'Meta': {'object_name': 'TincConnection', '_ormbases': ['tomato.EmulatedConnection']},
			'emulatedconnection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.EmulatedConnection']", 'unique': 'True', 'primary_key': 'True'}),
			'tinc_port': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
		},
		'tomato.tincconnector': {
			'Meta': {'object_name': 'TincConnector', '_ormbases': ['tomato.Connector']},
			'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.topology': {
			'Meta': {'object_name': 'Topology'},
			'attrs': ('tomato.lib.db.JSONField', [], {'default': '{}'}),
			'date_usage': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
			'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.User']"}),
			'task': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'})
		},
		'tomato.user': {
			'Meta': {'unique_together': "(('name', 'origin'),)", 'object_name': 'User'},
			'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
			'is_user': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
			'origin': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
			'password': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
			'password_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
		}
	}
	
	complete_apps = ['tomato']
